from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScraperEventBase(BaseModel):
    scraper_data_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ScraperDataReceived(ScraperEventBase):
    event_type: str = Field(default="scraper.data.received")
    source: str
    external_id: str
    data_size: int = Field(..., description="Size of raw data in bytes")


class ScraperDataProcessed(ScraperEventBase):
    event_type: str = Field(default="scraper.data.processed")
    source: str
    external_id: str
    status: str  # completed, failed
    error_message: Optional[str] = None
    products_created: int = Field(default=0, description="Number of products created")
    products_updated: int = Field(default=0, description="Number of products updated")
