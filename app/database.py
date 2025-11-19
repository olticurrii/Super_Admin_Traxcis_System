"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.superadmin.models import SuperAdminBase


# Engine for super_admin_db (for tenant metadata storage)
super_admin_engine = create_engine(
    settings.POSTGRES_SUPER_ADMIN_URL,
    pool_pre_ping=True,
    echo=False
)

# Engine for PostgreSQL server (for CREATE DATABASE operations)
# Use AUTOCOMMIT isolation level to allow DDL operations
server_engine = create_engine(
    settings.POSTGRES_SERVER_URL,
    isolation_level="AUTOCOMMIT",
    pool_pre_ping=True,
    echo=False
)

# Session factory for super_admin_db
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=super_admin_engine)


def init_db():
    """Initialize the super_admin_db by creating all tables."""
    SuperAdminBase.metadata.create_all(bind=super_admin_engine)


def get_super_admin_db() -> Session:
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

