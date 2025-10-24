import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.catalog.router import router as catalog_router
from apps.api.common.db import init_db
from apps.api.common.cache import init_cache
from shared.utils.logging import setup_logging, get_logger
from shared.utils.metrics import setup_metrics

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting API application")
    
    # Setup logging and metrics
    setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_format=os.getenv("LOG_FORMAT", "json")
    )
    setup_metrics()
    
    # Initialize database and cache
    await init_db()
    await init_cache()
    
    logger.info("API application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API application")


# Create FastAPI app
app = FastAPI(
    title="Aggregator API",
    description="E-commerce aggregator API",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(catalog_router, prefix="/api/v1", tags=["catalog"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from shared.utils.metrics import get_metrics
    from fastapi.responses import Response
    
    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type="text/plain")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "1"))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        reload=True,
    )
