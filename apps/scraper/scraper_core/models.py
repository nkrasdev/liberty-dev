"""Базовые модели для всех скраперов."""

from typing import List, Tuple

from pydantic import BaseModel, ConfigDict, Field, computed_field


class BaseImage(BaseModel):
    """Базовая модель изображения."""

    content_url: str = Field(..., description="URL изображения")
    description: str = Field(default="", description="Описание изображения")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content_url": "https://example.com/image.jpg",
                "description": "Основное изображение товара",
            }
        }
    )


class BaseOffer(BaseModel):
    """Базовая модель предложения."""

    url: str = Field(..., description="URL предложения")
    availability: str = Field(default="InStock", description="Доступность")
    price_specification: List[dict] = Field(default_factory=list, description="Спецификация цены")

    @computed_field
    @property
    def price(self) -> float | None:
        """Получить цену из спецификации."""
        if self.price_specification:
            return self.price_specification[0].get("price")
        return None

    @computed_field
    @property
    def currency(self) -> str | None:
        """Получить валюту из спецификации."""
        if self.price_specification:
            return self.price_specification[0].get("priceCurrency")
        return None


class BaseVariant(BaseModel):
    """Базовая модель варианта товара."""

    sku: str = Field(..., description="SKU товара")
    name: str = Field(..., description="Название варианта")
    offers: BaseOffer = Field(..., description="Предложение")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sku": "PROD-001-42",
                "name": "Product Variant | 42",
                "offers": {
                    "url": "https://example.com/offer",
                    "availability": "InStock",
                    "price_specification": [{"price": 100.0, "priceCurrency": "USD"}],
                },
            }
        }
    )


class BaseProduct(BaseModel):
    """Базовая модель товара."""

    name: str = Field(..., description="Название товара")
    brand: str = Field(..., description="Бренд")
    description: str = Field(default="", description="Описание")
    url: str = Field(..., description="URL товара")
    images: List[BaseImage] = Field(default_factory=list, description="Изображения")
    variants: List[BaseVariant] = Field(default_factory=list, description="Варианты")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Product Name",
                "brand": "Brand",
                "description": "Product description",
                "url": "https://example.com/product",
                "images": [],
                "variants": [],
            }
        }
    )

    @computed_field
    @property
    def price_range(self) -> Tuple[float | None, float | None]:
        """Получить диапазон цен."""
        prices = [v.offers.price for v in self.variants if v.offers.price]
        if not prices:
            return None, None
        return min(prices), max(prices)
