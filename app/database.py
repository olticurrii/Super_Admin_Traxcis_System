"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.superadmin.models import SuperAdminBase
# Import all models so they're registered with SuperAdminBase.metadata
from app.superadmin.models import Tenant  # noqa: F401
from app.superadmin.tenant_users_model import TenantUser  # noqa: F401


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
    from sqlalchemy import text, inspect
    
    # Create all tables
    SuperAdminBase.metadata.create_all(bind=super_admin_engine)
    
    # Add company_name column if it doesn't exist (migration)
    try:
        inspector = inspect(super_admin_engine)
        columns = [col['name'] for col in inspector.get_columns('tenants')]
        
        if 'company_name' not in columns:
            with super_admin_engine.connect() as connection:
                # Add column (nullable first)
                connection.execute(text("ALTER TABLE tenants ADD COLUMN company_name VARCHAR"))
                # Set default value for existing rows
                connection.execute(text("UPDATE tenants SET company_name = name WHERE company_name IS NULL"))
                # Make it NOT NULL
                connection.execute(text("ALTER TABLE tenants ALTER COLUMN company_name SET NOT NULL"))
                # Add unique constraint
                connection.execute(text("ALTER TABLE tenants ADD CONSTRAINT uq_tenant_company_name UNIQUE (company_name)"))
                # Add index
                connection.execute(text("CREATE INDEX ix_tenants_company_name ON tenants (company_name)"))
                connection.commit()
                print("✅ Added company_name column to tenants table")
    except Exception as e:
        print(f"Note: company_name column migration: {str(e)}")


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

