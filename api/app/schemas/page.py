from datetime import datetime
from typing import Optional

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


class PageResponse(PageBase):
    id: str
    client_count: int = 0
    last_scraped: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

