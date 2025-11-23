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
        
        # Use PostgreSQL aggregation for efficient counting
        response = client.rpc("get_category_counts").execute()
        
        if not response.data:
            return {}
        
        # Convert list of {category, count} to dict
        counts = {item["category"]: item["count"] for item in response.data}
        return counts
    except Exception as e:
        logger.error(f"Error in get_category_counts: {e}", exc_info=True)
        # Fallback: return empty dict
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
        
        if search is not None:
            search_pattern = f"%{search}%"
            query = query.or_(f"ig_username.ilike.{search_pattern},full_name.ilike.{search_pattern}")
        
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
    search: Optional[str] = Query(None, description="Search by username or full name (case-insensitive partial match)"),
    sort_by: Optional[str] = Query("client_count", description="Field to sort by (client_count, follower_count, last_reviewed_at)"),
    order: Optional[str] = Query("desc", description="Sort order (asc or desc)"),
    limit: Optional[int] = Query(100, description="Max pages to return (default 100)"),
    offset: Optional[int] = Query(0, description="Pagination offset"),
):
    """List pages with optional filtering, sorting, and pagination.
    
    Efficient server-side pagination with database-level sorting.
    """
    try:
        logger.info(f"[PAGES API] Request: min_client_count={min_client_count}, categorized={categorized}, category={category}, sort_by={sort_by}, order={order}, limit={limit}, offset={offset}")
        
        client = get_supabase_client()
        
        # Build query with filter applied at database level
        query = client.table("pages").select("*")
        
        # Apply min_client_count filter
        if min_client_count is not None:
            query = query.gte("client_count", min_client_count)
        
        # Apply categorization filter
        if categorized is not None:
            if categorized:
                query = query.filter("category", "not.is", "null")
            else:
                query = query.filter("category", "is", "null")
        
        # Apply specific category filter
        if category is not None:
            query = query.eq("category", category)
        
        # Apply search filter (username or full_name)
        if search is not None:
            # Use PostgREST's ilike for case-insensitive pattern matching
            search_pattern = f"%{search}%"
            # Search in both username and full_name using OR logic
            query = query.or_(f"ig_username.ilike.{search_pattern},full_name.ilike.{search_pattern}")
        
        # Apply sorting
        desc_order = order.lower() == "desc"
        query = query.order(sort_by, desc=desc_order)
        
        # Apply pagination using range (Supabase uses 0-based indexing)
        end = offset + limit - 1
        response = query.range(offset, end).execute()
        
        result = response.data if response.data else []
        logger.info(f"[PAGES API] Returning {len(result)} pages (offset={offset}, limit={limit})")
        
        return result
    except Exception as e:
        logger.error(f"Error in list_pages: {e}", exc_info=True)
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

