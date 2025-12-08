"""API routes for Super Admin Service."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_super_admin_db
from app.superadmin.schemas import TenantCreate, TenantResponse, TenantInfo
from app.superadmin.service import (
    create_tenant_record, 
    list_tenants, 
    delete_tenant_record,
    toggle_tenant_status,
    update_tenant_status
)
from app.hrms_provisioning.database_creator import create_database
from app.hrms_provisioning.run_migrations import run_hrms_migrations
from app.hrms_provisioning.seed_admin import seed_initial_admin
from app.security import hash_password
from app.utils import generate_secure_password
from app.config import settings
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/super-admin", tags=["super-admin"])


@router.post("/create-tenant", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_super_admin_db)
):
    """
    Create a new tenant database and provision it with HRMS migrations and admin user.
    
    This endpoint:
    1. Creates a new PostgreSQL database for the tenant
    2. Runs HRMS Alembic migrations on the new database
    3. Seeds an initial admin user
    4. Stores tenant metadata in super_admin_db
    5. Returns the initial admin password (shown only once)
    """
    try:
        # Generate unique database name
        db_name = f"tenant_{tenant_data.name.lower().replace(' ', '_')}_{int(time.time())}"
        
        # Build database URL for the tenant
        db_url = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{db_name}"
        
        # Step 1: Create the database
        create_database(db_name)
        
        # Step 2: Run HRMS migrations
        run_hrms_migrations(db_url)
        
        # Step 3: Generate secure random password for admin
        initial_password = generate_secure_password(12)
        hashed_password = hash_password(initial_password)
        
        # Step 4: Seed initial admin user
        seed_initial_admin(db_url, tenant_data.admin_email, hashed_password)
        
        # Step 5: Save tenant record in super_admin_db
        tenant = create_tenant_record(
            db=db,
            name=tenant_data.name,
            db_name=db_name,
            admin_email=tenant_data.admin_email
        )
        
        # Step 6: Return response with initial password (never stored in plaintext)
        return TenantResponse(
            tenant_id=tenant.id,
            tenant_db=db_name,
            admin_email=tenant_data.admin_email,
            initial_password=initial_password
        )
        
    except Exception as e:
        # If any step fails, we should ideally rollback, but database creation
        # and migrations are harder to rollback. Log the error for manual cleanup.
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Failed to create tenant: {str(e)}\n{error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}"
        )


@router.get("/tenants", response_model=List[TenantInfo])
async def get_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_super_admin_db)
):
    """
    Get a list of all tenants.
    
    Returns tenant information including database details and status.
    Does not include sensitive credentials.
    """
    try:
        tenants = list_tenants(db, skip=skip, limit=limit)
        return tenants
    except Exception as e:
        logger.error(f"Failed to list tenants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tenants: {str(e)}"
        )


@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_200_OK)
async def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_super_admin_db)
):
    """
    Delete a tenant record from the super_admin_db.
    
    IMPORTANT: This only removes the tenant record from the super_admin database.
    The actual PostgreSQL database for the tenant is NOT automatically deleted
    for safety reasons. Manual cleanup should be performed if needed.
    
    Args:
        tenant_id: The ID of the tenant to delete
        
    Returns:
        Success message with tenant database name for manual cleanup reference
    """
    try:
        # First get the tenant to retrieve the db_name
        from app.superadmin.service import get_tenant_by_id
        tenant = get_tenant_by_id(db, tenant_id)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with ID {tenant_id} not found"
            )
        
        db_name = tenant.db_name
        
        # Delete the tenant record
        success = delete_tenant_record(db, tenant_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to delete tenant with ID {tenant_id}"
            )
        
        logger.info(f"Deleted tenant record {tenant_id} (database: {db_name})")
        
        return {
            "message": "Tenant record deleted successfully",
            "tenant_id": tenant_id,
            "db_name": db_name,
            "note": "The PostgreSQL database was not automatically deleted. Manual cleanup may be required."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tenant: {str(e)}"
        )


@router.patch("/tenants/{tenant_id}/toggle-status", response_model=TenantInfo)
async def toggle_tenant_status_endpoint(
    tenant_id: int,
    db: Session = Depends(get_super_admin_db)
):
    """
    Toggle tenant status between 'active' and 'inactive'.
    
    When a tenant is inactive, users should not be able to login to that tenant.
    All data and the database remain intact - this is a soft disable.
    
    This is safer than deletion as it can be easily reversed.
    
    Args:
        tenant_id: The ID of the tenant to toggle
        
    Returns:
        Updated tenant information with new status
    """
    try:
        tenant = toggle_tenant_status(db, tenant_id)
        
        logger.info(f"Toggled tenant {tenant_id} status to: {tenant.status}")
        
        return tenant
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to toggle tenant {tenant_id} status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle tenant status: {str(e)}"
        )


@router.patch("/tenants/{tenant_id}/status", response_model=TenantInfo)
async def update_tenant_status_endpoint(
    tenant_id: int,
    status_value: str,
    db: Session = Depends(get_super_admin_db)
):
    """
    Update tenant status to a specific value.
    
    Args:
        tenant_id: The ID of the tenant to update
        status_value: New status ('active' or 'inactive')
        
    Returns:
        Updated tenant information with new status
    """
    try:
        tenant = update_tenant_status(db, tenant_id, status_value)
        
        logger.info(f"Updated tenant {tenant_id} status to: {status_value}")
        
        return tenant
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update tenant {tenant_id} status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tenant status: {str(e)}"
        )

