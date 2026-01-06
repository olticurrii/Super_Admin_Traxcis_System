"""Model for tenant user email mappings."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from app.superadmin.models import SuperAdminBase


class TenantUser(SuperAdminBase):
    """
    Model for mapping user emails to their tenant.
    
    This allows the Super Admin service to route login requests
    for ANY user (not just admins) to the correct tenant database.
    """
    
    __tablename__ = "tenant_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Ensure email is unique across all tenants
    __table_args__ = (
        UniqueConstraint('email', name='uq_tenant_user_email'),
    )
    
    def __repr__(self):
        return f"<TenantUser(email='{self.email}', tenant_id={self.tenant_id})>"

