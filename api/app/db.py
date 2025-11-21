from functools import lru_cache
from typing import Any
from datetime import datetime

from supabase import Client, create_client

from .config import get_settings


def serialize_for_db(data: dict[str, Any]) -> dict[str, Any]:
    """Convert datetime objects to ISO strings for database insertion."""
    serialized = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)


def insert_row(table: str, data: dict[str, Any]) -> dict[str, Any]:
    client = get_supabase_client()
    serialized_data = serialize_for_db(data)
    response = client.table(table).insert(serialized_data).execute()
    return response.data[0]


def upsert_row(table: str, data: dict[str, Any], on_conflict: str) -> dict[str, Any]:
    client = get_supabase_client()
    serialized_data = serialize_for_db(data)
    response = client.table(table).upsert(serialized_data, on_conflict=on_conflict).execute()
    return response.data[0]


def fetch_rows(table: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    client = get_supabase_client()
    query = client.table(table).select("*")
    filters = filters or {}
    for key, value in filters.items():
        query = query.eq(key, value)
    response = query.execute()
    return response.data or []

