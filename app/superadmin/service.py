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


def delete_tenant_record(db: Session, tenant_id: int) -> bool:
    """
    Delete a tenant record from the super_admin_db.
    
    Note: This only deletes the tenant record from the super_admin_db.
    The actual PostgreSQL database for the tenant is NOT automatically deleted.
    Manual cleanup of tenant databases should be done separately for safety.
    
    Args:
        db: Database session
        tenant_id: ID of the tenant to delete
        
    Returns:
        True if deleted successfully, False if tenant not found
    """
    tenant = get_tenant_by_id(db, tenant_id)
    if not tenant:
        return False
    
    db.delete(tenant)
    db.commit()
    return True


def toggle_tenant_status(db: Session, tenant_id: int) -> Tenant:
    """
    Toggle tenant status between 'active' and 'inactive'.
    
    When a tenant is set to 'inactive', users should not be able to login
    to that tenant. The database and all data remain intact.
    
    Args:
        db: Database session
        tenant_id: ID of the tenant to toggle
        
    Returns:
        Updated Tenant instance
        
    Raises:
        ValueError: If tenant not found
    """
    tenant = get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise ValueError(f"Tenant with ID {tenant_id} not found")
    
    # Toggle status
    tenant.status = "inactive" if tenant.status == "active" else "active"
    
    db.commit()
    db.refresh(tenant)
    return tenant


def update_tenant_status(db: Session, tenant_id: int, status: str) -> Tenant:
    """
    Update tenant status to a specific value.
    
    Args:
        db: Database session
        tenant_id: ID of the tenant to update
        status: New status ('active' or 'inactive')
        
    Returns:
        Updated Tenant instance
        
    Raises:
        ValueError: If tenant not found or invalid status
    """
    if status not in ["active", "inactive"]:
        raise ValueError(f"Invalid status: {status}. Must be 'active' or 'inactive'")
    
    tenant = get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise ValueError(f"Tenant with ID {tenant_id} not found")
    
    tenant.status = status
    
    db.commit()
    db.refresh(tenant)
    return tenant

