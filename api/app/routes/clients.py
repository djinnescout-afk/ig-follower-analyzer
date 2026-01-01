from fastapi import APIRouter, HTTPException, status, Depends

from ..db import fetch_rows, insert_row, upsert_row, update_row
from ..schemas.client import ClientCreate, ClientResponse, ClientUpdate
from ..auth import get_current_user_id

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=list[ClientResponse])
def list_clients(user_id: str = Depends(get_current_user_id)):
    """List all clients for the current user."""
    rows = fetch_rows("clients", user_id=user_id)
    return rows


@router.post(
    "/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED
)
def create_client(payload: ClientCreate, user_id: str = Depends(get_current_user_id)):
    """Create a new client for the current user."""
    # ensure username lowercase
    data = payload.model_dump()
    data["ig_username"] = data["ig_username"].lower()
    # Check if client exists for this user
    existing = fetch_rows("clients", {"ig_username": data["ig_username"]}, user_id=user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client already exists",
        )
    row = insert_row("clients", data, user_id=user_id)
    return row


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: str, payload: ClientUpdate, user_id: str = Depends(get_current_user_id)):
    """Update a client. Only updates if the client belongs to the current user."""
    data = payload.model_dump(exclude_unset=True)
    if not data:
        row = fetch_rows("clients", {"id": client_id}, user_id=user_id)
        if not row:
            raise HTTPException(status_code=404, detail="Client not found")
        return row[0]
    # Use update_row which ensures user_id matches
    row = update_row("clients", client_id, data, user_id=user_id)
    return row

