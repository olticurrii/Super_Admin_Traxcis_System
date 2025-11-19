"""Configuration settings for Super Admin Service."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # PostgreSQL server admin URL for creating databases
    POSTGRES_SERVER_URL: str = "postgresql+psycopg2://postgres:Oc132456@localhost:5432/postgres"
    
    # Super Admin database URL
    POSTGRES_SUPER_ADMIN_URL: str = "postgresql+psycopg2://postgres:Oc132456@localhost:5432/super_admin_db"
    
    # HRMS Alembic configuration path
    HRMS_ALEMBIC_INI_PATH: str = "/Users/olti/Desktop/Projektet e oltit/HR/backend/alembic.ini"
    
    # Database connection defaults
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "Oc132456"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

