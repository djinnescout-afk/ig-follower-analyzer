from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Query, status

from ..db import fetch_rows, get_supabase_client, insert_row, upsert_row
from ..schemas.page import PageCreate, PageResponse, PageUpdate

router = APIRouter(prefix="/pages", tags=["pages"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[PageResponse])
def list_pages(
    min_client_count: Optional[int] = Query(None, description="Filter by minimum client count"),
    categorized: Optional[bool] = Query(None, description="Filter by categorization status (true=categorized, false=uncategorized)"),
    category: Optional[str] = Query(None, description="Filter by specific category"),
    limit: Optional[int] = Query(10000, description="Max pages to return"),
    offset: Optional[int] = Query(0, description="Pagination offset"),
):
    """List pages with optional filtering.
    
    Uses the client_count column from the database (maintained by triggers).
    """
    try:
        print(f"[PAGES API] Request: min_client_count={min_client_count}, categorized={categorized}, category={category}")
        
        client = get_supabase_client()
        
        # Build query with filter applied at database level
        query = client.table("pages").select("*")
        
        # Apply min_client_count filter
        if min_client_count is not None:
            query = query.gte("client_count", min_client_count)
        
        # Apply categorization filter
        if categorized is not None:
            if categorized:
                # Filter for pages with a category (not null)
                # PostgREST syntax: "not.is" for IS NOT NULL
                query = query.filter("category", "not.is", "null")
            else:
                # Filter for pages without a category (is null)
                query = query.filter("category", "is", "null")
        
        # Apply specific category filter
        if category is not None:
            query = query.eq("category", category)
        
        # Sort by client_count descending
        query = query.order("client_count", desc=True)
        
        # Fetch pages in batches (Supabase limit is 1000 per query)
        all_pages = []
        batch_size = 1000
        start = 0
        iteration = 0
        
        print(f"[PAGES API] Starting batch fetch of pages...")
        
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
            except Exception as batch_error:
                print(f"[PAGES API] Batch {iteration}: ERROR - {str(batch_error)}")
                logger.error(f"Batch fetch error: {batch_error}", exc_info=True)
                break
        
        print(f"[PAGES API] Finished fetching. Total pages: {len(all_pages)}")
        
        # Apply pagination
        result = all_pages[offset:offset+limit]
        print(f"[PAGES API] Returning {len(result)} pages")
        return result
    except Exception as e:
        logger.error(f"Error in list_pages: {e}", exc_info=True)
        print(f"[PAGES API] FATAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
    
    # Use direct update instead of upsert to avoid null constraint issues
    from ..db import get_supabase_client, serialize_for_db
    client = get_supabase_client()
    serialized_data = serialize_for_db(data)
    response = client.table("pages").update(serialized_data).eq("id", page_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return response.data[0]

