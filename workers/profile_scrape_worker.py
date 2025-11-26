"""
Profile Scraper Worker

Polls the scrape_runs table for pending profile scrape jobs,
executes them via Apify, analyzes for promo signals, and stores results.
"""

import os
import sys
import time
import base64
import logging
import requests
from datetime import datetime
from typing import Optional
from io import BytesIO
from apify_client import ApifyClient
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProfileScrapeWorker:
    """Worker that processes profile scraping jobs"""
    
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
        logger.info("Profile scraper worker started, polling for jobs...")
        
        while True:
            try:
                # Get next pending profile_scrape job
                result = self.supabase.table("scrape_runs")\
                    .select("*")\
                    .eq("scrape_type", "profile_scrape")\
                    .eq("status", "pending")\
                    .order("created_at", desc=False)\
                    .limit(1)\
                    .execute()
                
                if result.data:
                    job = result.data[0]
                    logger.info(f"Processing profile scrape job {job['id']}")
                    self.process_job(job)
                else:
                    logger.debug("No pending jobs, waiting...")
                    time.sleep(poll_interval)
                    
            except Exception as e:
                logger.error(f"Error in poll loop: {e}", exc_info=True)
                time.sleep(poll_interval)
    
    def process_job(self, job: dict):
        """Process a single profile scrape job"""
        job_id = job["id"]
        page_ids = job.get("page_ids", [])
        
        if not page_ids:
            logger.warning(f"Job {job_id} has no page_ids")
            return
        
        try:
            # Mark as processing
            self.supabase.table("scrape_runs")\
                .update({"status": "processing", "started_at": datetime.utcnow().isoformat()})\
                .eq("id", job_id)\
                .execute()
            
            # Get pages to scrape
            pages = self.supabase.table("pages")\
                .select("id, ig_username")\
                .in_("id", page_ids)\
                .execute()
            
            total = len(pages.data)
            success_count = 0
            failed_usernames = []
            
            logger.info(f"Scraping {total} profiles...")
            
            for page in pages.data:
                try:
                    self.scrape_profile(page["id"], page["ig_username"])
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to scrape @{page['ig_username']}: {e}")
                    failed_usernames.append(page["ig_username"])
            
            # Update scrape run as completed
            self.supabase.table("scrape_runs")\
                .update({
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "result": {
                        "total_pages": total,
                        "success_count": success_count,
                        "failed_count": len(failed_usernames),
                        "failed_usernames": failed_usernames
                    }
                })\
                .eq("id", job_id)\
                .execute()
            
            logger.info(f"âœ… Job {job_id} completed: {success_count}/{total} profiles scraped")
            
        except Exception as e:
            logger.error(f"âŒ Job {job_id} failed: {e}", exc_info=True)
            
            # Mark job as failed
            self.supabase.table("scrape_runs")\
                .update({
                    "status": "failed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "result": {"error": str(e)}
                })\
                .eq("id", job_id)\
                .execute()
    
    def scrape_profile(self, page_id: str, ig_username: str):
        """Scrape a single Instagram profile and store results"""
        logger.info(f"Scraping profile: @{ig_username}")
        
        try:
            # Run Apify actor
            run_input = {
                "usernames": [ig_username],
                "resultsLimit": 12,  # Get 12 recent posts
            }
            
            logger.info(f"Starting Apify actor for @{ig_username}...")
            run = self.apify_client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
            logger.info(f"Apify actor completed for @{ig_username}, status: {run.get('status')}")
            
            dataset = self.apify_client.dataset(run["defaultDatasetId"])
            
            items = list(dataset.iterate_items())
            logger.info(f"Retrieved {len(items)} items from Apify for @{ig_username}")
            
            if not items:
                # Mark page with failed scrape status
                self.supabase.table("pages")\
                    .update({"last_scrape_status": "failed"})\
                    .eq("id", page_id)\
                    .execute()
                raise Exception(f"No data returned from Apify for @{ig_username}. Run status: {run.get('status')}, Run ID: {run.get('id')}")
            
            profile_data = items[0]
            
            # Check if profile was found
            if not profile_data.get("id"):
                self.supabase.table("pages")\
                    .update({"last_scrape_status": "failed"})\
                    .eq("id", page_id)\
                    .execute()
                raise Exception(f"Profile not found or inaccessible for @{ig_username}")
            
            # Extract profile info
            profile_pic_url = profile_data.get("profilePicUrl")
            bio = profile_data.get("biography", "")
            posts = profile_data.get("latestPosts", [])
            
            # Download and encode profile picture
            profile_pic_base64, profile_pic_mime = self.download_and_encode_image(profile_pic_url)
            
            # Process posts
            processed_posts = []
            for post in posts[:12]:  # Limit to 12 posts
                post_images = []
                for img_url in post.get("displayUrl", [])[:3]:  # Max 3 images per post
                    img_base64, img_mime = self.download_and_encode_image(img_url)
                    if img_base64:
                        post_images.append({
                            "image_base64": img_base64,
                            "mime_type": img_mime
                        })
                
                processed_posts.append({
                    "caption": post.get("caption", ""),
                    "images": post_images,
                    "likes": post.get("likesCount", 0),
                    "comments": post.get("commentsCount", 0)
                })
            
            # Detect promo signals
            promo_status, promo_indicators = self.detect_promo_openness(bio, posts)
            contact_email = self.extract_email(bio)
            
            # Store in page_profiles table
            profile_record = {
                "page_id": page_id,
                "profile_pic_base64": profile_pic_base64,
                "profile_pic_mime_type": profile_pic_mime,
                "bio": bio,
                "posts": processed_posts,
                "promo_status": promo_status,
                "promo_indicators": promo_indicators,
                "contact_email": contact_email,
                "scraped_at": datetime.utcnow().isoformat()
            }
            
            # Upsert profile data
            self.supabase.table("page_profiles")\
                .upsert(profile_record, on_conflict="page_id")\
                .execute()
            
            # Update page metadata
            self.supabase.table("pages")\
                .update({
                    "last_scraped": datetime.utcnow().isoformat(),
                    "last_scrape_status": "success",
                    "follower_count": profile_data.get("followersCount", 0),
                    "is_verified": profile_data.get("verified", False),
                    "is_private": profile_data.get("private", False)
                })\
                .eq("id", page_id)\
                .execute()
            
            logger.info(f"âœ… Profile saved for @{ig_username} (promo: {promo_status})")
            
        except Exception as e:
            logger.error(f"Failed to scrape @{ig_username}: {e}")
            # Mark page with failed scrape status
            try:
                self.supabase.table("pages")\
                    .update({"last_scrape_status": "failed"})\
                    .eq("id", page_id)\
                    .execute()
            except Exception as update_error:
                logger.error(f"Failed to update scrape status: {update_error}")
            raise
    
    def download_and_encode_image(self, url: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Download image and encode as base64"""
        if not url:
            return None, None
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Determine MIME type
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            # Encode as base64
            img_data = base64.b64encode(response.content).decode('utf-8')
            
            return img_data, content_type
            
        except Exception as e:
            logger.warning(f"Failed to download image {url}: {e}")
            return None, None
    
    def detect_promo_openness(self, bio: str, posts: list) -> tuple[str, list[str]]:
        """
        Detect if page is open to promos
        Returns: (status, indicators)
        """
        bio_lower = bio.lower()
        indicators = []
        
        # Check bio for promo keywords
        promo_keywords = [
            "collab", "collaboration", "business inquiries", "partnerships",
            "dm for business", "sponsorship", "brand deals", "promotion",
            "advertising", "marketing", "dm for collab"
        ]
        
        for keyword in promo_keywords:
            if keyword in bio_lower:
                indicators.append(f"Bio mentions '{keyword}'")
        
        # Check for business email in bio
        if "@" in bio and "." in bio:
            indicators.append("Business email in bio")
        
        # Determine status
        if indicators:
            status = "warm"
        else:
            status = "unknown"
        
        return status, indicators
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email from text"""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None


def main():
    """Main entry point"""
    try:
        worker = ProfileScrapeWorker()
        worker.poll_for_jobs()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

