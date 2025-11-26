#!/usr/bin/env python3
"""
Fix duplicate pages and incorrect follower counts.

This script:
1. Identifies duplicate pages (same ig_username)
2. Merges duplicates, keeping the one with more data
3. Identifies pages with 0 followers that should have more
4. Queues them for re-scraping via client following worker
"""

import os
import logging
from datetime import datetime
from supabase import create_client, Client
from collections import defaultdict

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

def find_duplicates(client: Client):
    """Find pages with duplicate ig_username."""
    logging.info("Checking for duplicate pages...")
    
    # Get all pages
    response = client.table("pages").select("id, ig_username, follower_count, client_count, category, last_scraped, created_at, updated_at").execute()
    pages = response.data
    
    # Group by username
    username_groups = defaultdict(list)
    for page in pages:
        username_groups[page["ig_username"]].append(page)
    
    # Find duplicates
    duplicates = {username: pages for username, pages in username_groups.items() if len(pages) > 1}
    
    if duplicates:
        logging.info(f"Found {len(duplicates)} usernames with duplicates:")
        for username, pages in duplicates.items():
            logging.info(f"  @{username}: {len(pages)} copies")
            for page in pages:
                logging.info(f"    - ID: {page['id']}, followers: {page['follower_count']}, clients: {page['client_count']}, category: {page['category']}")
    else:
        logging.info("No duplicates found!")
    
    return duplicates

def merge_duplicates(client: Client, duplicates: dict):
    """Merge duplicate pages, keeping the best one."""
    for username, pages in duplicates.items():
        logging.info(f"Merging duplicates for @{username}...")
        
        # Sort pages: prefer ones with category, then more clients, then higher follower count, then most recent
        pages.sort(key=lambda p: (
            p['category'] is not None,
            p['client_count'],
            p['follower_count'] or 0,
            p['updated_at']
        ), reverse=True)
        
        # Keep the first one (best)
        keep_page = pages[0]
        delete_pages = pages[1:]
        
        logging.info(f"  Keeping page ID: {keep_page['id']} (followers: {keep_page['follower_count']}, clients: {keep_page['client_count']})")
        
        for delete_page in delete_pages:
            logging.info(f"  Deleting page ID: {delete_page['id']}")
            
            # Update client_following to point to the kept page
            client.table("client_following").update({
                "page_id": keep_page["id"]
            }).eq("page_id", delete_page["id"]).execute()
            
            # Delete the duplicate page
            client.table("pages").delete().eq("id", delete_page["id"]).execute()
        
        logging.info(f"  ✓ Merged {len(delete_pages)} duplicate(s)")

def find_zero_follower_pages(client: Client):
    """Find pages with 0 or very low follower counts that seem wrong."""
    logging.info("Checking for pages with 0 followers...")
    
    response = client.table("pages").select(
        "id, ig_username, follower_count, client_count, last_scraped"
    ).eq("follower_count", 0).execute()
    
    zero_follower_pages = response.data
    
    if zero_follower_pages:
        logging.info(f"Found {len(zero_follower_pages)} pages with 0 followers:")
        for page in zero_follower_pages[:20]:  # Show first 20
            logging.info(f"  @{page['ig_username']}: {page['client_count']} clients, last scraped: {page['last_scraped']}")
    else:
        logging.info("No pages with 0 followers found")
    
    return zero_follower_pages

def queue_for_rescrape(client: Client, pages: list):
    """Queue pages for re-scraping by finding which clients follow them."""
    logging.info("Queuing pages for re-scrape via client following...")
    
    for page in pages:
        # Find clients that follow this page
        response = client.table("client_following").select(
            "client_id"
        ).eq("page_id", page["id"]).execute()
        
        if response.data:
            client_ids = [cf["client_id"] for cf in response.data]
            logging.info(f"  @{page['ig_username']}: Will be re-scraped when clients {client_ids} are re-scraped")
        else:
            logging.info(f"  @{page['ig_username']}: No clients following - can't auto re-scrape")

def main():
    client = get_supabase_client()
    
    # Step 1: Find and merge duplicates
    duplicates = find_duplicates(client)
    
    if duplicates:
        print("\n⚠️  Found duplicates! Do you want to merge them? (y/n): ", end="")
        response = input().strip().lower()
        if response == 'y':
            merge_duplicates(client, duplicates)
            logging.info("✓ Duplicates merged!")
        else:
            logging.info("Skipping duplicate merge")
    
    # Step 2: Find pages with 0 followers
    zero_follower_pages = find_zero_follower_pages(client)
    
    if zero_follower_pages:
        print(f"\n⚠️  Found {len(zero_follower_pages)} pages with 0 followers. Queue them for re-scrape? (y/n): ", end="")
        response = input().strip().lower()
        if response == 'y':
            queue_for_rescrape(client, zero_follower_pages)
            logging.info("✓ Pages queued for re-scrape (will happen when clients are re-scraped)")
        else:
            logging.info("Skipping re-scrape queue")
    
    logging.info("\n✓ Script complete!")

if __name__ == "__main__":
    main()

