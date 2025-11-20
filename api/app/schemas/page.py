from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class PageBase(BaseModel):
    ig_username: str = Field(..., description="Instagram handle")
    display_name: Optional[str] = None
    category: Optional[str] = None
    promo_status: Optional[str] = None
    pricing_notes: Optional[str] = None
    metadata: Optional[dict] = None


class PageCreate(PageBase):
    follower_count: Optional[int] = None


class PageUpdate(BaseModel):
    display_name: Optional[str] = None
    category: Optional[str] = None
    category_confidence: Optional[float] = None
    promo_status: Optional[str] = None
    promo_indicators: Optional[List[str]] = None
    contact_email: Optional[str] = None
    pricing_notes: Optional[str] = None
    metadata: Optional[dict] = None


class PageResponse(PageBase):
    id: str
    follower_count: Optional[int] = None
    clients_following_count: int = 0
    last_profile_scraped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

