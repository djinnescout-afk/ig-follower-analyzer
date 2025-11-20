from fastapi import APIRouter, HTTPException, status

from ..db import get_supabase_client, insert_row, upsert_row, fetch_rows
from ..schemas.outreach import OutreachCreate, OutreachResponse, OutreachUpdate

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.get("/{page_id}", response_model=OutreachResponse)
def get_outreach(page_id: str):
    """Get outreach tracking for a page."""
    client = get_supabase_client()
    response = client.table("outreach_tracking").select("*").eq("page_id", page_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Outreach tracking not found")
    
    return response.data[0]


@router.post("/", response_model=OutreachResponse, status_code=status.HTTP_201_CREATED)
def create_outreach(payload: OutreachCreate):
    """Create outreach tracking for a page."""
    data = payload.model_dump()
    row = insert_row("outreach_tracking", data)
    return row


@router.put("/{page_id}", response_model=OutreachResponse)
def update_outreach(page_id: str, payload: OutreachUpdate):
    """Update outreach tracking for a page."""
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return get_outreach(page_id)
    
    # Find existing outreach record
    existing = fetch_rows("outreach_tracking", {"page_id": page_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Outreach tracking not found")
    
    data["id"] = existing[0]["id"]
    row = upsert_row("outreach_tracking", data, on_conflict="id")
    return row

