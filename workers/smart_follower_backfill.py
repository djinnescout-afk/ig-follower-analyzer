#!/usr/bin/env python3
"""
Smart Follower Count Backfill Script

Instead of directly scraping profiles (which gets rate limited),
this queues client re-scrapes. When clients get re-scraped, their
following lists update all page follower counts automatically!

This uses the RELIABLE louisdeconinck/instagram-following-scraper
that we already trust and that works great.
"""

import os
import sys
from supabase import create_client, Client

# Hotlist keywords
HOTLIST_KEYWORDS = [
    'hustl', 'afri', 'afro', 'black', 'melanin', 
    'blvck', 'culture', 'kulture', 'brown', 'noir', 'ebony'
]

def main():
    # Get credentials from command line args or environment
    supabase_url = sys.argv[1] if len(sys.argv) > 1 else os.getenv("SUPABASE_URL")
    supabase_key = sys.argv[2] if len(sys.argv) > 2 else os.getenv("SUPABASE_SERVICE_KEY")
    
    if not all([supabase_url, supabase_key]):
        print("❌ Missing credentials!")
        print("Usage: python smart_follower_backfill.py <supabase_url> <supabase_key>")
        sys.exit(1)
    
    print("🔧 Connecting to Supabase...")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Step 1: Find high-value pages with missing/zero follower counts
    print("\n📊 Finding high-value pages with missing follower counts...")
    
    pages = supabase.table("pages")\
        .select("id, ig_username, full_name, follower_count, client_count, category")\
        .or_("follower_count.is.null,follower_count.eq.0")\
        .execute()
    
    all_pages = pages.data or []
    print(f"   Found {len(all_pages):,} pages with missing/zero follower counts")
    
    # Step 2: Filter to high-value pages
    print("\n🎯 Filtering to high-value pages...")
    
    targeted_page_ids = []
    stats = {"hotlist": 0, "categorized": 0, "multi_client": 0}
    
    for page in all_pages:
        username = page.get("ig_username", "").lower()
        full_name = (page.get("full_name") or "").lower()
        client_count = page.get("client_count", 0)
        category = page.get("category")
        
        # Check if hotlist (matches keywords AND not categorized)
        is_hotlist = (
            any(keyword in f"{username} {full_name}" for keyword in HOTLIST_KEYWORDS)
            and not category
        )
        
        # Check if categorized
        is_categorized = bool(category)
        
        # Check if 2+ clients
        has_multiple_clients = client_count >= 2
        
        # Include if any criteria match
        if is_hotlist or is_categorized or has_multiple_clients:
            targeted_page_ids.append(page["id"])
            if is_hotlist:
                stats["hotlist"] += 1
            if is_categorized:
                stats["categorized"] += 1
            if has_multiple_clients:
                stats["multi_client"] += 1
    
    print(f"\n   ✅ {len(targeted_page_ids):,} high-value pages need follower counts:")
    print(f"      • {stats['hotlist']:,} hotlist pages")
    print(f"      • {stats['categorized']:,} categorized pages")
    print(f"      • {stats['multi_client']:,} pages with 2+ clients")
    
    if not targeted_page_ids:
        print("\n✅ No pages need backfilling!")
        return
    
    # Step 3: Find clients that follow these pages
    print(f"\n🔍 Finding clients that follow these {len(targeted_page_ids)} pages...")
    
    # Query in batches
    batch_size = 100
    client_ids = set()
    
    for i in range(0, len(targeted_page_ids), batch_size):
        batch = targeted_page_ids[i:i + batch_size]
        
        relationships = supabase.table("client_following")\
            .select("client_id")\
            .in_("page_id", batch)\
            .execute()
        
        for rel in (relationships.data or []):
            client_ids.add(rel["client_id"])
    
    print(f"   Found {len(client_ids)} clients that follow these pages")
    
    if not client_ids:
        print("   ⚠️  No clients follow these pages - can't update via re-scrape")
        print("   💡 These pages might be orphaned or only manually added")
        return
    
    # Step 4: Get client details
    print(f"\n📋 Getting client details...")
    
    clients = supabase.table("clients")\
        .select("id, ig_username, full_name")\
        .in_("id", list(client_ids))\
        .execute()
    
    clients_data = clients.data or []
    print(f"   Found {len(clients_data)} clients")
    
    # Step 5: Confirm and queue
    print(f"\n⚠️  This will queue {len(clients_data)} client re-scrapes.")
    print(f"   💰 Cost: ~${len(clients_data) * 0.01:.2f} (at ~$0.01 per client following list)")
    print(f"   ⏱️  Time: Will be processed by worker over next ~{len(clients_data)} minutes")
    print(f"   ✨ Benefit: Updates ALL pages these clients follow (not just the {len(targeted_page_ids)} target pages)")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    print(f"\n🚀 Queuing client re-scrapes...")
    
    queued = 0
    skipped = 0
    
    for client in clients_data:
        # Check if already has pending/running scrape
        existing = supabase.table("scrape_runs")\
            .select("id")\
            .eq("client_id", client["id"])\
            .eq("scrape_type", "client_following")\
            .in_("status", ["pending", "running"])\
            .execute()
        
        if existing.data:
            print(f"   ⏭️  Skipping @{client['ig_username']}: already has pending scrape")
            skipped += 1
            continue
        
        # Queue scrape
        supabase.table("scrape_runs").insert({
            "client_id": client["id"],
            "scrape_type": "client_following",
            "status": "pending",
            "priority": 5,  # High priority
        }).execute()
        
        queued += 1
        print(f"      ✓ Queued @{client['ig_username']}")
    
    print(f"\n{'='*60}")
    print(f"✅ Queued {queued} client scrapes!")
    if skipped > 0:
        print(f"   ⏭️  Skipped {skipped} clients (already pending)")
    
    print(f"\n📋 What happens next:")
    print(f"   1. client_following_worker processes these jobs")
    print(f"   2. For each client, scrapes their following list")
    print(f"   3. Updates follower counts for ALL pages they follow")
    print(f"   4. This uses the RELIABLE louisdeconinck actor")
    print(f"\n💡 Why this works:")
    print(f"   • No Instagram rate limiting (proven reliable)")
    print(f"   • Updates more pages than just the targets (bonus!)")
    print(f"   • Uses the scraping method we already trust")

if __name__ == "__main__":
    main()

