from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import fetch_rows, insert_row

router = APIRouter(prefix="/scrapes", tags=["scrapes"])


# Request schemas
class ClientFollowingRequest(BaseModel):
    client_ids: List[str]


class ProfileScrapeRequest(BaseModel):
    page_ids: List[str]


# Response schemas  
class ScrapeRunResponse(BaseModel):
    id: str
    scrape_type: str
    status: str
    client_id: str | None = None
    created_at: str


@router.post("/client-following", response_model=dict)
def trigger_client_following(request: ClientFollowingRequest):
    """Queue scrape jobs for client following lists"""
    job_ids = []
    for client_id in request.client_ids:
        # Insert scrape job into database
        job = insert_row("scrape_runs", {
            "scrape_type": "client_following",
            "status": "pending",
            "client_id": client_id
        })
        job_ids.append(job["id"])
    
    return {"message": f"Queued {len(job_ids)} scrape jobs", "job_ids": job_ids}


@router.post("/profile-scrape", response_model=dict)
def trigger_profile_scrape(request: ProfileScrapeRequest):
    """Queue scrape jobs for profile data"""
    job_ids = []
    for page_id in request.page_ids:
        # Insert scrape job into database
        job = insert_row("scrape_runs", {
            "scrape_type": "profile_scrape",
            "status": "pending",
            "page_ids": [page_id]
        })
        job_ids.append(job["id"])
    
    return {"message": f"Queued {len(job_ids)} scrape jobs", "job_ids": job_ids}


@router.get("/", response_model=List[ScrapeRunResponse])
def list_scrapes(limit: int = 50, offset: int = 0):
    """List recent scrape jobs"""
    rows = fetch_rows("scrape_runs")
    # Sort by created_at descending and apply limit/offset
    sorted_rows = sorted(rows, key=lambda x: x.get("created_at", ""), reverse=True)
    return sorted_rows[offset:offset + limit]


@router.get("/{run_id}", response_model=ScrapeRunResponse)
def get_scrape(run_id: str):
    """Get a specific scrape job by ID"""
    rows = fetch_rows("scrape_runs", {"id": run_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Scrape run not found")
    return rows[0]

