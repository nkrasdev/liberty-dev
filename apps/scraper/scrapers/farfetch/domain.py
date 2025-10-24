from pydantic import ConfigDict, Field

from apps.scraper.scraper_core.models import BaseProduct, BaseVariant


class ProductVariant(BaseVariant):
    """Вариант товара Farfetch (размер, цвет и т.д.)."""

    size: str = Field(default="", description="Размер")
    image: str = Field(default="", description="URL изображения варианта")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sku": "PROD-001-42",
                "name": "Nike Air Force 1 | 42",
                "size": "42",
                "image": "https://example.com/variant.jpg",
                "offers": {
                    "url": "https://example.com/offer",
                    "availability": "InStock",
                    "price_specification": [{"price": 100.0, "priceCurrency": "USD"}],
                },
            }
        }
    )


class FarfetchProduct(BaseProduct):
    """Модель товара Farfetch."""

    color: str = Field(default="", description="Цвет")
    product_group_id: str = Field(default="", description="ID группы товаров")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Nike Air Force 1",
                "brand": "Nike",
                "color": "белый",
                "description": "Классические кроссовки",
                "product_group_id": "12345",
                "url": "https://example.com/product",
                "images": [],
                "variants": [],
            }
        }
    )
