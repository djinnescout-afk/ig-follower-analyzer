#!/usr/bin/env python3
"""
Actively rescrape pages with 0 or missing follower counts.

This script immediately triggers scrapes for pages with 0 followers
by finding which clients follow them and running the following scraper.
"""

import os
import logging
import sys
from datetime import datetime
from supabase import create_client, Client
from apify_client import ApifyClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)

def get_apify_client() -> ApifyClient:
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise ValueError("APIFY_TOKEN must be set")
    return ApifyClient(token)

def find_zero_follower_pages(client: Client):
    """Find pages with 0 followers."""
    logging.info("Finding pages with 0 followers...")
    
    response = client.table("pages").select(
        "id, ig_username, follower_count, client_count"
    ).eq("follower_count", 0).execute()
    
    pages = response.data
    logging.info(f"Found {len(pages)} pages with 0 followers")
    return pages

def rescrape_page_via_client(supabase: Client, apify: ApifyClient, page: dict):
    """Rescrape a page by finding a client that follows it and scraping their following."""
    logging.info(f"Rescaping @{page['ig_username']}...")
    
    # Find a client that follows this page
    response = supabase.table("client_following").select(
        "client_id"
    ).eq("page_id", page["id"]).limit(1).execute()
    
    if not response.data:
        logging.warning(f"  ❌ No clients follow @{page['ig_username']} - can't rescrape")
        return False
    
    client_id = response.data[0]["client_id"]
    
    # Get client username
    client_response = supabase.table("clients").select(
        "ig_username"
    ).eq("id", client_id).execute()
    
    if not client_response.data:
        logging.warning(f"  ❌ Client {client_id} not found")
        return False
    
    client_username = client_response.data[0]["ig_username"]
    logging.info(f"  Using client @{client_username} to rescrape...")
    
    # Run the Instagram following scraper
    try:
        run_input = {
            "username": [client_username],
            "resultsLimit": 10000,
        }
        
        logging.info(f"  Starting Apify scrape for @{client_username}...")
        run = apify.actor("louisdeconinck/instagram-following-scraper").call(
            run_input=run_input,
            timeout_secs=300
        )
        
        if run["status"] != "SUCCEEDED":
            logging.error(f"  ❌ Scrape failed: {run['status']}")
            return False
        
        # Get results
        dataset_items = list(apify.dataset(run["defaultDatasetId"]).iterate_items())
        logging.info(f"  ✓ Scraped {len(dataset_items)} pages from @{client_username}'s following")
        
        # Update follower counts for all scraped pages
        updated_count = 0
        for item in dataset_items:
            username = item.get("username")
            follower_count = item.get("followersCount", 0)
            
            if username:
                # Update the page
                supabase.table("pages").update({
                    "follower_count": follower_count,
                    "last_scraped": datetime.utcnow().isoformat()
                }).eq("ig_username", username).execute()
                
                if username == page["ig_username"]:
                    updated_count += 1
                    logging.info(f"  ✓ Updated @{username}: {follower_count} followers")
        
        return updated_count > 0
        
    except Exception as e:
        logging.error(f"  ❌ Error during scrape: {e}")
        return False

def main():
    supabase = get_supabase_client()
    apify = get_apify_client()
    
    # Find pages with 0 followers
    pages = find_zero_follower_pages(supabase)
    
    if not pages:
        logging.info("✓ No pages with 0 followers found!")
        return
    
    print(f"\nFound {len(pages)} pages with 0 followers:")
    for page in pages[:10]:  # Show first 10
        print(f"  - @{page['ig_username']} ({page['client_count']} clients)")
    
    if len(pages) > 10:
        print(f"  ... and {len(pages) - 10} more")
    
    print(f"\n⚠️  This will use Apify credits to rescrape these pages.")
    print(f"Continue? (y/n): ", end="")
    
    response = input().strip().lower()
    if response != 'y':
        logging.info("Cancelled")
        return
    
    # Rescrape each page
    success_count = 0
    for i, page in enumerate(pages, 1):
        logging.info(f"\n[{i}/{len(pages)}] Processing @{page['ig_username']}...")
        if rescrape_page_via_client(supabase, apify, page):
            success_count += 1
    
    logging.info(f"\n✓ Complete! Successfully updated {success_count}/{len(pages)} pages")

if __name__ == "__main__":
    main()

