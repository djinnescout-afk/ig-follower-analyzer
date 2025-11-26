#!/usr/bin/env python3
"""
Check if a specific page has followers in the database.
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
    page_id = "8bd77b51-e87a-4c45-aa4c-c92533b73edd"  # blackalchemysolutions
    
    client = get_supabase_client()
    
    # Get page details
    print(f"Checking page {page_id}...")
    page_response = client.table("pages").select("id, ig_username, client_count").eq("id", page_id).execute()
    
    if not page_response.data:
        print("❌ Page not found!")
        return
    
    page = page_response.data[0]
    print(f"✓ Page found: @{page['ig_username']}, client_count: {page['client_count']}")
    
    # Get client_following records
    print("\nChecking client_following records...")
    cf_response = client.table("client_following").select("client_id, page_id").eq("page_id", page_id).execute()
    
    if not cf_response.data:
        print("❌ No client_following records found!")
        return
    
    print(f"✓ Found {len(cf_response.data)} client_following records:")
    for cf in cf_response.data:
        print(f"  - client_id: {cf['client_id']}")
        
        # Get client details
        client_response = client.table("clients").select("id, ig_username, full_name").eq("id", cf["client_id"]).execute()
        
        if client_response.data:
            c = client_response.data[0]
            print(f"    → @{c['ig_username']} ({c.get('full_name', 'No name')})")
        else:
            print(f"    → ❌ Client not found in clients table!")

if __name__ == "__main__":
    main()

