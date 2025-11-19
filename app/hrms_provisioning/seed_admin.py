"""Module for seeding initial admin user into tenant databases."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.hrms_provisioning.models_stub import get_hrms_user_model
import logging

logger = logging.getLogger(__name__)


def seed_initial_admin(db_url: str, admin_email: str, hashed_password: str) -> None:
    """
    Seed an initial admin user into a tenant database.
    
    Args:
        db_url: Database URL for the tenant database
        admin_email: Email address for the admin user
        hashed_password: Bcrypt hashed password
        
    Raises:
        Exception: If seeding fails
    """
    try:
        # Create engine for tenant database
        engine = create_engine(db_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Get the HRMS User model
        User = get_hrms_user_model()
        
        # Create session
        db = SessionLocal()
        
        try:
            # Check if admin user already exists
            existing_user = db.query(User).filter(User.email == admin_email).first()
            if existing_user:
                logger.warning(f"Admin user with email {admin_email} already exists")
                return
            
            # Create new admin user
            admin_user = User(
                email=admin_email,
                hashed_password=hashed_password,
                role="admin",
                is_active=True
            )
            
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

