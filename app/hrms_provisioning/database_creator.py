"""Module for creating PostgreSQL databases."""
from app.database import server_engine
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


def create_database(db_name: str) -> None:
    """
    Create a new PostgreSQL database.
    
    Args:
        db_name: Name of the database to create
        
    Raises:
        Exception: If database creation fails
    """
    # Sanitize database name - PostgreSQL identifiers need to be quoted if they contain special chars
    # But we'll use a safe naming convention, so we can quote it for safety
    safe_db_name = db_name.replace('"', '""')  # Escape quotes
    
    try:
        with server_engine.connect() as conn:
            # Use IF NOT EXISTS to avoid errors if database already exists
            # PostgreSQL doesn't support IF NOT EXISTS for CREATE DATABASE in older versions
            # So we'll use a try-except or check first
            # Note: AUTOCOMMIT mode is set on server_engine, so no commit() needed
            conn.execute(text(f'CREATE DATABASE "{safe_db_name}"'))
        logger.info(f"Successfully created database: {db_name}")
    except Exception as e:
        logger.error(f"Failed to create database {db_name}: {str(e)}")
        raise

