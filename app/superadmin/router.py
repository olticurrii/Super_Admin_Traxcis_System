"""API routes for Super Admin Service."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_super_admin_db
from app.superadmin.schemas import TenantCreate, TenantResponse, TenantInfo
from app.superadmin.service import create_tenant_record, list_tenants, delete_tenant_record, toggle_tenant_status, update_tenant_status
from app.hrms_provisioning.database_creator import create_database
from app.hrms_provisioning.run_migrations import run_tenant_migrations
from app.hrms_provisioning.seed_admin import seed_initial_admin
from app.security import hash_password
from app.utils import generate_secure_password
from app.config import settings
from app.superadmin.fix_schema import fix_tenant_schema
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
    2. Runs tenant schema migrations on the new database
    3. Seeds an initial admin user
    4. Stores tenant metadata in super_admin_db
    5. Returns the initial admin password (shown only once)
    """
    tenant = None
    try:
        # Generate unique database name
        db_name = f"tenant_{tenant_data.name.lower().replace(' ', '_')}_{int(time.time())}"
        
        # Build database URL for the tenant
        db_url = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{db_name}"
        
        # Step 1: Create tenant record in super_admin_db FIRST to get tenant_id
        logger.info(f"Creating tenant record for: {tenant_data.name}")
        tenant = create_tenant_record(
            db=db,
            name=tenant_data.name,
            db_name=db_name,
            admin_email=tenant_data.admin_email
        )
        tenant_id = tenant.id
        logger.info(f"Tenant record created with ID: {tenant_id}")
        
        # Step 2: Create the database
        logger.info(f"Creating database: {db_name}")
        create_database(db_name)
        
        # Step 3: Run tenant migrations (uses subprocess, no HRMS imports)
        logger.info(f"Running tenant migrations on: {db_name}")
        try:
            run_tenant_migrations(db_url)
        except Exception as migration_error:
            logger.error(f"Migration failed: {str(migration_error)}")
            # Mark tenant as failed
            tenant.status = "migration_failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to run migrations: {str(migration_error)}"
            )
        
        # Step 4: Generate secure random password for admin
        initial_password = generate_secure_password(12)
        hashed_password = hash_password(initial_password)
        
        # Step 5: Seed initial admin user WITH the correct tenant_id
        logger.info(f"Seeding admin user in: {db_name} with tenant_id={tenant_id}")
        try:
            seed_initial_admin(db_url, tenant_data.admin_email, hashed_password, tenant_id)
        except Exception as seed_error:
            logger.error(f"Failed to seed admin user: {str(seed_error)}")
            # Mark tenant as failed
            tenant.status = "seed_failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to seed admin user: {str(seed_error)}"
            )
        
        # Step 6: Return response with initial password (never stored in plaintext)
        logger.info(f"Successfully created tenant: {tenant_data.name} (ID: {tenant.id})")
        return TenantResponse(
            tenant_id=tenant.id,
            tenant_db=db_name,
            admin_email=tenant_data.admin_email,
            initial_password=initial_password
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Failed to create tenant: {str(e)}\n{error_trace}")
        
        # Mark tenant as failed if record exists
        if tenant:
            try:
                tenant.status = "failed"
                db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update tenant status: {str(update_error)}")
        
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


@router.post("/fix-all-tenant-schemas", status_code=status.HTTP_200_OK)
async def fix_all_tenant_schemas(db: Session = Depends(get_super_admin_db)):
    """
    Fix schema for all existing tenant databases by adding missing is_admin column.
    
    This endpoint iterates through all active tenants and adds the is_admin column
    if it's missing from the users table.
    
    Returns:
        Summary of the fix operation for each tenant
    """
    try:
        # Get all active tenants
        tenants = list_tenants(db, skip=0, limit=1000)
        
        results = []
        fixed_count = 0
        error_count = 0
        
        for tenant in tenants:
            logger.info(f"Fixing schema for tenant: {tenant.name} (DB: {tenant.db_name}, ID: {tenant.id})")
            result = fix_tenant_schema(tenant.db_name, tenant.id)
            
            results.append({
                "tenant_id": tenant.id,
                "tenant_name": tenant.name,
                "db_name": tenant.db_name,
                "result": result
            })
            
            if result["status"] == "success":
                fixed_count += 1
            else:
                error_count += 1
        
        logger.info(f"Schema fix complete. Fixed: {fixed_count}, Errors: {error_count}")
        
        return {
            "message": f"Schema fix complete. Fixed: {fixed_count}, Errors: {error_count}",
            "fixed_count": fixed_count,
            "error_count": error_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to fix tenant schemas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fix tenant schemas: {str(e)}"
        )

