import re
from decimal import Decimal
from typing import Any, Dict, List, Optional

from shared.utils.logging import get_logger
from shared.utils.retry import with_retry

logger = get_logger(__name__)


class ProductNormalizer:
    """Normalizes scraped product data into a consistent format."""
    
    def __init__(self):
        self.currency_map = {
            "$": "USD",
            "€": "EUR", 
            "£": "GBP",
            "¥": "JPY",
        }
    
    async def normalize_products(self, raw_data: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
        """Normalize raw scraped data into product format."""
        try:
            if source == "farfetch":
                return await self._normalize_farfetch(raw_data)
            elif source == "goat":
                return await self._normalize_goat(raw_data)
            elif source == "stockx":
                return await self._normalize_stockx(raw_data)
            else:
                logger.warning("Unknown source for normalization", source=source)
                return []
                
        except Exception as e:
            logger.error("Failed to normalize products", source=source, error=str(e))
            return []
    
    async def _normalize_farfetch(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize Farfetch data."""
        products = []
        
        # Extract product information
        name = raw_data.get("name", "")
        brand = raw_data.get("brand", "")
        price_str = raw_data.get("price", "0")
        currency = self._extract_currency(price_str)
        price = self._extract_price(price_str)
        
        # Extract additional fields
        description = raw_data.get("description", "")
        image_url = raw_data.get("image_url", "")
        source_url = raw_data.get("url", "")
        external_id = raw_data.get("id", "")
        size = raw_data.get("size")
        color = raw_data.get("color")
        condition = raw_data.get("condition", "new")
        availability = raw_data.get("availability", True)
        
        product = {
            "name": name,
            "brand": brand,
            "price": price,
            "currency": currency,
            "description": description,
            "image_url": image_url,
            "source_url": source_url,
            "source": "farfetch",
            "external_id": external_id,
            "size": size,
            "color": color,
            "condition": condition,
            "availability": availability,
        }
        
        products.append(product)
        return products
    
    async def _normalize_goat(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize GOAT data."""
        products = []
        
        name = raw_data.get("name", "")
        brand = raw_data.get("brand", "")
        price_str = raw_data.get("price", "0")
        currency = self._extract_currency(price_str)
        price = self._extract_price(price_str)
        
        description = raw_data.get("description", "")
        image_url = raw_data.get("image_url", "")
        source_url = raw_data.get("url", "")
        external_id = raw_data.get("id", "")
        size = raw_data.get("size")
        color = raw_data.get("color")
        condition = raw_data.get("condition", "new")
        availability = raw_data.get("availability", True)
        
        product = {
            "name": name,
            "brand": brand,
            "price": price,
            "currency": currency,
            "description": description,
            "image_url": image_url,
            "source_url": source_url,
            "source": "goat",
            "external_id": external_id,
            "size": size,
            "color": color,
            "condition": condition,
            "availability": availability,
        }
        
        products.append(product)
        return products
    
    async def _normalize_stockx(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize StockX data."""
        products = []
        
        name = raw_data.get("name", "")
        brand = raw_data.get("brand", "")
        price_str = raw_data.get("price", "0")
        currency = self._extract_currency(price_str)
        price = self._extract_price(price_str)
        
        description = raw_data.get("description", "")
        image_url = raw_data.get("image_url", "")
        source_url = raw_data.get("url", "")
        external_id = raw_data.get("id", "")
        size = raw_data.get("size")
        color = raw_data.get("color")
        condition = raw_data.get("condition", "new")
        availability = raw_data.get("availability", True)
        
        product = {
            "name": name,
            "brand": brand,
            "price": price,
            "currency": currency,
            "description": description,
            "image_url": image_url,
            "source_url": source_url,
            "source": "stockx",
            "external_id": external_id,
            "size": size,
            "color": color,
            "condition": condition,
            "availability": availability,
        }
        
        products.append(product)
        return products
    
    def _extract_currency(self, price_str: str) -> str:
        """Extract currency from price string."""
        if not price_str:
            return "USD"
        
        # Check for currency symbols
        for symbol, currency in self.currency_map.items():
            if symbol in price_str:
                return currency
        
        # Default to USD
        return "USD"
    
    def _extract_price(self, price_str: str) -> Decimal:
        """Extract numeric price from price string."""
        if not price_str:
            return Decimal("0")
        
        # Remove currency symbols and non-numeric characters except decimal point
        cleaned = re.sub(r'[^\d.,]', '', price_str)
        
        # Handle different decimal separators
        if ',' in cleaned and '.' in cleaned:
            # Both present, assume comma is thousands separator
            cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Only comma, could be decimal separator
            cleaned = cleaned.replace(',', '.')
        
        try:
            return Decimal(cleaned)
        except:
            return Decimal("0")
