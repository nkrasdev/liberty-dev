import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import aiobotocore.session
from botocore.exceptions import ClientError

from shared.schemas.scraper_data import ScraperData
from shared.utils.logging import get_logger
from shared.utils.retry import with_retry

logger = get_logger(__name__)

# Global S3 service instance
_s3_service: Optional["S3Service"] = None


class S3Service:
    """S3-compatible storage service for MinIO."""
    
    def __init__(self):
        self.endpoint_url = f"http://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}"
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket = os.getenv("MINIO_BUCKET", "aggregator-data")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        # Create session
        self.session = aiobotocore.session.get_session()
    
    async def _get_client(self):
        """Get S3 client."""
        return self.session.create_client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            use_ssl=self.secure,
        )
    
    @with_retry(max_attempts=3)
    async def store_scraper_data(self, scraper_data: ScraperData) -> str:
        """Store scraper data in S3."""
        try:
            # Create S3 key
            timestamp = datetime.utcnow().strftime("%Y/%m/%d")
            s3_key = f"scraper-data/{scraper_data.source}/{timestamp}/{scraper_data.id}.json"
            
            # Prepare data
            data = {
                "id": str(scraper_data.id),
                "source": scraper_data.source,
                "external_id": scraper_data.external_id,
                "raw_data": scraper_data.raw_data,
                "status": scraper_data.status,
                "error_message": scraper_data.error_message,
                "created_at": scraper_data.created_at.isoformat(),
                "updated_at": scraper_data.updated_at.isoformat(),
            }
            
            # Upload to S3
            async with await self._get_client() as client:
                await client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=json.dumps(data, indent=2),
                    ContentType="application/json",
                )
            
            logger.info("Stored scraper data in S3", s3_key=s3_key)
            return s3_key
            
        except Exception as e:
            logger.error("Failed to store scraper data in S3", error=str(e))
            raise
    
    @with_retry(max_attempts=3)
    async def get_scraper_data(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get scraper data from S3."""
        try:
            async with await self._get_client() as client:
                response = await client.get_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                )
                
                data = await response['Body'].read()
                return json.loads(data.decode('utf-8'))
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning("Scraper data not found in S3", s3_key=s3_key)
                return None
            raise
        except Exception as e:
            logger.error("Failed to get scraper data from S3", s3_key=s3_key, error=str(e))
            raise
    
    @with_retry(max_attempts=3)
    async def store_product_image(self, product_id: UUID, image_data: bytes, content_type: str) -> str:
        """Store product image in S3."""
        try:
            # Create S3 key
            s3_key = f"product-images/{product_id}.jpg"
            
            # Upload to S3
            async with await self._get_client() as client:
                await client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=image_data,
                    ContentType=content_type,
                )
            
            logger.info("Stored product image in S3", s3_key=s3_key)
            return s3_key
            
        except Exception as e:
            logger.error("Failed to store product image in S3", error=str(e))
            raise
    
    @with_retry(max_attempts=3)
    async def get_product_image_url(self, product_id: UUID, expires_in: int = 3600) -> Optional[str]:
        """Get presigned URL for product image."""
        try:
            s3_key = f"product-images/{product_id}.jpg"
            
            async with await self._get_client() as client:
                url = await client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': s3_key},
                    ExpiresIn=expires_in,
                )
            
            return url
            
        except Exception as e:
            logger.error("Failed to generate presigned URL", product_id=str(product_id), error=str(e))
            return None
    
    async def ensure_bucket_exists(self) -> None:
        """Ensure the S3 bucket exists."""
        try:
            async with await self._get_client() as client:
                try:
                    await client.head_bucket(Bucket=self.bucket)
                    logger.info("S3 bucket exists", bucket=self.bucket)
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        # Bucket doesn't exist, create it
                        await client.create_bucket(Bucket=self.bucket)
                        logger.info("Created S3 bucket", bucket=self.bucket)
                    else:
                        raise
                        
        except Exception as e:
            logger.error("Failed to ensure bucket exists", bucket=self.bucket, error=str(e))
            raise


async def init_s3() -> None:
    """Initialize S3 service."""
    global _s3_service
    
    try:
        _s3_service = S3Service()
        await _s3_service.ensure_bucket_exists()
        logger.info("S3 service initialized")
    except Exception as e:
        logger.error("Failed to initialize S3 service", error=str(e))
        raise


def get_s3_service() -> S3Service:
    """Get S3 service instance."""
    if _s3_service is None:
        raise RuntimeError("S3 service not initialized")
    return _s3_service
