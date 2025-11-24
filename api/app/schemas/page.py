from datetime import datetime
from typing import Optional, List, Any

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
    model_config = ConfigDict(from_attributes=True)
    
    ig_username: Optional[str] = None
    full_name: Optional[str] = None
    follower_count: Optional[int] = None
    is_verified: Optional[bool] = None
    is_private: Optional[bool] = None
    last_scraped: Optional[datetime] = None
    last_scrape_status: Optional[str] = None
    last_scrape_error: Optional[str] = None
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
    # Contact detail fields
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    contact_telegram: Optional[str] = None
    contact_other: Optional[str] = None
    attempted_contact_methods: Optional[List[str]] = None
    # Promo tracking fields
    manual_promo_status: Optional[str] = None
    website_has_promo_page: Optional[bool] = None
    website_contact_email: Optional[str] = None
    website_has_contact_form: Optional[bool] = None
    website_last_scraped_at: Optional[datetime] = None
    # Archival fields
    archived: Optional[bool] = None
    archived_by: Optional[str] = None
    archive_reason: Optional[str] = None


class PageResponse(PageBase):
    id: str
    client_count: int = 0
    last_scraped: Optional[datetime] = None
    last_scrape_status: Optional[str] = None
    last_scrape_error: Optional[str] = None
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
    # Contact detail fields
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    contact_telegram: Optional[str] = None
    contact_other: Optional[str] = None
    attempted_contact_methods: Optional[List[str]] = None
    # Promo tracking fields
    manual_promo_status: Optional[str] = None
    website_has_promo_page: Optional[bool] = None
    website_contact_email: Optional[str] = None
    website_has_contact_form: Optional[bool] = None
    website_last_scraped_at: Optional[datetime] = None
    # Archival fields
    archived: bool = False
    archived_at: Optional[datetime] = None
    archived_by: Optional[str] = None
    archive_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PageProfile(BaseModel):
    """Profile data scraped from Instagram"""
    model_config = ConfigDict(from_attributes=True)
    
    page_id: str
    profile_pic_base64: Optional[str] = None
    profile_pic_mime_type: Optional[str] = None
    bio: Optional[str] = None
    posts: Optional[List[Any]] = None
    promo_status: Optional[str] = None  # Auto-detected: 'warm', 'unknown', 'not_open'
    promo_indicators: Optional[List[str]] = None  # Auto-detected keywords from bio
    contact_email: Optional[str] = None
    scraped_at: Optional[datetime] = None


class PageWithProfile(PageResponse):
    """Page with embedded profile data"""
    profile: Optional[PageProfile] = None

