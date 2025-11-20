from fastapi import APIRouter, HTTPException, status

from ..db import fetch_rows, insert_row, upsert_row
from ..schemas.client import ClientCreate, ClientResponse, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=list[ClientResponse])
def list_clients():
    rows = fetch_rows("clients")
    return rows


@router.post(
    "/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED
)
def create_client(payload: ClientCreate):
    # ensure username lowercase
    data = payload.dict()
    data["ig_username"] = data["ig_username"].lower()
    existing = fetch_rows("clients", {"ig_username": data["ig_username"]})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client already exists",
        )
    row = insert_row("clients", data)
    return row


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: str, payload: ClientUpdate):
    data = payload.dict(exclude_unset=True)
    if not data:
        row = fetch_rows("clients", {"id": client_id})
        if not row:
            raise HTTPException(status_code=404, detail="Client not found")
        return row[0]
    data["id"] = client_id
    row = upsert_row("clients", data, on_conflict="id")
    return row

