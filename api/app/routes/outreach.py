from fastapi import APIRouter, HTTPException, status, Depends

from ..db import get_supabase_client, insert_row, update_row, upsert_row, fetch_rows
from ..schemas.outreach import OutreachCreate, OutreachResponse, OutreachUpdate
from ..auth import get_current_user_id

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.get("/{page_id}", response_model=OutreachResponse)
def get_outreach(page_id: str, user_id: str = Depends(get_current_user_id)):
    """Get outreach tracking for a page (only if page belongs to user)."""
    # First verify the page belongs to the user
    page = fetch_rows("pages", {"id": page_id}, user_id=user_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    client = get_supabase_client()
    response = client.table("outreach_tracking").select("*").eq("page_id", page_id).eq("user_id", user_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Outreach tracking not found")
    
    return response.data[0]


@router.post("/", response_model=OutreachResponse, status_code=status.HTTP_201_CREATED)
def create_outreach(payload: OutreachCreate, user_id: str = Depends(get_current_user_id)):
    """Create outreach tracking for a page."""
    # Verify page belongs to user
    page = fetch_rows("pages", {"id": payload.page_id}, user_id=user_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    data = payload.model_dump()
    row = insert_row("outreach_tracking", data, user_id=user_id)
    return row


@router.put("/{page_id}", response_model=OutreachResponse)
def update_outreach(page_id: str, payload: OutreachUpdate, user_id: str = Depends(get_current_user_id)):
    """Update outreach tracking for a page."""
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return get_outreach(page_id, user_id)
    
    # Find existing outreach record (filtered by user_id)
    existing = fetch_rows("outreach_tracking", {"page_id": page_id}, user_id=user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Outreach tracking not found")
    
    # Use update instead of upsert to only modify specified fields
    row = update_row("outreach_tracking", existing[0]["id"], data, user_id=user_id)
    return row


