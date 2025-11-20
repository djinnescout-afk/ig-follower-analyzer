from fastapi import APIRouter, HTTPException

from ..db import fetch_rows
from ..schemas.scrape import ScrapeRequest, ScrapeRunResponse
from ..services.scrape_runs import enqueue_scrape_run

router = APIRouter(prefix="/scrapes", tags=["scrapes"])


@router.post("/", response_model=ScrapeRunResponse)
def enqueue_scrape(request: ScrapeRequest):
    if request.job_type not in {"client_following", "profile_scrape"}:
        raise HTTPException(status_code=400, detail="Invalid job_type")
    run = enqueue_scrape_run(
        job_type=request.job_type,
        target_username=request.target_username,
        client_id=request.client_id,
        metadata={"force": request.force},
    )
    return run


@router.get("/{run_id}", response_model=ScrapeRunResponse)
def get_scrape(run_id: str):
    rows = fetch_rows("scrape_runs", {"id": run_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Scrape run not found")
    return rows[0]

