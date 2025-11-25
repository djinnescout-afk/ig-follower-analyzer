"""
One-time script to backfill follower counts for existing pages

Finds all pages with follower_count = 0 or NULL and queues profile scrape jobs for them.
This fixes pages that were added before the auto-scraping feature was implemented.
"""

import os
import sys
import logging
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_follower_counts():
    """Find pages with missing follower counts and queue profile scrapes"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not all([supabase_url, supabase_key]):
        raise ValueError("Missing required environment variables")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    logger.info("Finding pages with missing follower counts...")
    
    # Find pages with 0 or null follower_count that have at least 1 client
    # (pages with 0 clients don't need to be prioritized)
    all_pages = []
    offset = 0
    limit = 1000
    
    while True:
        result = supabase.table("pages")\
            .select("id, ig_username, follower_count, client_count")\
            .gte("client_count", 1)\
            .limit(limit)\
            .offset(offset)\
            .execute()
        
        batch = result.data or []
        all_pages.extend(batch)
        
        logger.info(f"Fetched batch at offset {offset}: {len(batch)} pages")
        
        if len(batch) < limit:
            break
        
        offset += limit
    
    # Filter to only pages with 0 or null follower_count
    pages_needing_scrape = [
        p for p in all_pages
        if not p.get("follower_count") or p.get("follower_count") == 0
    ]
    
    logger.info(f"Found {len(pages_needing_scrape)} pages needing follower count updates")
    
    if not pages_needing_scrape:
        logger.info("No pages need updating!")
        return
    
    # Queue profile scrape jobs (batched)
    logger.info("Queueing profile scrape jobs...")
    batch_size = 100
    total_queued = 0
    
    for i in range(0, len(pages_needing_scrape), batch_size):
        batch = pages_needing_scrape[i:i + batch_size]
        
        scrape_jobs = [
            {
                "page_id": page["id"],
                "scrape_type": "profile",
                "status": "pending",
                "priority": 10  # Low priority - background task
            }
            for page in batch
        ]
        
        supabase.table("scrape_jobs").insert(scrape_jobs).execute()
        total_queued += len(scrape_jobs)
        logger.info(f"Queued batch {i//batch_size + 1}: {len(scrape_jobs)} jobs (total: {total_queued}/{len(pages_needing_scrape)})")
    
    logger.info(f"✅ Successfully queued {total_queued} profile scrape jobs")
    logger.info("The profile scrape worker will process these jobs automatically.")


def main():
    """Main entry point"""
    try:
        backfill_follower_counts()
    except Exception as e:
        logger.error(f"Backfill failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

