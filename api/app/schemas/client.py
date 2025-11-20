from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ClientBase(BaseModel):
    ig_username: str = Field(..., description="Instagram handle in lowercase")
    display_name: Optional[str] = None
    status: str = Field(default="pending")
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    display_name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    last_error: Optional[str] = None


class ClientResponse(ClientBase):
    id: str
    following_count: int = 0
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

