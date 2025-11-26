#!/usr/bin/env python3
"""
List which clients need rescaping to fix 0-follower pages.
"""

import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)

def main():
    client = get_supabase_client()
    
    # Get pages with 0 followers
    print("Finding pages with 0 followers...")
    pages_response = client.table("pages").select(
        "id, ig_username, client_count"
    ).eq("follower_count", 0).execute()
    
    zero_pages = pages_response.data
    print(f"\nFound {len(zero_pages)} pages with 0 followers:")
    
    # Group by client
    client_pages = {}
    
    for page in zero_pages:
        # Find clients that follow this page
        cf_response = client.table("client_following").select(
            "client_id"
        ).eq("page_id", page["id"]).execute()
        
        for cf in cf_response.data:
            client_id = cf["client_id"]
            if client_id not in client_pages:
                client_pages[client_id] = []
            client_pages[client_id].append(page["ig_username"])
    
    # Get client details and show results
    print(f"\n{len(client_pages)} clients need rescaping:\n")
    
    for client_id, page_usernames in client_pages.items():
        client_response = client.table("clients").select(
            "ig_username"
        ).eq("id", client_id).execute()
        
        if client_response.data:
            client_username = client_response.data[0]["ig_username"]
            print(f"@{client_username}: {len(page_usernames)} pages with 0 followers")
            for username in page_usernames[:5]:  # Show first 5
                print(f"  - @{username}")
            if len(page_usernames) > 5:
                print(f"  ... and {len(page_usernames) - 5} more")
            print()

if __name__ == "__main__":
    main()

