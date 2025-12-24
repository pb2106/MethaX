"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.api import dashboard_router
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} in {settings.env} mode")
    logger.info(f"Timezone: {settings.tz}")
    
    # Initialize database (creates tables if they don't exist)
    if settings.is_development:
        await init_db()
        logger.info("Database initialized")
    
    logger.info(f"Trading parameters: Capital=₹{settings.default_capital}, "
                f"MaxTrades={settings.max_daily_trades}, Risk={settings.risk_per_trade*100}%")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Institution-grade NIFTY 50 options virtual trading platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(dashboard_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "description": "Institution-grade NIFTY 50 options virtual trading platform",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )
