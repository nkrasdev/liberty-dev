from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductEventBase(BaseModel):
    product_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProductCreated(ProductEventBase):
    event_type: str = Field(default="product.created")
    name: str
    brand: str
    source: str
    external_id: str


class ProductUpdated(ProductEventBase):
    event_type: str = Field(default="product.updated")
    changes: dict = Field(..., description="Fields that were updated")


class ProductDeleted(ProductEventBase):
    event_type: str = Field(default="product.deleted")
    name: str
    brand: str
    source: str
