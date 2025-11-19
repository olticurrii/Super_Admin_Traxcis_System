"""Module for running HRMS Alembic migrations on tenant databases."""
from alembic import command
from alembic.config import Config
from app.config import settings
import logging
import os

logger = logging.getLogger(__name__)


def run_hrms_migrations(db_url: str) -> None:
    """
    Run HRMS Alembic migrations on a tenant database.
    
    Args:
        db_url: Database URL for the tenant database
        
    Raises:
        Exception: If migrations fail
    """
    alembic_ini_path = settings.HRMS_ALEMBIC_INI_PATH
    
    if not os.path.exists(alembic_ini_path):
        raise FileNotFoundError(
            f"HRMS Alembic configuration not found at: {alembic_ini_path}"
        )
    
    try:
        # Load the HRMS Alembic configuration
        alembic_cfg = Config(alembic_ini_path)
        
        # Override the sqlalchemy.url with the tenant database URL
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        
        # Run migrations up to head
        logger.info(f"Running HRMS migrations on database: {db_url}")
        command.upgrade(alembic_cfg, "head")
        logger.info("HRMS migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to run HRMS migrations: {str(e)}")
        raise

