"""Main FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.superadmin.router import router as super_admin_router
from app.tenants.router import router as tenants_router
from app.database import init_db
import logging
import traceback
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI instance
app = FastAPI(
    title="Super Admin Service",
    description="Service for creating and managing tenant databases for HRMS system",
    version="1.0.0"
)

# CORS origins - combine default with environment variable
cors_origins = [
    # Local development
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # Production - Vercel frontend
    "https://super-admin-traxcis-system.vercel.app",
]

# Add additional origins from environment variable (for Vercel preview deployments)
additional_origins = os.getenv("CORS_ORIGINS", "")
if additional_origins:
    cors_origins.extend([origin.strip() for origin in additional_origins.split(",") if origin.strip()])

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(super_admin_router)
app.include_router(tenants_router)


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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to log all errors."""
    import traceback
    error_trace = traceback.format_exc()
    logger.error(f"Unhandled exception: {str(exc)}\n{error_trace}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )

