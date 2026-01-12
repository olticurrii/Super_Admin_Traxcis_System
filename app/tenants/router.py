"""API routes for tenant lookup operations."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_super_admin_db
from app.superadmin.models import Tenant
from app.superadmin.schemas import TenantByEmailResponse, TenantByIdResponse
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"]
)


@router.get("/find-by-company/{company_name}", response_model=TenantByEmailResponse)
def find_tenant_by_company(
    company_name: str,
    db: Session = Depends(get_super_admin_db)
):
    """
    Find tenant by company name (case-insensitive search).
    
    This is the PRIMARY endpoint for HRMS login. Users provide their company name
    during login, and this returns the tenant database connection info.
    
    This allows ANY user in the company to login without pre-registration!
    
    Args:
        company_name: Company name to search for (case-insensitive)
        db: Database session
        
    Returns:
        dict with tenant_id, db_url, and company_name
        
    Raises:
        HTTPException: 404 if tenant not found or inactive
    """
    # Case-insensitive search using LOWER() function
    tenant = db.query(Tenant).filter(
        func.lower(Tenant.company_name) == func.lower(company_name),
        Tenant.status == "active"
    ).first()
    
    if not tenant:
        logger.warning(f"Tenant not found for company: {company_name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active tenant found for company: {company_name}"
        )
    
    # Override host/port for local development if LOCAL_DB_HOST is set
    db_host = settings.LOCAL_DB_HOST if settings.LOCAL_DB_HOST else tenant.db_host
    db_port = settings.LOCAL_DB_PORT if settings.LOCAL_DB_PORT else tenant.db_port
    
    # Construct db_url from tenant's database connection fields
    # Format: postgresql+psycopg2://user:password@host:port/db_name
    db_url = f"postgresql+psycopg2://{tenant.db_user}:{tenant.db_password}@{db_host}:{db_port}/{tenant.db_name}"
    
    logger.info(f"Found tenant {tenant.id} ({tenant.name}) for company: {company_name}")
    
    return TenantByEmailResponse(
        tenant_id=tenant.id,
        db_url=db_url,
        company_name=tenant.company_name
    )


@router.get("/find-by-email/{email}", response_model=TenantByEmailResponse)
def find_tenant_by_email(
    email: str,
    db: Session = Depends(get_super_admin_db)
):
    """
    Find tenant by admin_email (case-insensitive search).
    
    DEPRECATED: Use /find-by-company/{company_name} instead for better UX.
    This endpoint is kept for backwards compatibility.
    
    Args:
        email: Email address to search for (case-insensitive)
        db: Database session
        
    Returns:
        dict with tenant_id, db_url, and company_name
        
    Raises:
        HTTPException: 404 if tenant not found
    """
    # Case-insensitive search using LOWER() function
    tenant = db.query(Tenant).filter(
        func.lower(Tenant.admin_email) == func.lower(email),
        Tenant.status == "active"
    ).first()
    
    if not tenant:
        logger.warning(f"Tenant not found for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found for email"
        )
    
    # Override host/port for local development if LOCAL_DB_HOST is set
    db_host = settings.LOCAL_DB_HOST if settings.LOCAL_DB_HOST else tenant.db_host
    db_port = settings.LOCAL_DB_PORT if settings.LOCAL_DB_PORT else tenant.db_port
    
    # Construct db_url from tenant's database connection fields
    # Format: postgresql+psycopg2://user:password@host:port/db_name
    db_url = f"postgresql+psycopg2://{tenant.db_user}:{tenant.db_password}@{db_host}:{db_port}/{tenant.db_name}"
    
    logger.info(f"Found tenant {tenant.id} ({tenant.name}) for email: {email}")
    
    return TenantByEmailResponse(
        tenant_id=tenant.id,
        db_url=db_url,
        company_name=tenant.company_name if hasattr(tenant, 'company_name') else tenant.name
    )


@router.get("/{tenant_id}", response_model=TenantByIdResponse)
def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_super_admin_db)
):
    """
    Get tenant by ID.
    
    This endpoint is used by the HRMS backend to retrieve tenant information
    by tenant ID.
    
    Args:
        tenant_id: The tenant ID to retrieve
        db: Database session
        
    Returns:
        dict with tenant information including id, tenant_id, db_url, company_name, admin_email
        
    Raises:
        HTTPException: 404 if tenant not found
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        logger.warning(f"Tenant {tenant_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    
    # Override host/port for local development if LOCAL_DB_HOST is set
    db_host = settings.LOCAL_DB_HOST if settings.LOCAL_DB_HOST else tenant.db_host
    db_port = settings.LOCAL_DB_PORT if settings.LOCAL_DB_PORT else tenant.db_port
    
    # Construct db_url from tenant's database connection fields
    # Format: postgresql+psycopg2://user:password@host:port/db_name
    db_url = f"postgresql+psycopg2://{tenant.db_user}:{tenant.db_password}@{db_host}:{db_port}/{tenant.db_name}"
    
    logger.info(f"Retrieved tenant {tenant.id} ({tenant.name})")
    
    return TenantByIdResponse(
        id=tenant.id,
        tenant_id=tenant.id,  # Alias for compatibility
        db_url=db_url,
        company_name=tenant.name,
        admin_email=tenant.admin_email
    )

