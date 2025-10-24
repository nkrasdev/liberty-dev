import os
from typing import Any, Dict, Optional
from uuid import UUID

import asyncpg
from shared.utils.logging import get_logger
from shared.utils.retry import with_retry

logger = get_logger(__name__)


class ProductRepository:
    """Repository for product data operations."""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/aggregator")
        self._pool = None
    
    async def _get_pool(self):
        """Get database connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.database_url)
        return self._pool
    
    @with_retry(max_attempts=3)
    async def get_by_source_and_external_id(self, source: str, external_id: str) -> Optional[Dict[str, Any]]:
        """Get product by source and external ID."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                query = """
                    SELECT id, name, brand, price, currency, description, image_url, 
                           source_url, source, external_id, size, color, condition, 
                           availability, created_at, updated_at
                    FROM products 
                    WHERE source = $1 AND external_id = $2
                """
                row = await conn.fetchrow(query, source, external_id)
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(
                "Failed to get product by source and external_id",
                source=source,
                external_id=external_id,
                error=str(e)
            )
            raise
    
    @with_retry(max_attempts=3)
    async def create_product(self, product_data: Dict[str, Any]) -> UUID:
        """Create a new product."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                query = """
                    INSERT INTO products (
                        name, brand, price, currency, description, image_url,
                        source_url, source, external_id, size, color, condition, availability
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                    ) RETURNING id
                """
                
                product_id = await conn.fetchval(
                    query,
                    product_data["name"],
                    product_data["brand"],
                    product_data["price"],
                    product_data["currency"],
                    product_data.get("description"),
                    product_data.get("image_url"),
                    product_data["source_url"],
                    product_data["source"],
                    product_data["external_id"],
                    product_data.get("size"),
                    product_data.get("color"),
                    product_data.get("condition"),
                    product_data.get("availability", True)
                )
                
                logger.info("Product created", product_id=str(product_id))
                return product_id
                
        except Exception as e:
            logger.error("Failed to create product", error=str(e))
            raise
    
    @with_retry(max_attempts=3)
    async def update_product(self, product_id: UUID, product_data: Dict[str, Any]) -> None:
        """Update an existing product."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                # Build dynamic update query
                set_clauses = []
                values = []
                param_count = 1
                
                for field, value in product_data.items():
                    if field in ["name", "brand", "price", "currency", "description", 
                               "image_url", "source_url", "size", "color", "condition", "availability"]:
                        set_clauses.append(f"{field} = ${param_count}")
                        values.append(value)
                        param_count += 1
                
                if not set_clauses:
                    return
                
                query = f"""
                    UPDATE products 
                    SET {', '.join(set_clauses)}, updated_at = NOW()
                    WHERE id = ${param_count}
                """
                values.append(product_id)
                
                await conn.execute(query, *values)
                
                logger.info("Product updated", product_id=str(product_id))
                
        except Exception as e:
            logger.error("Failed to update product", product_id=str(product_id), error=str(e))
            raise
    
    @with_retry(max_attempts=3)
    async def delete_product(self, product_id: UUID) -> None:
        """Delete a product."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                query = "DELETE FROM products WHERE id = $1"
                await conn.execute(query, product_id)
                
                logger.info("Product deleted", product_id=str(product_id))
                
        except Exception as e:
            logger.error("Failed to delete product", product_id=str(product_id), error=str(e))
            raise
    
    async def close(self):
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
