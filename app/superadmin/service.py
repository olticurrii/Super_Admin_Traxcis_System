"""Service layer for Super Admin operations."""
from sqlalchemy.orm import Session
from app.superadmin.models import Tenant
from app.config import settings
import time


def create_tenant_record(
    db: Session,
    name: str,
    db_name: str,
    admin_email: str,
    db_host: str = None,
    db_port: str = None,
    db_user: str = None,
    db_password: str = None
) -> Tenant:
    """
    Create a tenant record in the super_admin_db.
    
    Args:
        db: Database session
        name: Tenant name
        db_name: Database name for the tenant
        admin_email: Admin email for the tenant
        db_host: Database host (defaults to config)
        db_port: Database port (defaults to config)
        db_user: Database user (defaults to config)
        db_password: Database password (defaults to config)
        
    Returns:
        Created Tenant instance
    """
    tenant = Tenant(
        name=name,
        db_name=db_name,
        db_host=db_host or settings.DB_HOST,
        db_port=db_port or settings.DB_PORT,
        db_user=db_user or settings.DB_USER,
        db_password=db_password or settings.DB_PASSWORD,
        admin_email=admin_email,
        status="active"
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def get_tenant_by_id(db: Session, tenant_id: int) -> Tenant:
    """Get a tenant by ID."""
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def get_tenant_by_db_name(db: Session, db_name: str) -> Tenant:
    """Get a tenant by database name."""
    return db.query(Tenant).filter(Tenant.db_name == db_name).first()


def list_tenants(db: Session, skip: int = 0, limit: int = 100):
    """List all tenants."""
    return db.query(Tenant).offset(skip).limit(limit).all()

