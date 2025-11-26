from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Query, status

from ..db import fetch_rows, get_supabase_client, insert_row, upsert_row
from ..schemas.page import PageCreate, PageResponse, PageUpdate

router = APIRouter(prefix="/pages", tags=["pages"])
logger = logging.getLogger(__name__)


@router.get("/category-counts")
def get_category_counts():
    """Get count of pages per category using efficient SQL aggregation."""
    try:
        client = get_supabase_client()
        response = client.rpc("get_category_counts").execute()
        
        if not response.data:
            return {}
        
        # Convert list of {category, count} to dict
        counts = {item["category"]: item["count"] for item in response.data}
        return counts
    except Exception as e:
        logger.error(f"Error in get_category_counts: {e}", exc_info=True)
        return {}


@router.get("/count")
def get_pages_count(
    min_client_count: Optional[int] = Query(None),
    categorized: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """Get total count of pages matching filters (for pagination)."""
    try:
        client = get_supabase_client()
        query = client.table("pages").select("id", count="exact")
        
        if min_client_count is not None:
            query = query.gte("client_count", min_client_count)
        
        if categorized is not None:
            if categorized:
                query = query.filter("category", "not.is", "null")
            else:
                query = query.filter("category", "is", "null")
        
        if category is not None:
            query = query.eq("category", category)
        
        if search is not None and search.strip():
            query = query.or_(f"ig_username.ilike.%{search}%,full_name.ilike.%{search}%")
        
        response = query.execute()
        return {"count": response.count}
    except Exception as e:
        logger.error(f"Error in get_pages_count: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[PageResponse])
def list_pages(
    min_client_count: Optional[int] = Query(None, description="Filter by minimum client count"),
    categorized: Optional[bool] = Query(None, description="Filter by categorization status (true=categorized, false=uncategorized)"),
    category: Optional[str] = Query(None, description="Filter by specific category"),
    sort_by: Optional[str] = Query("client_count", description="Field to sort by (client_count, follower_count, last_reviewed_at)"),
    order: Optional[str] = Query("desc", description="Sort order (asc or desc)"),
    limit: Optional[int] = Query(10000, description="Max pages to return"),
    offset: Optional[int] = Query(0, description="Pagination offset"),
):
    """List pages with optional filtering, sorting, and pagination.
    
    Uses the client_count column from the database (maintained by triggers).
    """
    client = get_supabase_client()
    
    # Build query with filter applied at database level
    query = client.table("pages").select("*")
    
    # Apply min_client_count filter
    if min_client_count is not None:
        query = query.gte("client_count", min_client_count)
    
    # Apply categorization filter
    if categorized is not None:
        if categorized:
            query = query.is_not("category", "null")
        else:
            query = query.is_("category", "null")
    
    # Apply specific category filter
    if category is not None:
        query = query.eq("category", category)
    
    # Apply sorting
    desc_order = order.lower() == "desc"
    query = query.order(sort_by, desc=desc_order)
    
    # Fetch pages in batches (Supabase limit is 1000 per query)
    all_pages = []
    batch_size = 1000
    start = 0
    iteration = 0
    
    print(f"[PAGES API] Starting batch fetch of pages (min_client_count={min_client_count})...")
    
    while True:
        iteration += 1
        end = start + batch_size - 1
        print(f"[PAGES API] Batch {iteration}: Fetching range({start}, {end})")
        
        try:
            batch = query.range(start, end).execute()
            batch_count = len(batch.data) if batch.data else 0
            print(f"[PAGES API] Batch {iteration}: Retrieved {batch_count} items")
            
            if not batch.data:
                print(f"[PAGES API] Batch {iteration}: No data, breaking")
                break
                
            all_pages.extend(batch.data)
            print(f"[PAGES API] Total pages so far: {len(all_pages)}")
            
            if len(batch.data) < batch_size:
                print(f"[PAGES API] Batch {iteration}: Last batch (partial), breaking")
                break  # Last batch
                
            start += batch_size
        except Exception as e:
            print(f"[PAGES API] Batch {iteration}: ERROR - {str(e)}")
            break
    
    print(f"[PAGES API] Finished fetching. Total pages: {len(all_pages)}")
    
    # Apply pagination
    result = all_pages[offset:offset+limit]
    print(f"[PAGES API] Returning slice [offset={offset}:offset+limit={offset+limit}]: {len(result)} pages")
    return result


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

