from fastapi import APIRouter, HTTPException, status
import logging

from ..db import fetch_rows, insert_row, upsert_row
from ..schemas.client import ClientCreate, ClientResponse, ClientUpdate, ClientBulkCreate, ClientBulkResult

router = APIRouter(prefix="/clients", tags=["clients"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[ClientResponse])
def list_clients():
    rows = fetch_rows("clients")
    return rows


@router.post(
    "/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED
)
def create_client(payload: ClientCreate):
    # ensure username lowercase
    data = payload.model_dump()
    data["ig_username"] = data["ig_username"].lower()
    existing = fetch_rows("clients", {"ig_username": data["ig_username"]})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client already exists",
        )
    row = insert_row("clients", data)
    return row


@router.post("/bulk", response_model=ClientBulkResult, status_code=status.HTTP_201_CREATED)
def create_clients_bulk(payload: ClientBulkCreate):
    """Create multiple clients at once. Returns successfully created clients and failed ones with reasons."""
    result = ClientBulkResult()
    
    for client in payload.clients:
        try:
            # Ensure username lowercase
            data = client.model_dump()
            data["ig_username"] = data["ig_username"].lower().strip()
            
            # Skip empty usernames
            if not data["ig_username"]:
                result.failed.append({
                    "name": data.get("name", "Unknown"),
                    "ig_username": "",
                    "reason": "Empty username"
                })
                continue
            
            # Check if already exists
            existing = fetch_rows("clients", {"ig_username": data["ig_username"]})
            if existing:
                result.failed.append({
                    "name": data["name"],
                    "ig_username": data["ig_username"],
                    "reason": "Already exists"
                })
                continue
            
            # Insert client
            row = insert_row("clients", data)
            result.success.append(row)
            logger.info(f"Bulk created client: {data['ig_username']}")
            
        except Exception as e:
            logger.error(f"Error creating client {client.ig_username}: {e}")
            result.failed.append({
                "name": client.name,
                "ig_username": client.ig_username,
                "reason": str(e)
            })
    
    return result


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: str, payload: ClientUpdate):
    data = payload.model_dump(exclude_unset=True)
    if not data:
        row = fetch_rows("clients", {"id": client_id})
        if not row:
            raise HTTPException(status_code=404, detail="Client not found")
        return row[0]
    data["id"] = client_id
    row = upsert_row("clients", data, on_conflict="id")
    return row

