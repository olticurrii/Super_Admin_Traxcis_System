"""
Re-seed admin users for all tenants after schema recreation.
"""
from sqlalchemy import create_engine, text
from app.config import settings
from app.security import hash_password
from app.utils import generate_secure_password
import logging

logger = logging.getLogger(__name__)


def reseed_tenant_admin(db_name: str, admin_email: str, tenant_id: int) -> dict:
    """
    Re-seed admin user in a tenant database.
    
    Args:
        db_name: Name of the tenant database
        admin_email: Email for the admin user
        tenant_id: The Super Admin tenant ID
        
    Returns:
        dict with status, message, and new password
    """
    try:
        # Construct database URL
        db_url = f"{settings.POSTGRES_SERVER_URL.rsplit('/', 1)[0]}/{db_name}"
        db_url = db_url.replace('/postgres', f'/{db_name}')
        
        engine = create_engine(db_url, pool_pre_ping=True)
        
        # Generate new password
        new_password = generate_secure_password(12)
        hashed_password = hash_password(new_password)
        
        with engine.connect() as connection:
            # Check if admin user already exists
            result = connection.execute(
                text("SELECT id FROM users WHERE email = :email LIMIT 1"),
                {"email": admin_email}
            )
            existing_user = result.fetchone()
            
            if existing_user:
                # Update existing admin user
                connection.execute(
                    text("""
                        UPDATE users 
                        SET hashed_password = :password,
                            tenant_id = :tenant_id,
                            is_admin = true,
                            role = 'admin',
                            is_active = true
                        WHERE email = :email
                    """),
                    {
                        "password": hashed_password,
                        "tenant_id": tenant_id,
                        "email": admin_email
                    }
                )
                logger.info(f"Updated admin user for {db_name}")
            else:
                # Insert new admin user
                connection.execute(
                    text("""
                        INSERT INTO users (
                            tenant_id, email, full_name, hashed_password,
                            role, is_admin, is_active
                        ) VALUES (
                            :tenant_id, :email, :full_name, :password,
                            'admin', true, true
                        )
                    """),
                    {
                        "tenant_id": tenant_id,
                        "email": admin_email,
                        "full_name": "Admin User",
                        "password": hashed_password
                    }
                )
                logger.info(f"Created new admin user for {db_name}")
            
            connection.commit()
            
            return {
                "status": "success",
                "message": f"Admin user re-seeded for {db_name}",
                "password": new_password
            }
            
    except Exception as e:
        logger.error(f"Failed to reseed admin for {db_name}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to reseed admin: {str(e)}",
            "password": None
        }


