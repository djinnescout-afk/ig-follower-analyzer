from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    job_type: str = Field(..., description="client_following or profile_scrape")
    target_username: str
    client_id: Optional[str] = None
    force: bool = False


class ScrapeRunResponse(BaseModel):
    id: str
    job_type: str
    target_username: str
    status: str
    coverage_pct: Optional[float] = None
    total_expected: Optional[int] = None
    total_retrieved: Optional[int] = None
    failed_accounts: Optional[List[str]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        orm_mode = True

