"""Main FastAPI application."""
from fastapi import FastAPI
from app.superadmin.router import router as super_admin_router
from app.database import init_db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI instance
app = FastAPI(
    title="Super Admin Service",
    description="Service for creating and managing tenant databases for HRMS system",
    version="1.0.0"
)

# Include routers
app.include_router(super_admin_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"service": "super_admin_service"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

