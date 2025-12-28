"""Configuration settings for Super Admin Service."""
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # PostgreSQL server admin URL for creating databases
    POSTGRES_SERVER_URL: str = os.getenv(
        "POSTGRES_SERVER_URL",
        "postgresql+psycopg2://olticurri:84SuVnkW0msge8tAYGD7UhEKanOQDegC@dpg-d55fjm0gjchc738eo1og-a/postgres"
    )
    
    # Super Admin database URL
    POSTGRES_SUPER_ADMIN_URL: str = os.getenv(
        "POSTGRES_SUPER_ADMIN_URL",
        "postgresql+psycopg2://olticurri:84SuVnkW0msge8tAYGD7UhEKanOQDegC@dpg-d55fjm0gjchc738eo1og-a/super_admin_db_qvvv"
    )
    
    # Database connection defaults
    DB_HOST: str = os.getenv("DB_HOST", "dpg-d55fjm0gjchc738eo1og-a")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_USER: str = os.getenv("DB_USER", "olticurri")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "84SuVnkW0msge8tAYGD7UhEKanOQDegC")
    
    class Config:
        case_sensitive = True


settings = Settings()


