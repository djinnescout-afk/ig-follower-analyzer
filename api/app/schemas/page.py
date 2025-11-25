from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class PageBase(BaseModel):
    ig_username: str = Field(..., description="Instagram handle")
    full_name: Optional[str] = None
    follower_count: int = 0
    is_verified: bool = False
    is_private: bool = False


class PageCreate(PageBase):
    pass


class PageUpdate(BaseModel):
    ig_username: Optional[str] = None
    full_name: Optional[str] = None
    follower_count: Optional[int] = None
    is_verified: Optional[bool] = None
    is_private: Optional[bool] = None
    last_scraped: Optional[datetime] = None
    # VA Categorization fields
    category: Optional[str] = None
    known_contact_methods: Optional[List[str]] = None
    successful_contact_method: Optional[str] = None
    current_main_contact_method: Optional[str] = None
    ig_account_for_dm: Optional[str] = None
    promo_price: Optional[float] = None
    website_url: Optional[str] = None
    va_notes: Optional[str] = None
    last_reviewed_by: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None


class PageResponse(PageBase):
    id: str
    client_count: int = 0
    last_scraped: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # VA Categorization fields
    category: Optional[str] = None
    known_contact_methods: Optional[List[str]] = None
    successful_contact_method: Optional[str] = None
    current_main_contact_method: Optional[str] = None
    ig_account_for_dm: Optional[str] = None
    promo_price: Optional[float] = None
    website_url: Optional[str] = None
    va_notes: Optional[str] = None
    last_reviewed_by: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

