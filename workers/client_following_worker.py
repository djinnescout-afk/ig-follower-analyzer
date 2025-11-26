"""
Client Following Scraper Worker

Polls the scrape_runs table for pending client following scrapes,
executes them via Apify, and updates the database with results.
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Optional
from apify_client import ApifyClient
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClientFollowingWorker:
    """Worker that processes client following scrape jobs"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.apify_token = os.getenv("APIFY_TOKEN")
        
        if not all([self.supabase_url, self.supabase_key, self.apify_token]):
            raise ValueError("Missing required environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.apify_client = ApifyClient(self.apify_token)
        
    def poll_for_jobs(self, poll_interval: int = 10):
        """Continuously poll for pending scrape jobs"""
        logger.info("Worker started, polling for jobs...")
        
        while True:
            try:
                # Get next pending client_following job
                result = self.supabase.table("scrape_runs")\
                    .select("*")\
                    .eq("scrape_type", "client_following")\
                    .eq("status", "pending")\
                    .order("created_at", desc=False)\
                    .limit(1)\
                    .execute()
                
                if result.data:
                    job = result.data[0]
                    logger.info(f"Processing job {job['id']} for client {job['client_id']}")
                    self.process_job(job)
                else:
                    logger.debug("No pending jobs, waiting...")
                    time.sleep(poll_interval)
                    
            except Exception as e:
                logger.error(f"Error in poll loop: {e}", exc_info=True)
                time.sleep(poll_interval)
    
    def process_job(self, job: dict):
        """Process a single scrape job"""
        job_id = job["id"]
        client_id = job["client_id"]
        
        try:
            # Mark as processing
            self.supabase.table("scrape_runs")\
                .update({"status": "processing", "started_at": datetime.utcnow().isoformat()})\
                .eq("id", job_id)\
                .execute()
            
            # Get client username
            client = self.supabase.table("clients")\
                .select("ig_username")\
                .eq("id", client_id)\
                .single()\
                .execute()
            
            ig_username = client.data["ig_username"]
            logger.info(f"Scraping following list for @{ig_username}")
            
            # Get expected following count from Instagram
            total_following_count = self.get_following_count(ig_username)
            
            # Run Apify actor
            following_list, failed_usernames = self.scrape_following(ig_username)
            
            if following_list is None:
                raise Exception("Failed to scrape following list")
            
            # Calculate coverage
            coverage = 0.0
            if total_following_count and total_following_count > 0:
                coverage = len(following_list) / total_following_count
            
            # Store results in database
            self.store_following_results(client_id, following_list)
            
            # Update scrape run as completed
            self.supabase.table("scrape_runs")\
                .update({
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "result": {
                        "accounts_scraped": len(following_list),
                        "expected_count": total_following_count,
                        "coverage_percent": coverage * 100,
                        "failed_usernames": failed_usernames
                    }
                })\
                .eq("id", job_id)\
                .execute()
            
            # Update client following_count
            self.supabase.table("clients")\
                .update({
                    "following_count": len(following_list),
                    "last_scraped": datetime.utcnow().isoformat()
                })\
                .eq("id", client_id)\
                .execute()
            
            logger.info(f"Γ£à Job {job_id} completed: {len(following_list)} accounts, {coverage*100:.1f}% coverage")
            
        except Exception as e:
            logger.error(f"Γ¥î Job {job_id} failed: {e}", exc_info=True)
            
            # Mark job as failed
            self.supabase.table("scrape_runs")\
                .update({
                    "status": "failed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "result": {"error": str(e)}
                })\
                .eq("id", job_id)\
                .execute()
    
    def get_following_count(self, ig_username: str) -> Optional[int]:
        """Get total following count from Instagram profile"""
        try:
            logger.info(f"Getting following count for @{ig_username}...")
            
            run_input = {
                "usernames": [ig_username],
                "resultsLimit": 1,
            }
            
            run = self.apify_client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
            dataset = self.apify_client.dataset(run["defaultDatasetId"])
            
            for item in dataset.iterate_items():
                edge_follow = item.get("edge_follow", {})
                count = edge_follow.get("count", 0) if edge_follow else 0
                
                if not count:
                    count = item.get("followingCount", 0) or item.get("following_count", 0)
                
                if count:
                    logger.info(f"Instagram reports {count} following accounts")
                    return count
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not get following count: {e}")
            return None
    
    def scrape_following(self, ig_username: str) -> tuple[list[dict], list[str]]:
        """
        Scrape following list via Apify
        Returns: (following_list, failed_usernames)
        """
        try:
            run_input = {
                "usernames": [ig_username],
            }
            
            logger.info(f"Starting Apify scrape for @{ig_username}...")
            run = self.apify_client.actor("louisdeconinck/instagram-following-scraper").call(run_input=run_input)
            
            # Fetch results
            following_list = []
            failed_usernames = []
            dataset = self.apify_client.dataset(run["defaultDatasetId"])
            
            for item in dataset.iterate_items():
                if item.get("username"):
                    following_list.append({
                        "username": item.get("username"),
                        "full_name": item.get("full_name", ""),
                        # Note: follower_count not available from following scraper
                        "is_verified": item.get("is_verified", False),
                        "is_private": item.get("is_private", False),
                    })
            
            logger.info(f"Retrieved {len(following_list)} accounts")
            return following_list, failed_usernames
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return None, []
    
    def store_following_results(self, client_id: str, following_list: list[dict]):
        """Store following results in database"""
        logger.info(f"Storing {len(following_list)} following records...")
        
        # First, ensure all pages exist (batch create)
        pages_to_create = []
        batch_check_size = 50  # Smaller batches for .in() query
        
        for i in range(0, len(following_list), batch_check_size):
            batch = following_list[i:i + batch_check_size]
            usernames = [a["username"] for a in batch]
            
            # Check which pages already exist
            existing = self.supabase.table("pages")\
                .select("ig_username")\
                .in_("ig_username", usernames)\
                .execute()
            
            existing_usernames = {p["ig_username"] for p in (existing.data or [])}
            
            # Add non-existing pages to create list
            for account in batch:
                if account["username"] not in existing_usernames:
                    pages_to_create.append({
                        "ig_username": account["username"],
                        "full_name": account.get("full_name"),
                        # follower_count will be scraped separately for high-value pages
                        "follower_count": 0,  # Default to 0, will be updated by profile scraper
                        "is_verified": account.get("is_verified", False),
                        "is_private": account.get("is_private", False),
                    })
        
        # Batch insert new pages
        if pages_to_create:
            logger.info(f"Creating {len(pages_to_create)} new pages...")
            insert_batch_size = 100
            for i in range(0, len(pages_to_create), insert_batch_size):
                batch = pages_to_create[i:i + insert_batch_size]
                self.supabase.table("pages").insert(batch).execute()
                logger.info(f"Created pages batch {i//insert_batch_size + 1}: {len(batch)} pages")
        
        # Note: The following scraper does NOT return follower counts
        # Follower counts are scraped separately for high-value pages via _scrape_targeted_follower_counts
        logger.info(f"Note: Follower counts will be scraped separately for high-value pages (hotlist, 2+ clients)")
        
        # Now insert client_following relationships
        # First delete existing relationships for this client
        logger.info(f"Deleting existing relationships for client {client_id}...")
        self.supabase.table("client_following")\
            .delete()\
            .eq("client_id", client_id)\
            .execute()
        
        # Batch insert new relationships with smaller batches
        logger.info(f"Inserting {len(following_list)} relationships...")
        relationship_batch_size = 50  # Smaller for .in() query
        total_inserted = 0
        
        for i in range(0, len(following_list), relationship_batch_size):
            batch = following_list[i:i + relationship_batch_size]
            
            # Get page IDs for this batch
            usernames = [a["username"] for a in batch]
            pages = self.supabase.table("pages")\
                .select("id, ig_username")\
                .in_("ig_username", usernames)\
                .execute()
            
            # Create username -> id mapping
            page_id_map = {p["ig_username"]: p["id"] for p in (pages.data or [])}
            
            # Insert relationships
            relationships = [
                {
                    "client_id": client_id,
                    "page_id": page_id_map[account["username"]]
                }
                for account in batch
                if account["username"] in page_id_map
            ]
            
            if relationships:
                self.supabase.table("client_following")\
                    .insert(relationships)\
                    .execute()
                total_inserted += len(relationships)
                logger.info(f"Inserted relationship batch {i//relationship_batch_size + 1}: {len(relationships)} relationships (total: {total_inserted})")
        
        logger.info(f"Γ£à Stored following data for client {client_id}: {total_inserted} relationships created")
        
        # After storing relationships, scrape follower counts for ALL high-value pages (new AND existing)
        logger.info("Checking which pages need follower counts (hotlist or 2+ clients)...")
        all_usernames = [account["username"] for account in following_list]
        self._scrape_targeted_follower_counts(all_usernames)
    
    def _scrape_targeted_follower_counts(self, new_usernames: list[str]):
        """
        Scrape follower counts ONLY for high-value pages:
        - Hotlist pages (match keywords + not categorized)
        - Pages with 2+ clients
        
        This saves Apify credits by not scraping low-value pages.
        """
        try:
            # Hotlist keywords
            HOTLIST_KEYWORDS = [
                'hustl', 'afri', 'afro', 'black', 'melanin', 
                'blvck', 'culture', 'kulture', 'brown', 'noir', 'ebony'
            ]
            
            # Fetch pages in batches to avoid URL length limits
            pages_data = []
            batch_size = 100  # Query 100 usernames at a time
            
            for i in range(0, len(new_usernames), batch_size):
                batch = new_usernames[i:i + batch_size]
                try:
                    result = self.supabase.table("pages")\
                        .select("id, ig_username, full_name, follower_count, client_count, category")\
                        .in_("ig_username", batch)\
                        .execute()
                    pages_data.extend(result.data or [])
                except Exception as e:
                    logger.warning(f"Failed to fetch batch {i//batch_size + 1}: {e}")
            
            logger.info(f"Fetched {len(pages_data)} pages from database")
            
            # Filter to high-value pages needing follower counts
            targeted_pages = []
            
            for page in pages_data:
                username = page.get("ig_username", "").lower()
                full_name = (page.get("full_name") or "").lower()
                client_count = page.get("client_count", 0)
                category = page.get("category")
                
                # Check if hotlist (matches keywords AND not categorized)
                is_hotlist = (
                    any(keyword in f"{username} {full_name}" for keyword in HOTLIST_KEYWORDS)
                    and not category
                )
                
                # Check if 2+ clients
                has_multiple_clients = client_count >= 2
                
                # Scrape if hotlist OR 2+ clients (always update high-value pages)
                if is_hotlist or has_multiple_clients:
                    targeted_pages.append(page)
                    reason = []
                    if is_hotlist:
                        reason.append("hotlist")
                    if has_multiple_clients:
                        reason.append(f"{client_count} clients")
                    logger.info(f"  ≡ƒôî {username}: {', '.join(reason)}")
            
            if not targeted_pages:
                logger.info(f"Γ£à No high-value pages need follower counts (checked {len(pages_data)} new pages)")
                return
            
            logger.info(f"≡ƒÄ» Found {len(targeted_pages)} high-value pages to scrape (out of {len(pages_data)} new pages)")
            
            # Batch scrape (smaller batches to avoid Instagram rate limiting)
            batch_size = 25  # Reduced from 100 to avoid rate limiting
            total_updated = 0
            
            for i in range(0, len(targeted_pages), batch_size):
                batch = targeted_pages[i:i + batch_size]
                usernames = [p["ig_username"] for p in batch]
                
                try:
                    logger.info(f"Scraping batch {i//batch_size + 1}: {len(usernames)} usernames...")
                    
                    # Use Apify's Instagram Profile Scraper (lightweight)
                    run_input = {
                        "usernames": usernames,
                        "resultsLimit": len(usernames),
                        "addParentData": False,  # Don't fetch additional data
                    }
                    
                    run = self.apify_client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
                    dataset = self.apify_client.dataset(run["defaultDatasetId"])
                    
                    # Update database with follower counts
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
                        
                        # Update page
                        self.supabase.table("pages")\
                            .update({"follower_count": follower_count})\
                            .eq("ig_username", username)\
                            .execute()
                        
                        total_updated += 1
                        logger.info(f"    Γ£ô @{username}: {follower_count:,} followers")
                    
                    logger.info(f"Updated batch {i//batch_size + 1}: {total_updated} pages total")
                    
                except Exception as e:
                    logger.warning(f"Failed to scrape batch {i//batch_size + 1}: {e}")
                    continue
            
            logger.info(f"Γ£à Successfully scraped follower counts for {total_updated}/{len(targeted_pages)} high-value pages")
            
        except Exception as e:
            logger.warning(f"Failed to scrape follower counts: {e}")
            # Don't fail the whole import if follower scraping fails


def main():
    """Main entry point"""
    try:
        worker = ClientFollowingWorker()
        worker.poll_for_jobs()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

