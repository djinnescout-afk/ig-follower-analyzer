from fastapi import APIRouter, HTTPException, status

from ..db import fetch_rows, insert_row, upsert_row
from ..schemas.page import PageCreate, PageResponse, PageUpdate

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("/", response_model=list[PageResponse])
def list_pages():
    rows = fetch_rows("pages")
    return rows


@router.post("/", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
def create_page(payload: PageCreate):
    data = payload.model_dump()
    data["ig_username"] = data["ig_username"].lower()
    existing = fetch_rows("pages", {"ig_username": data["ig_username"]})
    if existing:
        raise HTTPException(status_code=409, detail="Page already exists")
    row = insert_row("pages", data)
    return row


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

