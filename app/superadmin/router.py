"""API routes for Super Admin Service."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_super_admin_db
from app.superadmin.schemas import TenantCreate, TenantResponse
from app.superadmin.service import create_tenant_record
from app.hrms_provisioning.database_creator import create_database
from app.hrms_provisioning.run_migrations import run_hrms_migrations
from app.hrms_provisioning.seed_admin import seed_initial_admin
from app.security import hash_password
from app.utils import generate_secure_password
from app.config import settings
import time

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}"
        )

