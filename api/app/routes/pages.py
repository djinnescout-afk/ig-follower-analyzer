from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Query, status, Depends

from ..db import fetch_rows, get_supabase_client, insert_row, update_row, upsert_row
from ..schemas.page import PageCreate, PageResponse, PageUpdate
from ..auth import get_current_user_id

router = APIRouter(prefix="/pages", tags=["pages"])
logger = logging.getLogger(__name__)


def _merge_outreach_data(pages: list[dict], user_id: str) -> list[dict]:
    """Merge outreach tracking data into page objects."""
    if not pages:
        return pages
    
    client = get_supabase_client()
    page_ids = [p["id"] for p in pages]
    
    try:
        # Fetch outreach data for all pages at once (filtered by user_id)
        outreach_response = client.table("outreach_tracking").select(
            "page_id, status, date_contacted, follow_up_date"
        ).in_("page_id", page_ids).eq("user_id", user_id).execute()
        
        # Create lookup map
        outreach_map = {ot["page_id"]: ot for ot in (outreach_response.data or [])}
        
        # Merge outreach data into pages
        for page in pages:
            outreach = outreach_map.get(page["id"])
            if outreach:
                page["outreach_status"] = outreach["status"]
                page["outreach_date_contacted"] = outreach.get("date_contacted")
                page["outreach_follow_up_date"] = outreach.get("follow_up_date")
            else:
                page["outreach_status"] = None
                page["outreach_date_contacted"] = None
                page["outreach_follow_up_date"] = None
        
    except Exception as e:
        logger.warning(f"[PAGES API] Error fetching outreach data: {e}", exc_info=True)
        # If outreach fetch fails, set all to None
        for page in pages:
            page["outreach_status"] = None
            page["outreach_date_contacted"] = None
            page["outreach_follow_up_date"] = None
    
    return pages


@router.get("/category-counts")
def get_category_counts(user_id: str = Depends(get_current_user_id)):
    """Get count of pages per category using efficient SQL aggregation (for current user)."""
    try:
        client = get_supabase_client()
        # Note: RPC function would need to be updated to accept user_id parameter
        # For now, we'll filter client-side or create a new RPC function
        # Temporary solution: Get all pages and count by category
        response = client.table("pages").select("category").eq("user_id", user_id).execute()
        
        if not response.data:
            return {}
        
        # Count by category
        counts = {}
        for page in response.data:
            category = page.get("category")
            if category:
                counts[category] = counts.get(category, 0) + 1
        
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
    user_id: str = Depends(get_current_user_id),
):
    """Get total count of pages matching filters (for pagination)."""
    try:
        client = get_supabase_client()
        query = client.table("pages").select("id", count="exact").eq("user_id", user_id)
        
        if min_client_count is not None:
            query = query.gte("client_count", min_client_count)
        
        if categorized is not None:
            if categorized:
                query = query.not_.is_("category", "null")
            else:
                query = query.is_("category", "null")
        
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
    user_id: str = Depends(get_current_user_id),
):
    """List pages with optional filtering, sorting, and pagination.
    
    Uses the client_count column from the database (maintained by triggers).
    Only returns pages belonging to the current user.
    """
    client = get_supabase_client()
    
    # Build query with filter applied at database level
    query = client.table("pages").select("*").eq("user_id", user_id)
    
    # Apply min_client_count filter
    if min_client_count is not None:
        query = query.gte("client_count", min_client_count)
    
    # Apply categorization filter
    if categorized is not None:
        if categorized:
            query = query.not_.is_("category", "null")
        else:
            query = query.is_("category", "null")
    
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
    
    # Apply sorting with secondary sort by id for stable pagination
    desc_order = order.lower() == "desc"
    query = query.order(sort_by, desc=desc_order)
    query = query.order("id", desc=False)  # Always ascending for consistent ordering
    
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
        # Merge outreach tracking data
        all_pages = _merge_outreach_data(all_pages, user_id)
        # Convert to PageResponse objects to ensure all fields are included
        return [PageResponse(**page) for page in all_pages]
    else:
        # Single request for small limits
        end = offset + limit - 1
        logger.info(f"[PAGES API] Fetching range({offset}, {end}) for category={category}, categorized={categorized}")
        
        try:
            response = query.range(offset, end).execute()
            result = response.data if response.data else []
            logger.info(f"[PAGES API] Returning {len(result)} pages")
            # Merge outreach tracking data
            result = _merge_outreach_data(result, user_id)
            # Convert to PageResponse objects to ensure all fields are included
            return [PageResponse(**page) for page in result]
        except Exception as e:
            logger.error(f"[PAGES API] Error fetching pages: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error fetching pages: {str(e)}")


@router.post("/", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
def create_page(payload: PageCreate, user_id: str = Depends(get_current_user_id)):
    data = payload.model_dump()
    data["ig_username"] = data["ig_username"].lower()
    # Check if page exists for this user
    existing = fetch_rows("pages", {"ig_username": data["ig_username"]}, user_id=user_id)
    if existing:
        raise HTTPException(status_code=409, detail="Page already exists")
    row = insert_row("pages", data, user_id=user_id)
    return row


@router.get("/{page_id}/profile")
def get_page_profile(page_id: str, user_id: str = Depends(get_current_user_id)):
    """Get the most recent profile data for a page (only if page belongs to user)."""
    client = get_supabase_client()
    
    # First verify the page belongs to the user
    page = fetch_rows("pages", {"id": page_id}, user_id=user_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get the most recent profile scrape for this page
    response = (
        client.table("page_profiles")
        .select("*")
        .eq("page_id", page_id)
        .eq("user_id", user_id)
        .order("scraped_at", desc=True)
        .limit(1)
        .execute()
    )
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Profile not found. Page hasn't been scraped yet.")
    
    return response.data[0]


@router.put("/{page_id}", response_model=PageResponse)
def update_page(page_id: str, payload: PageUpdate, user_id: str = Depends(get_current_user_id)):
    """Update a page. Only updates if the page belongs to the current user."""
    data = payload.model_dump(exclude_unset=True)
    if not data:
        row = fetch_rows("pages", {"id": page_id}, user_id=user_id)
        if not row:
            raise HTTPException(status_code=404, detail="Page not found")
        return row[0]
    # Use update instead of upsert to only modify specified fields
    # update_row ensures user_id matches
    row = update_row("pages", page_id, data, user_id=user_id)
    return row


@router.get("/{page_id}/followers")
def get_page_followers(page_id: str, user_id: str = Depends(get_current_user_id)):
    """Get list of clients that follow this page (only if page belongs to user)."""
    try:
        client = get_supabase_client()
        
        # First verify the page belongs to the user
        page = fetch_rows("pages", {"id": page_id}, user_id=user_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        # Get client_following records for this page (filtered by user_id)
        cf_response = client.table("client_following").select("client_id").eq("page_id", page_id).eq("user_id", user_id).execute()
        
        if not cf_response.data:
            return []
        
        # Get client details for each client_id (filtered by user_id)
        clients = []
        for cf in cf_response.data:
            client_id = cf["client_id"]
            client_response = client.table("clients").select("id, ig_username").eq("id", client_id).eq("user_id", user_id).execute()
            
            if client_response.data:
                clients.append(client_response.data[0])
        
        return clients
    except Exception as e:
        logging.error(f"Error fetching followers for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

