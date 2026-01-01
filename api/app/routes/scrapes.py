from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..db import fetch_rows, insert_row
from ..auth import get_current_user_id

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
def trigger_client_following(request: ClientFollowingRequest, user_id: str = Depends(get_current_user_id)):
    """Queue scrape jobs for client following lists"""
    job_ids = []
    for client_id in request.client_ids:
        # Verify client belongs to user
        clients = fetch_rows("clients", {"id": client_id}, user_id=user_id)
        if not clients:
            continue  # Skip clients that don't belong to user
        # Insert scrape job into database
        job = insert_row("scrape_runs", {
            "scrape_type": "client_following",
            "status": "pending",
            "client_id": client_id
        }, user_id=user_id)
        job_ids.append(job["id"])
    
    return {"message": f"Queued {len(job_ids)} scrape jobs", "job_ids": job_ids}


@router.post("/profile-scrape", response_model=dict)
def trigger_profile_scrape(request: ProfileScrapeRequest, user_id: str = Depends(get_current_user_id)):
    """Queue scrape jobs for profile data"""
    job_ids = []
    for page_id in request.page_ids:
        # Verify page belongs to user
        pages = fetch_rows("pages", {"id": page_id}, user_id=user_id)
        if not pages:
            continue  # Skip pages that don't belong to user
        # Insert scrape job into database
        job = insert_row("scrape_runs", {
            "scrape_type": "profile_scrape",
            "status": "pending",
            "page_ids": [page_id]
        }, user_id=user_id)
        job_ids.append(job["id"])
    
    return {"message": f"Queued {len(job_ids)} scrape jobs", "job_ids": job_ids}


@router.get("/", response_model=List[ScrapeRunResponse])
def list_scrapes(limit: int = 50, offset: int = 0, user_id: str = Depends(get_current_user_id)):
    """List recent scrape jobs for the current user"""
    rows = fetch_rows("scrape_runs", user_id=user_id)
    # Sort by created_at descending and apply limit/offset
    sorted_rows = sorted(rows, key=lambda x: x.get("created_at", ""), reverse=True)
    return sorted_rows[offset:offset + limit]


@router.get("/{run_id}", response_model=ScrapeRunResponse)
def get_scrape(run_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a specific scrape job by ID (only if it belongs to user)"""
    rows = fetch_rows("scrape_runs", {"id": run_id}, user_id=user_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Scrape run not found")
    return rows[0]

