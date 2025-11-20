from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ClientBase(BaseModel):
    name: str = Field(..., description="Client name")
    ig_username: str = Field(..., description="Instagram handle in lowercase")


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    ig_username: Optional[str] = None
    following_count: Optional[int] = None
    last_scraped: Optional[datetime] = None


class ClientResponse(ClientBase):
    id: str
    following_count: int = 0
    last_scraped: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

