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
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Create all tables
    SuperAdminBase.metadata.create_all(bind=super_admin_engine)
    
    # Add company_name column if it doesn't exist (migration)
    try:
        inspector = inspect(super_admin_engine)
        columns = [col['name'] for col in inspector.get_columns('tenants')]
        
        if 'company_name' not in columns:
            logger.info("Adding company_name column to tenants table...")
            
            with super_admin_engine.begin() as connection:
                # Add column (nullable first)
                connection.execute(text("ALTER TABLE tenants ADD COLUMN company_name VARCHAR"))
                logger.info("✓ Column added")
                
                # Set default value for existing rows
                connection.execute(text("UPDATE tenants SET company_name = name WHERE company_name IS NULL"))
                logger.info("✓ Default values set")
                
                # Fix duplicates before adding unique constraint
                result = connection.execute(text("""
                    WITH duplicates AS (
                        SELECT id, company_name,
                               ROW_NUMBER() OVER (PARTITION BY company_name ORDER BY id) as rn
                        FROM tenants
                        WHERE company_name IS NOT NULL
                    )
                    UPDATE tenants
                    SET company_name = tenants.company_name || '_' || tenants.id
                    FROM duplicates
                    WHERE tenants.id = duplicates.id AND duplicates.rn > 1
                """))
                if result.rowcount > 0:
                    logger.info(f"✓ Fixed {result.rowcount} duplicate company names")
                
                # Make it NOT NULL
                connection.execute(text("ALTER TABLE tenants ALTER COLUMN company_name SET NOT NULL"))
                logger.info("✓ NOT NULL constraint added")
                
                # Add unique constraint
                connection.execute(text("ALTER TABLE tenants ADD CONSTRAINT uq_tenant_company_name UNIQUE (company_name)"))
                logger.info("✓ Unique constraint added")
                
                # Add index
                connection.execute(text("CREATE INDEX ix_tenants_company_name ON tenants (company_name)"))
                logger.info("✓ Index created")
                
            logger.info("✅ company_name column successfully added to tenants table")
        else:
            # Column exists, but check if constraints are missing (from previous failed migration)
            logger.info("company_name column already exists, checking constraints...")
            
            with super_admin_engine.begin() as connection:
                # Check if unique constraint exists
                constraint_check = connection.execute(text("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'tenants' 
                    AND constraint_name = 'uq_tenant_company_name'
                """))
                
                if not constraint_check.fetchone():
                    logger.info("Unique constraint missing, adding it now...")
                    
                    # Fix duplicates first
                    result = connection.execute(text("""
                        WITH duplicates AS (
                            SELECT id, company_name,
                                   ROW_NUMBER() OVER (PARTITION BY company_name ORDER BY id) as rn
                            FROM tenants
                            WHERE company_name IS NOT NULL
                        )
                        UPDATE tenants
                        SET company_name = tenants.company_name || '_' || tenants.id
                        FROM duplicates
                        WHERE tenants.id = duplicates.id AND duplicates.rn > 1
                    """))
                    if result.rowcount > 0:
                        logger.info(f"✓ Fixed {result.rowcount} duplicate company names")
                    
                    # Add unique constraint
                    connection.execute(text("ALTER TABLE tenants ADD CONSTRAINT uq_tenant_company_name UNIQUE (company_name)"))
                    logger.info("✓ Unique constraint added")
                    
                # Check if index exists
                index_check = connection.execute(text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'tenants' 
                    AND indexname = 'ix_tenants_company_name'
                """))
                
                if not index_check.fetchone():
                    logger.info("Index missing, creating it now...")
                    connection.execute(text("CREATE INDEX ix_tenants_company_name ON tenants (company_name)"))
                    logger.info("✓ Index created")
            
            logger.info("✅ company_name column and constraints verified")
            
    except Exception as e:
        logger.error(f"❌ Failed to add company_name column: {str(e)}")
        raise  # Re-raise to prevent service from starting with broken schema


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

