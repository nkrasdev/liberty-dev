from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Boolean, Text, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import func

from apps.api.common.db import Base


class Product(Base):
    """Product model."""
    
    __tablename__ = "products"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(500), nullable=False)
    brand = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    description = Column(Text)
    image_url = Column(String(1000))
    source_url = Column(String(1000), nullable=False)
    source = Column(String(50), nullable=False)  # farfetch, goat, stockx
    external_id = Column(String(100), nullable=False)
    size = Column(String(20))
    color = Column(String(50))
    condition = Column(String(20))
    availability = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Indexes for better performance
    __table_args__ = (
        Index("idx_products_source_external_id", "source", "external_id"),
        Index("idx_products_brand", "brand"),
        Index("idx_products_source", "source"),
        Index("idx_products_created_at", "created_at"),
        Index("idx_products_price", "price"),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', source='{self.source}')>"
