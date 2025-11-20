from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ..db import fetch_rows, get_supabase_client, insert_row, upsert_row
from ..schemas.page import PageCreate, PageResponse, PageUpdate

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("/", response_model=list[PageResponse])
def list_pages(
    min_client_count: Optional[int] = Query(None, description="Filter by minimum client count"),
    limit: Optional[int] = Query(10000, description="Max pages to return"),
    offset: Optional[int] = Query(0, description="Pagination offset"),
):
    """List pages with optional filtering.
    
    Note: Manually calculates client_count from relationships due to PostgREST schema cache issues.
    """
    client = get_supabase_client()
    
    # Fetch all pages (we'll filter and paginate after counting)
    # Note: Supabase has a default limit of 1000, need to fetch in batches
    all_pages = []
    batch_size = 1000
    offset_fetch = 0
    
    while True:
        batch = client.table("pages").select("*").limit(batch_size).offset(offset_fetch).execute()
        if not batch.data:
            break
        all_pages.extend(batch.data)
        if len(batch.data) < batch_size:
            break  # Last batch
        offset_fetch += batch_size
    
    # Get client counts from relationships
    following_response = client.table("client_following").select("page_id").execute()
    following_data = following_response.data or []
    
    from collections import Counter
    page_client_counts = Counter(f["page_id"] for f in following_data)
    
    # Add client_count to each page
    for page in all_pages:
        page["client_count"] = page_client_counts.get(page["id"], 0)
    
    # Filter by min_client_count
    if min_client_count is not None:
        all_pages = [p for p in all_pages if p["client_count"] >= min_client_count]
    
    # Sort by client_count desc
    all_pages.sort(key=lambda p: p["client_count"], reverse=True)
    
    # Apply pagination
    return all_pages[offset:offset+limit]


@router.post("/", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
def create_page(payload: PageCreate):
    data = payload.model_dump()
    data["ig_username"] = data["ig_username"].lower()
    existing = fetch_rows("pages", {"ig_username": data["ig_username"]})
    if existing:
        raise HTTPException(status_code=409, detail="Page already exists")
    row = insert_row("pages", data)
    return row


@router.get("/{page_id}/profile")
def get_page_profile(page_id: str):
    """Get the most recent profile data for a page."""
    client = get_supabase_client()
    
    # Get the most recent profile scrape for this page
    response = (
        client.table("page_profiles")
        .select("*")
        .eq("page_id", page_id)
        .order("scraped_at", desc=True)
        .limit(1)
        .execute()
    )
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Profile not found. Page hasn't been scraped yet.")
    
    return response.data[0]


@router.put("/{page_id}", response_model=PageResponse)
def update_page(page_id: str, payload: PageUpdate):
    data = payload.model_dump(exclude_unset=True)
    if not data:
        row = fetch_rows("pages", {"id": page_id})
        if not row:
            raise HTTPException(status_code=404, detail="Page not found")
        return row[0]
    data["id"] = page_id
    row = upsert_row("pages", data, on_conflict="id")
    return row

