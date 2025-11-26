#!/usr/bin/env python3
"""
Fix 0-follower pages by rescaping the clients that follow them.

This is the reliable approach - we scrape the client's following list,
which includes follower counts for all pages they follow.
"""

import os
import logging
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

def find_clients_to_rescrape(supabase: Client):
    """Find clients that follow pages with 0 followers."""
    logging.info("Finding clients that follow 0-follower pages...")
    
    # Get pages with 0 followers
    pages_response = supabase.table("pages").select(
        "id, ig_username"
    ).eq("follower_count", 0).execute()
    
    zero_follower_pages = pages_response.data
    logging.info(f"Found {len(zero_follower_pages)} pages with 0 followers")
    
    if not zero_follower_pages:
        return []
    
    # Find clients that follow these pages
    page_ids = [p["id"] for p in zero_follower_pages]
    
    clients_set = set()
    for page_id in page_ids:
        cf_response = supabase.table("client_following").select(
            "client_id"
        ).eq("page_id", page_id).execute()
        
        for cf in cf_response.data:
            clients_set.add(cf["client_id"])
    
    logging.info(f"Found {len(clients_set)} unique clients that follow these pages")
    
    # Get client details
    clients = []
    for client_id in clients_set:
        client_response = supabase.table("clients").select(
            "id, ig_username"
        ).eq("id", client_id).execute()
        
        if client_response.data:
            clients.append(client_response.data[0])
    
    return clients

def rescrape_client(supabase: Client, apify: ApifyClient, client: dict):
    """Rescrape a client's following list to update follower counts."""
    logging.info(f"Rescaping @{client['ig_username']}...")
    
    try:
        run_input = {
            "username": [client["ig_username"]],
            "resultsLimit": 10000,
        }
        
        logging.info(f"  Starting Apify scrape...")
        run = apify.actor("louisdeconinck/instagram-following-scraper").call(
            run_input=run_input,
            timeout_secs=300
        )
        
        if run["status"] != "SUCCEEDED":
            logging.error(f"  ❌ Scrape failed: {run['status']}")
            return False
        
        # Get results
        dataset_items = list(apify.dataset(run["defaultDatasetId"]).iterate_items())
        logging.info(f"  ✓ Scraped {len(dataset_items)} pages from following list")
        
        # Update follower counts for all scraped pages
        updated_count = 0
        for item in dataset_items:
            username = item.get("username")
            follower_count = item.get("followersCount", 0)
            
            if username and follower_count > 0:
                # Check if this page exists and has 0 followers
                existing = supabase.table("pages").select(
                    "follower_count"
                ).eq("ig_username", username).execute()
                
                if existing.data and existing.data[0]["follower_count"] == 0:
                    # Update it
                    supabase.table("pages").update({
                        "follower_count": follower_count,
                        "last_scraped": datetime.utcnow().isoformat()
                    }).eq("ig_username", username).execute()
                    
                    updated_count += 1
                    logging.info(f"    ✓ Fixed @{username}: {follower_count} followers")
        
        logging.info(f"  ✓ Fixed {updated_count} pages with 0 followers")
        return True
        
    except Exception as e:
        logging.error(f"  ❌ Error during scrape: {e}")
        return False

def main():
    supabase = get_supabase_client()
    apify = get_apify_client()
    
    # Find clients to rescrape
    clients = find_clients_to_rescrape(supabase)
    
    if not clients:
        logging.info("✓ No clients to rescrape (no 0-follower pages found)!")
        return
    
    print(f"\nFound {len(clients)} clients to rescrape:")
    for client in clients[:10]:  # Show first 10
        print(f"  - @{client['ig_username']}")
    
    if len(clients) > 10:
        print(f"  ... and {len(clients) - 10} more")
    
    print(f"\n⚠️  This will use Apify credits (~${len(clients) * 0.03:.2f}).")
    print(f"Rescrape {len(clients)} clients? (y/n): ", end="")
    
    response = input().strip().lower()
    if response != 'y':
        logging.info("Cancelled")
        return
    
    # Rescrape each client
    success_count = 0
    for i, client in enumerate(clients, 1):
        logging.info(f"\n[{i}/{len(clients)}] Processing @{client['ig_username']}...")
        if rescrape_client(supabase, apify, client):
            success_count += 1
    
    logging.info(f"\n✓ Complete! Successfully rescraped {success_count}/{len(clients)} clients")

if __name__ == "__main__":
    main()

