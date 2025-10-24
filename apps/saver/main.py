import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from faststream import FastStream
from faststream.rabbit import RabbitBroker

from apps.saver.consumers.scraper_consumer import router as scraper_router
from apps.saver.domain.s3 import init_s3
from shared.utils.logging import setup_logging, get_logger
from shared.utils.metrics import setup_metrics

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastStream) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Saver application")
    
    # Setup logging and metrics
    setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_format=os.getenv("LOG_FORMAT", "json")
    )
    setup_metrics()
    
    # Initialize S3
    await init_s3()
    
    logger.info("Saver application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Saver application")


# Create broker
broker = RabbitBroker(os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"))

# Create FastStream app
app = FastStream(broker, lifespan=lifespan)

# Include routers
app.include_router(scraper_router)


@app.after_startup
async def after_startup():
    """After startup hook."""
    logger.info("Saver application is ready to process messages")


if __name__ == "__main__":
    import asyncio
    
    async def main():
        await app.run()
    
    asyncio.run(main())
