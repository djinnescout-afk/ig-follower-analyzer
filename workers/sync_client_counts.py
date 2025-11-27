"""
Sync Client Counts Worker

Updates the client_count column for all pages based on actual 
client_following relationships.
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


def sync_client_counts():
    """Sync client_count column for all pages based on actual relationships"""
    
    # Get environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not all([supabase_url, supabase_key]):
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    logger.info("Starting client_count sync...")
    
    try:
        # Update client_count in batches
        sync_client_counts_batch(supabase)
        
    except Exception as e:
        logger.error(f"Error syncing client counts: {e}", exc_info=True)
        raise


def sync_client_counts_batch(supabase: Client):
    """Update client_count by batching page IDs"""
    
    logger.info("Getting all pages and their relationship counts...")
    
    # Get all page IDs
    all_pages = []
    batch_size = 1000
    offset = 0
    
    while True:
        pages_result = supabase.table("pages")\
            .select("id, client_count")\
            .range(offset, offset + batch_size - 1)\
            .execute()
        
        if not pages_result.data:
            break
        
        all_pages.extend(pages_result.data)
        offset += batch_size
        
        if len(pages_result.data) < batch_size:
            break
    
    logger.info(f"Found {len(all_pages)} total pages")
    
    # Get all relationships and count them
    logger.info("Counting all client_following relationships...")
    all_relationships = []
    offset = 0
    
    while True:
        rel_result = supabase.table("client_following")\
            .select("page_id")\
            .range(offset, offset + batch_size - 1)\
            .execute()
        
        if not rel_result.data:
            break
        
        all_relationships.extend(rel_result.data)
        offset += batch_size
        
        if len(rel_result.data) < batch_size:
            break
    
    logger.info(f"Found {len(all_relationships)} total relationships")
    
    # Count relationships per page
    count_map = {}
    for rel in all_relationships:
        page_id = rel["page_id"]
        count_map[page_id] = count_map.get(page_id, 0) + 1
    
    # Update pages where count doesn't match
    total_updated = 0
    needs_update = []
    
    for page in all_pages:
        actual_count = count_map.get(page["id"], 0)
        if page["client_count"] != actual_count:
            needs_update.append((page["id"], actual_count))
    
    logger.info(f"Found {len(needs_update)} pages that need updating")
    
    # Batch update
    update_batch_size = 50  # Smaller batches for update queries
    for i in range(0, len(needs_update), update_batch_size):
        batch = needs_update[i:i + update_batch_size]
        
        for page_id, count in batch:
            supabase.table("pages")\
                .update({"client_count": count})\
                .eq("id", page_id)\
                .execute()
            total_updated += 1
        
        if (i + update_batch_size) % 500 == 0:
            logger.info(f"Progress: {total_updated}/{len(needs_update)} pages updated")
    
    logger.info(f"✅ Batch update complete! Updated {total_updated} pages")
    
    # Verify
    verification = supabase.table("pages")\
        .select("id", count="exact")\
        .or_("client_count.is.null,client_count.eq.0")\
        .execute()
    
    logger.info(f"Pages with client_count=0/NULL after sync: {verification.count or 0}")


if __name__ == "__main__":
    try:
        sync_client_counts()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

