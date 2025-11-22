"""Module for seeding initial admin user into tenant databases."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.hrms_provisioning.models_stub import get_hrms_user_model
import logging
import sys
import os
import types

logger = logging.getLogger(__name__)


def seed_initial_admin(db_url: str, admin_email: str, hashed_password: str) -> None:
    """
    Seed an initial admin user into a tenant database.
    
    Args:
        db_url: Database URL for the tenant database
        admin_email: Email address for the admin user
        hashed_password: Bcrypt hashed password (already hashed)
        
    Raises:
        Exception: If seeding fails
    """
    # Temporarily prevent HRMS hashing module from being imported
    # to avoid bcrypt initialization issues
    # Create a stub module to prevent the real one from being imported
    hashing_stub = types.ModuleType('app.core.hashing')
    hashing_stub.hash_password = lambda p: p  # Stub function
    hashing_stub.verify_password = lambda p, h: False  # Stub function
    hashing_stub.Hasher = type('Hasher', (), {
        'hash_password': staticmethod(lambda p: p),
        'verify_password': staticmethod(lambda p, h: False)
    })
    hashing_stub.pwd_context = None
    
    # Save original if it exists
    original_modules = {}
    if 'app.core.hashing' in sys.modules:
        original_modules['app.core.hashing'] = sys.modules['app.core.hashing']
    
    # Install the stub before HRMS modules are imported
    sys.modules['app.core.hashing'] = hashing_stub
    logger.info("Installed stub for app.core.hashing to prevent bcrypt initialization issues")
    
    try:
        # Create engine for tenant database
        engine = create_engine(db_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Get the HRMS User model (this might import hashing, so we handle it above)
        User = get_hrms_user_model()
        
        # Create session
        db = SessionLocal()
        
        try:
            # First, check if the users table exists
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if 'users' not in tables:
                logger.error(f"Users table does not exist. Available tables: {tables}")
                raise Exception(
                    f"Users table not found in database. "
                    f"Migrations may not have run successfully. "
                    f"Available tables: {tables}"
                )
            
            # Check if admin user already exists
            existing_user = db.query(User).filter(User.email == admin_email).first()
            if existing_user:
                logger.warning(f"Admin user with email {admin_email} already exists")
                return
            
            # Create new admin user with the already-hashed password
            # The hashed_password should already be a bcrypt hash (60 chars)
            # Extract name from email for full_name (required field)
            # Use the part before @ as the name, or "Admin" as default
            email_name = admin_email.split('@')[0] if '@' in admin_email else "Admin"
            full_name = email_name.replace('.', ' ').replace('_', ' ').title() or "Admin User"
            
            # Use setattr to bypass any potential property setters
            admin_user = User()
            admin_user.email = admin_email
            admin_user.full_name = full_name
            admin_user.hashed_password = hashed_password
            admin_user.role = "admin"
            admin_user.is_active = True
            
            db.add(admin_user)
            db.commit()
            logger.info(f"Successfully seeded admin user: {admin_email}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to seed admin user: {str(e)}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to connect to tenant database or seed admin: {str(e)}")
        raise
    finally:
        # Restore original modules if they existed
        if original_modules:
            sys.modules.update(original_modules)
        elif 'app.core.hashing' in sys.modules and sys.modules['app.core.hashing'] == hashing_stub:
            # Remove the stub if no original existed
            del sys.modules['app.core.hashing']

