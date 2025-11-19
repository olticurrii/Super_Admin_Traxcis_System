"""Pydantic schemas for Super Admin Service."""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""
    name: str
    admin_email: EmailStr


class TenantResponse(BaseModel):
    """Schema for tenant response."""
    tenant_id: int
    tenant_db: str
    admin_email: str
    initial_password: str
    
    class Config:
        from_attributes = True


class TenantInfo(BaseModel):
    """Schema for tenant information (without sensitive data)."""
    id: int
    name: str
    db_name: str
    db_host: str
    db_port: str
    db_user: str
    admin_email: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

