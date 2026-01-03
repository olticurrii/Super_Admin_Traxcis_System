"""Utility to fix schema for existing tenant databases."""
from sqlalchemy import create_engine, text
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def fix_tenant_schema(db_name: str) -> dict:
    """
    Add missing is_admin column to an existing tenant database.
    
    Args:
        db_name: Name of the tenant database to fix
        
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
                return {
                    "status": "success",
                    "message": f"is_admin column already exists in {db_name}"
                }
            
            # Add is_admin column
            connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_admin BOOLEAN DEFAULT false NOT NULL;
            """))
            
            # Update admin users
            result = connection.execute(text("""
                UPDATE users 
                SET is_admin = true 
                WHERE role = 'admin';
            """))
            updated_count = result.rowcount
            
            connection.commit()
            
            logger.info(f"Added is_admin column to {db_name}, updated {updated_count} admin users")
            
            return {
                "status": "success",
                "message": f"Added is_admin column to {db_name}, updated {updated_count} admin users"
            }
            
    except Exception as e:
        logger.error(f"Failed to fix schema for {db_name}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fix schema: {str(e)}"
        }

