"""
Lightweight Follower Count Backfill

Uses Apify's basic profile scraper to ONLY get follower counts (no bio, images, posts).
This is much cheaper and faster than full profile scraping.

Cost estimate: ~$2-3 for 28k profiles (vs $7-15 for full scraping)
"""

import os
import sys
import logging
from datetime import datetime
from apify_client import ApifyClient
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_follower_counts_lightweight():
    """Backfill follower counts using lightweight scraping"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    apify_token = os.getenv("APIFY_TOKEN")
    
    if not all([supabase_url, supabase_key, apify_token]):
        raise ValueError("Missing required environment variables")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    apify_client = ApifyClient(apify_token)
    
    logger.info("Finding ALL pages with missing follower counts...")
    
    all_pages = []
    offset = 0
    limit = 1000
    
    while True:
        result = supabase.table("pages")\
            .select("id, ig_username, follower_count, client_count")\
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
    
    logger.info(f"Found {len(pages_needing_scrape)} pages needing follower counts (out of {len(all_pages)} total)")
    
    if not pages_needing_scrape:
        logger.info("No pages need updating!")
        return
    
    # Batch scrape follower counts
    logger.info("Starting lightweight follower count scraping...")
    
    batch_size = 100  # Scrape in batches of 100
    total_updated = 0
    
    for i in range(0, len(pages_needing_scrape), batch_size):
        batch = pages_needing_scrape[i:i + batch_size]
        usernames = [p["ig_username"] for p in batch]
        
        logger.info(f"Scraping batch {i//batch_size + 1}: {len(usernames)} profiles...")
        
        try:
            # Use Apify's Instagram Profile Scraper with minimal data
            run_input = {
                "usernames": usernames,
                "resultsLimit": len(usernames),
                # Only get basic profile info (follower count)
                "addParentData": False,
            }
            
            run = apify_client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
            dataset = apify_client.dataset(run["defaultDatasetId"])
            
            # Process results and update database
            for item in dataset.iterate_items():
                username = item.get("username")
                if not username:
                    continue
                
                # Extract follower count
                follower_count = 0
                if item.get("followersCount"):
                    follower_count = item["followersCount"]
                elif item.get("edge_followed_by", {}).get("count"):
                    follower_count = item["edge_followed_by"]["count"]
                
                # Update page in database
                supabase.table("pages")\
                    .update({"follower_count": follower_count})\
                    .eq("ig_username", username)\
                    .execute()
                
                total_updated += 1
            
            logger.info(f"Updated batch {i//batch_size + 1}: {total_updated}/{len(pages_needing_scrape)} pages")
            
        except Exception as e:
            logger.error(f"Batch {i//batch_size + 1} failed: {e}")
            continue
    
    logger.info(f"✅ Successfully updated {total_updated} pages with follower counts")
    
    # Show cost estimate
    estimated_cost = (len(pages_needing_scrape) / 1000) * 0.30
    logger.info(f"💰 Estimated cost: ${estimated_cost:.2f}")


def main():
    """Main entry point"""
    try:
        backfill_follower_counts_lightweight()
    except Exception as e:
        logger.error(f"Backfill failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

