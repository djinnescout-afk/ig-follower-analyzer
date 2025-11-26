from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Query, status

from ..db import fetch_rows, get_supabase_client, insert_row, update_row, upsert_row
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
    search: Optional[str] = Query(None, description="Search by username or name"),
    sort_by: Optional[str] = Query("client_count", description="Field to sort by (client_count, follower_count, last_reviewed_at)"),
    order: Optional[str] = Query("desc", description="Sort order (asc or desc)"),
    limit: Optional[int] = Query(10000, description="Max pages to return"),
    offset: Optional[int] = Query(0, description="Pagination offset"),
    include_archived: Optional[bool] = Query(False, description="Include archived pages"),
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
            query = query.filter("category", "not.is", "null")
        else:
            query = query.filter("category", "is", "null")
    
    # Apply specific category filter
    if category is not None:
        query = query.eq("category", category)
    
    # Apply search filter
    if search is not None and search.strip():
        query = query.or_(f"ig_username.ilike.%{search}%,full_name.ilike.%{search}%")
    
    # Filter archived pages
    if not include_archived:
        # Only filter if archived column exists, otherwise skip
        try:
            query = query.eq("archived", False)
        except Exception:
            pass  # archived column might not exist yet
    
    # Apply sorting
    desc_order = order.lower() == "desc"
    query = query.order(sort_by, desc=desc_order)
    
    # If limit > 1000, we need to batch fetch (Supabase limit is 1000 per query)
    if limit > 1000:
        all_pages = []
        batch_size = 1000
        current_offset = offset
        remaining = limit
        
        logger.info(f"[PAGES API] Large request (limit={limit}), using batch fetching")
        
        while remaining > 0:
            batch_limit = min(batch_size, remaining)
            end = current_offset + batch_limit - 1
            
            try:
                response = query.range(current_offset, end).execute()
                batch = response.data if response.data else []
                all_pages.extend(batch)
                
                if len(batch) < batch_limit:
                    break  # No more data
                
                current_offset += batch_limit
                remaining -= batch_limit
            except Exception as e:
                logger.error(f"[PAGES API] Error in batch fetch: {e}", exc_info=True)
                break
        
        logger.info(f"[PAGES API] Returning {len(all_pages)} pages (batched)")
        return all_pages
    else:
        # Single request for small limits
        end = offset + limit - 1
        logger.info(f"[PAGES API] Fetching range({offset}, {end}) for category={category}, categorized={categorized}")
        
        try:
            response = query.range(offset, end).execute()
            result = response.data if response.data else []
            logger.info(f"[PAGES API] Returning {len(result)} pages")
            return result
        except Exception as e:
            logger.error(f"[PAGES API] Error fetching pages: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error fetching pages: {str(e)}")


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
    # Use update instead of upsert to only modify specified fields
    row = update_row("pages", page_id, data)
    return row


@router.get("/{page_id}/followers")
def get_page_followers(page_id: str):
    """Get list of clients that follow this page."""
    try:
        client = get_supabase_client()
        
        # Get client_following records for this page
        cf_response = client.table("client_following").select("client_id").eq("page_id", page_id).execute()
        
        if not cf_response.data:
            return []
        
        # Get client details for each client_id
        clients = []
        for cf in cf_response.data:
            client_id = cf["client_id"]
            client_response = client.table("clients").select("id, ig_username, full_name").eq("id", client_id).execute()
            
            if client_response.data:
                clients.append(client_response.data[0])
        
        return clients
    except Exception as e:
        logging.error(f"Error fetching followers for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

