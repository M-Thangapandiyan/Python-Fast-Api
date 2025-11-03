"""
FastAPI application main entry point.
"""

from app.utils.logger import logger

from fastapi import FastAPI
from app.core.config import settings
from contextlib import asynccontextmanager
from app.routes import auth_router, document_router, user_router
from app.db.dynamodb import get_document_table, get_user_table


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown."""
    
    get_user_table()
    get_document_table()
    logger.info("All required tables are ready.")
    logger.info("Application starting...")
    yield
    # Shutdown
    logger.info("Application shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url=settings.DOCS_URL,
    lifespan=lifespan
)

# Include routers
app.include_router(auth_router.router)
app.include_router(document_router.router)
app.include_router(user_router.router)


@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": settings.DOCS_URL,
        "endpoints": {
            "documents": f"{settings.API_V1_PREFIX}/documents",
            "users": f"{settings.API_V1_PREFIX}/user",
            "login": "/login",
            "refresh": "/refresh"
        }
    }


@app.get(settings.HEALTH_CHECK_ENDPOINT)
def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}