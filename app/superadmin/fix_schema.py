"""Utility to fix schema for existing tenant databases."""
from sqlalchemy import create_engine, text
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def fix_tenant_schema(db_name: str, tenant_id: int) -> dict:
    """
    Add missing columns to an existing tenant database.
    
    Args:
        db_name: Name of the tenant database to fix
        tenant_id: The Super Admin tenant ID this database belongs to
        
    Returns:
        dict with status and message
    """
    try:
        # Construct database URL for the tenant
        db_url = f"{settings.POSTGRES_SERVER_URL.rsplit('/', 1)[0]}/{db_name}"
        db_url = db_url.replace('/postgres', f'/{db_name}')
        
        # Create engine
        engine = create_engine(db_url, pool_pre_ping=True)
        
        with engine.connect() as connection:
            # Check if users table exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                return {
                    "status": "error",
                    "message": f"Users table does not exist in {db_name}"
                }
            
            # Check if is_admin column already exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                    AND column_name = 'is_admin'
                );
            """))
            column_exists = result.scalar()
            
            if column_exists:
                # Still run the full fix to ensure all columns exist
                pass
            
            # Add ALL missing columns from HRMS backend User model
            connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false NOT NULL,
                ADD COLUMN IF NOT EXISTS job_role VARCHAR,
                ADD COLUMN IF NOT EXISTS department_id INTEGER,
                ADD COLUMN IF NOT EXISTS manager_id INTEGER,
                ADD COLUMN IF NOT EXISTS avatar_url VARCHAR,
                ADD COLUMN IF NOT EXISTS phone VARCHAR,
                ADD COLUMN IF NOT EXISTS hire_date DATE,
                ADD COLUMN IF NOT EXISTS timezone VARCHAR DEFAULT 'UTC',
                ADD COLUMN IF NOT EXISTS locale VARCHAR DEFAULT 'en',
                ADD COLUMN IF NOT EXISTS theme VARCHAR DEFAULT 'light',
                ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT true NOT NULL;
            """))
            
            # Update admin users and set correct tenant_id from Super Admin
            # Set default values for nullable fields
            result = connection.execute(
                text("""
                    UPDATE users 
                    SET is_admin = true,
                        tenant_id = COALESCE(tenant_id, :tenant_id),
                        timezone = COALESCE(timezone, 'UTC'),
                        locale = COALESCE(locale, 'en'),
                        theme = COALESCE(theme, 'light'),
                        email_notifications = COALESCE(email_notifications, true)
                    WHERE role = 'admin';
                """),
                {"tenant_id": tenant_id}
            )
            updated_count = result.rowcount
            
            connection.commit()
            
            logger.info(f"Added all missing columns to {db_name}, updated {updated_count} admin users")
            
            return {
                "status": "success",
                "message": f"Added all missing columns to {db_name}, updated {updated_count} admin users"
            }
            
    except Exception as e:
        logger.error(f"Failed to fix schema for {db_name}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fix schema: {str(e)}"
        }

