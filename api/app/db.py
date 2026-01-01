from datetime import datetime
from functools import lru_cache
from typing import Any, Optional

from supabase import Client, create_client

from .config import get_settings


def serialize_datetime(data: dict[str, Any]) -> dict[str, Any]:
    """Convert datetime objects to ISO strings for JSON serialization."""
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, list):
            # Handle lists of datetimes
            result[key] = [v.isoformat() if isinstance(v, datetime) else v for v in value]
        else:
            result[key] = value
    return result


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)


def insert_row(table: str, data: dict[str, Any], user_id: Optional[str] = None) -> dict[str, Any]:
    """Insert a row. If user_id is provided, it will be added to the data."""
    client = get_supabase_client()
    serialized_data = serialize_datetime(data)
    if user_id and "user_id" not in serialized_data:
        serialized_data["user_id"] = user_id
    response = client.table(table).insert(serialized_data).execute()
    return response.data[0]


def upsert_row(table: str, data: dict[str, Any], on_conflict: str, user_id: Optional[str] = None) -> dict[str, Any]:
    """Upsert a row. If user_id is provided, it will be added to the data."""
    client = get_supabase_client()
    serialized_data = serialize_datetime(data)
    if user_id and "user_id" not in serialized_data:
        serialized_data["user_id"] = user_id
    response = client.table(table).upsert(serialized_data, on_conflict=on_conflict).execute()
    return response.data[0]


def update_row(table: str, row_id: str, data: dict[str, Any], user_id: Optional[str] = None) -> dict[str, Any]:
    """Update an existing row by ID. Only updates fields present in data.
    If user_id is provided, ensures the row belongs to that user."""
    client = get_supabase_client()
    serialized_data = serialize_datetime(data)
    query = client.table(table).update(serialized_data).eq("id", row_id)
    if user_id:
        query = query.eq("user_id", user_id)  # Ensure user owns the row
    response = query.execute()
    if not response.data:
        raise ValueError(f"Row not found or access denied: {table}.{row_id}")
    return response.data[0]


def fetch_rows(table: str, filters: dict[str, Any] | None = None, user_id: Optional[str] = None) -> list[dict[str, Any]]:
    """Fetch rows. If user_id is provided, filters by user_id."""
    client = get_supabase_client()
    query = client.table(table).select("*")
    filters = filters or {}
    for key, value in filters.items():
        query = query.eq(key, value)
    if user_id:
        query = query.eq("user_id", user_id)
    response = query.execute()
    return response.data or []

