from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OutreachBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    status: str
    date_contacted: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None


class OutreachCreate(OutreachBase):
    page_id: str


class OutreachUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    status: Optional[str] = None
    date_contacted: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None


class OutreachResponse(OutreachBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    page_id: str
    created_at: datetime
    updated_at: datetime


