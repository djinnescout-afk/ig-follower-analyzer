from datetime import datetime
from typing import Optional

from ..db import insert_row


def enqueue_scrape_run(
    *,
    job_type: str,
    target_username: str,
    client_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    payload = {
        "job_type": job_type,
        "target_username": target_username.lower(),
        "client_id": client_id,
        "status": "queued",
        "metadata": metadata or {},
        "started_at": None,
        "finished_at": None,
        "created_at": datetime.utcnow().isoformat(),
    }
    row = insert_row("scrape_runs", payload)
    return row

