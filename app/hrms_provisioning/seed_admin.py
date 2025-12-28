"""Module for seeding initial admin user into tenant databases.

This module directly inserts the admin user using SQLAlchemy Core (not ORM)
to avoid importing any HRMS backend models.
"""
from sqlalchemy import create_engine, text, MetaData, Table
import logging

logger = logging.getLogger(__name__)


def seed_initial_admin(db_url: str, admin_email: str, hashed_password: str) -> None:
    """
    Seed an initial admin user into a tenant database using SQL.
    
    This function uses SQLAlchemy Core to insert the admin user directly
    without importing any HRMS backend models.
    
    Args:
        db_url: Database URL for the tenant database
        admin_email: Email address for the admin user
        hashed_password: Bcrypt hashed password (already hashed)
        
    Raises:
        Exception: If seeding fails
    """
    try:
        # Create engine for tenant database
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
                raise Exception(
                    "Users table does not exist. "
                    "Migrations may not have run successfully."
                )
            
            # Check if admin user already exists
            result = connection.execute(
                text("SELECT email FROM users WHERE email = :email"),
                {"email": admin_email}
            )
            existing_user = result.first()
            
            if existing_user:
                logger.warning(f"Admin user with email {admin_email} already exists")
                return
            
            # Extract name from email for full_name
            email_name = admin_email.split('@')[0] if '@' in admin_email else "Admin"
            full_name = email_name.replace('.', ' ').replace('_', ' ').title() or "Admin User"
            
            # Insert admin user
            connection.execute(
                text("""
                    INSERT INTO users (email, full_name, hashed_password, role, is_active)
                    VALUES (:email, :full_name, :hashed_password, :role, :is_active)
                """),
                {
                    "email": admin_email,
                    "full_name": full_name,
                    "hashed_password": hashed_password,
                    "role": "admin",
                    "is_active": True
                }
            )
            connection.commit()
            
            logger.info(f"Successfully seeded admin user: {admin_email}")
            
    except Exception as e:
        logger.error(f"Failed to seed admin user: {str(e)}")
        raise
