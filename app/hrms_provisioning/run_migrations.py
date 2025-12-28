"""Module for running tenant database migrations using subprocess.

This module runs Alembic migrations via subprocess to avoid importing
any HRMS backend code. All migrations are self-contained in tenant_migrations/.
"""
import subprocess
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def run_tenant_migrations(db_url: str) -> None:
    """
    Run tenant database migrations using Alembic subprocess.
    
    This function:
    1. Sets DATABASE_URL environment variable
    2. Runs: alembic -c tenant_migrations/alembic.ini upgrade head
    3. Does NOT import any HRMS backend code
    
    Args:
        db_url: Database URL for the tenant database
        
    Raises:
        Exception: If migrations fail
    """
    # Get the path to tenant_migrations/alembic.ini
    # Use absolute path to ensure it works from any directory
    base_dir = Path(__file__).resolve().parent.parent
    alembic_ini_path = base_dir / "tenant_migrations" / "alembic.ini"
    
    if not alembic_ini_path.exists():
        raise FileNotFoundError(
            f"Tenant migrations configuration not found at: {alembic_ini_path}"
        )
    
    logger.info(f"Running tenant migrations from: {alembic_ini_path}")
    logger.info(f"Target database: {db_url[:50]}...")
    
    # Prepare environment variables
    env = os.environ.copy()
    env['DATABASE_URL'] = db_url
    
    # Run alembic upgrade head via subprocess
    try:
        result = subprocess.run(
            [
                'alembic',
                '-c', str(alembic_ini_path),
                'upgrade', 'head'
            ],
            env=env,
            capture_output=True,
            text=True,
            check=True,
            cwd=str(base_dir)  # Run from project root
        )
        
        logger.info("Migration subprocess completed successfully")
        logger.info(f"Output: {result.stdout}")
        
        if result.stderr:
            logger.warning(f"Migration warnings: {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed with exit code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise Exception(
            f"Failed to run tenant migrations: {e.stderr or e.stdout or str(e)}"
        )
    except FileNotFoundError:
        raise Exception(
            "Alembic command not found. Make sure alembic is installed: "
            "pip install alembic"
        )
