from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScraperDataBase(BaseModel):
    source: str = Field(..., max_length=50)
    external_id: str = Field(..., max_length=100)
    raw_data: Dict[str, Any] = Field(..., description="Raw scraped data")
    status: str = Field(default="pending", max_length=20)  # pending, processing, completed, failed
    error_message: Optional[str] = Field(None, max_length=1000)


class ScraperDataCreate(ScraperDataBase):
    pass


class ScraperDataUpdate(BaseModel):
    raw_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, max_length=20)
    error_message: Optional[str] = Field(None, max_length=1000)


class ScraperData(ScraperDataBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
