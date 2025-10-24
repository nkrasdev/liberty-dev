from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    brand: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    description: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=1000)
    source_url: str = Field(..., max_length=1000)
    source: str = Field(..., max_length=50)  # farfetch, goat, stockx
    external_id: str = Field(..., max_length=100)
    size: Optional[str] = Field(None, max_length=20)
    color: Optional[str] = Field(None, max_length=50)
    condition: Optional[str] = Field(None, max_length=20)
    availability: bool = Field(default=True)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    description: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=1000)
    source_url: Optional[str] = Field(None, max_length=1000)
    size: Optional[str] = Field(None, max_length=20)
    color: Optional[str] = Field(None, max_length=50)
    condition: Optional[str] = Field(None, max_length=20)
    availability: Optional[bool] = None


class Product(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
