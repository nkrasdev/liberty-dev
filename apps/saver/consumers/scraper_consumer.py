from typing import Dict, Any

from faststream import Context
from faststream.rabbit import RabbitMessage
from faststream.rabbit.annotations import RabbitStream

from apps.saver.domain.normalize import ProductNormalizer
from apps.saver.domain.repository import ProductRepository
from apps.saver.domain.s3 import S3Service
from shared.schemas.scraper_data import ScraperData
from shared.utils.logging import get_logger
from shared.utils.metrics import SCRAPER_OPERATIONS
from shared.utils.retry import with_retry

logger = get_logger(__name__)


@RabbitStream.subscribe("scraper.data.received")
async def process_scraper_data(
    message: ScraperData,
    stream: RabbitStream = Context(),
) -> None:
    """Process scraper data and save products."""
    try:
        logger.info(
            "Processing scraper data",
            scraper_data_id=str(message.id),
            source=message.source,
            external_id=message.external_id
        )
        
        # Initialize services
        normalizer = ProductNormalizer()
        repository = ProductRepository()
        s3_service = S3Service()
        
        # Store raw data in S3
        s3_key = await s3_service.store_scraper_data(message)
        logger.info("Stored scraper data in S3", s3_key=s3_key)
        
        # Normalize and save products
        products = await normalizer.normalize_products(message.raw_data, message.source)
        
        products_created = 0
        products_updated = 0
        
        for product_data in products:
            try:
                # Check if product exists
                existing_product = await repository.get_by_source_and_external_id(
                    message.source, 
                    product_data.get("external_id")
                )
                
                if existing_product:
                    # Update existing product
                    await repository.update_product(existing_product["id"], product_data)
                    products_updated += 1
                    logger.info("Updated product", product_id=str(existing_product["id"]))
                else:
                    # Create new product
                    product_id = await repository.create_product(product_data)
                    products_created += 1
                    logger.info("Created product", product_id=str(product_id))
                    
            except Exception as e:
                logger.error(
                    "Failed to process product",
                    product_data=product_data,
                    error=str(e)
                )
                continue
        
        # Update metrics
        SCRAPER_OPERATIONS.labels(
            source=message.source,
            status="completed"
        ).inc()
        
        logger.info(
            "Successfully processed scraper data",
            scraper_data_id=str(message.id),
            products_created=products_created,
            products_updated=products_updated
        )
        
    except Exception as e:
        logger.error(
            "Failed to process scraper data",
            scraper_data_id=str(message.id),
            error=str(e),
            exc_info=True
        )
        
        # Update metrics
        SCRAPER_OPERATIONS.labels(
            source=message.source,
            status="failed"
        ).inc()
        
        # Re-raise to trigger retry mechanism
        raise


@RabbitStream.subscribe("scraper.data.failed")
async def handle_scraper_failure(
    message: Dict[str, Any],
    stream: RabbitStream = Context(),
) -> None:
    """Handle scraper data processing failures."""
    try:
        logger.error(
            "Scraper data processing failed",
            message=message
        )
        
        # Update metrics
        source = message.get("source", "unknown")
        SCRAPER_OPERATIONS.labels(
            source=source,
            status="failed"
        ).inc()
        
    except Exception as e:
        logger.error("Failed to handle scraper failure", error=str(e))
