"""SQLAlchemy models for Super Admin Service."""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

SuperAdminBase = declarative_base()


class Tenant(SuperAdminBase):
    """Model representing a tenant in the system."""
    
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    db_name = Column(String, nullable=False, unique=True, index=True)
    db_host = Column(String, nullable=False, default="localhost")
    db_port = Column(String, nullable=False, default="5432")
    db_user = Column(String, nullable=False)
    db_password = Column(String, nullable=False)
    admin_email = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', db_name='{self.db_name}')>"

