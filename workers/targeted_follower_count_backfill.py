#!/usr/bin/env python3
"""
Targeted Follower Count Backfill Script

Scrapes follower counts ONLY for high-value pages:
- Hotlist pages (keyword match + uncategorized)
- Categorized pages (already reviewed)
- Pages with 2+ clients

This saves Apify credits by skipping low-value pages.
"""

import os
import sys
import time
from supabase import create_client, Client
from apify_client import ApifyClient

# Hotlist keywords
HOTLIST_KEYWORDS = [
    'hustl', 'afri', 'afro', 'black', 'melanin', 
    'blvck', 'culture', 'kulture', 'brown', 'noir', 'ebony'
]

def main():
    # Get credentials from command line args or environment
    supabase_url = sys.argv[1] if len(sys.argv) > 1 else os.getenv("SUPABASE_URL")
    supabase_key = sys.argv[2] if len(sys.argv) > 2 else os.getenv("SUPABASE_SERVICE_KEY")
    apify_token = sys.argv[3] if len(sys.argv) > 3 else os.getenv("APIFY_TOKEN")
    
    if not all([supabase_url, supabase_key, apify_token]):
        print("❌ Missing credentials!")
        print("Usage: python targeted_follower_count_backfill.py <supabase_url> <supabase_key> <apify_token>")
        sys.exit(1)
    
    print("🔧 Connecting to Supabase and Apify...")
    supabase: Client = create_client(supabase_url, supabase_key)
    apify = ApifyClient(apify_token)
    
    # Step 1: Find all pages needing follower counts
    print("\n📊 Finding pages with missing/zero follower counts...")
    
    pages = supabase.table("pages")\
        .select("id, ig_username, full_name, follower_count, client_count, category")\
        .or_("follower_count.is.null,follower_count.eq.0")\
        .execute()
    
    all_pages = pages.data or []
    print(f"   Found {len(all_pages):,} pages with missing/zero follower counts")
    
    # Step 2: Filter to high-value pages
    print("\n🎯 Filtering to high-value pages...")
    
    targeted_pages = []
    stats = {"hotlist": 0, "categorized": 0, "multi_client": 0}
    
    for page in all_pages:
        username = page.get("ig_username", "").lower()
        full_name = (page.get("full_name") or "").lower()
        client_count = page.get("client_count", 0)
        category = page.get("category")
        
        reasons = []
        
        # Check if hotlist (matches keywords AND not categorized)
        is_hotlist = (
            any(keyword in f"{username} {full_name}" for keyword in HOTLIST_KEYWORDS)
            and not category
        )
        if is_hotlist:
            reasons.append("hotlist")
            stats["hotlist"] += 1
        
        # Check if categorized
        if category:
            reasons.append(f"categorized ({category})")
            stats["categorized"] += 1
        
        # Check if 2+ clients
        if client_count >= 2:
            reasons.append(f"{client_count} clients")
            stats["multi_client"] += 1
        
        # Include if any criteria match
        if reasons:
            targeted_pages.append({
                "username": username,
                "reasons": reasons,
                "page": page
            })
    
    print(f"\n   ✅ {len(targeted_pages):,} high-value pages to scrape:")
    print(f"      • {stats['hotlist']:,} hotlist pages")
    print(f"      • {stats['categorized']:,} categorized pages")
    print(f"      • {stats['multi_client']:,} pages with 2+ clients")
    
    if not targeted_pages:
        print("\n✅ No pages need backfilling!")
        return
    
    # Step 3: Confirm
    print(f"\n⚠️  This will scrape {len(targeted_pages):,} profiles.")
    print(f"   📊 Estimated Apify cost: ~${len(targeted_pages) * 0.003:.2f} (at $0.003/profile)")
    print(f"   ⏱️  Processing time: ~{(len(targeted_pages) // 5) * 30 // 60} minutes")
    print(f"   📦 Using small batches (5 profiles) with 30-second delays to avoid blocks")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    # Step 4: Batch scrape with SMALL batches and delays
    print("\n🚀 Starting scrape...")
    batch_size = 5  # MUCH smaller batches to avoid Instagram blocks
    delay_between_batches = 30  # 30 seconds between batches
    total_updated = 0
    total_failed = 0
    
    for i in range(0, len(targeted_pages), batch_size):
        batch = targeted_pages[i:i + batch_size]
        usernames = [p["username"] for p in batch]
        batch_num = i//batch_size + 1
        total_batches = (len(targeted_pages)-1)//batch_size + 1
        
        try:
            print(f"\n📦 Batch {batch_num}/{total_batches}: {len(usernames)} profiles")
            
            # Use lightweight Instagram Profile Scraper
            run_input = {
                "usernames": usernames,
                "resultsLimit": len(usernames),
                "addParentData": False,  # Only get basic profile data
            }
            
            print(f"   ⏳ Scraping...")
            run = apify.actor("apify/instagram-profile-scraper").call(run_input=run_input)
            dataset = apify.dataset(run["defaultDatasetId"])
            
            # Update database
            batch_updated = 0
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
                supabase.table("pages")\
                    .update({"follower_count": follower_count})\
                    .eq("ig_username", username)\
                    .execute()
                
                batch_updated += 1
                total_updated += 1
                
                # Find and log reasons
                page_info = next((p for p in batch if p["username"] == username.lower()), None)
                if page_info:
                    reasons_str = ", ".join(page_info["reasons"])
                    print(f"      ✓ @{username}: {follower_count:,} followers ({reasons_str})")
            
            # Show what failed in this batch
            if batch_updated < len(usernames):
                failed_in_batch = len(usernames) - batch_updated
                total_failed += failed_in_batch
                print(f"      ⚠️  {failed_in_batch} profiles couldn't be scraped in this batch")
            
            print(f"   ✅ Updated {batch_updated}/{len(usernames)} pages in this batch")
            print(f"   📊 Total progress: {total_updated}/{len(targeted_pages)} ({100*total_updated//len(targeted_pages) if len(targeted_pages) > 0 else 0}%)")
            
            # Delay between batches to avoid rate limiting
            if i + batch_size < len(targeted_pages):
                print(f"   ⏸️  Waiting {delay_between_batches}s before next batch...")
                time.sleep(delay_between_batches)
            
        except Exception as e:
            print(f"   ❌ Batch failed: {e}")
            total_failed += len(usernames)
            
            # Still delay even on failure
            if i + batch_size < len(targeted_pages):
                print(f"   ⏸️  Waiting {delay_between_batches}s before next batch...")
                time.sleep(delay_between_batches)
            continue
    
    print(f"\n✅ Backfill complete!")
    print(f"   • Successfully updated: {total_updated:,} pages")
    print(f"   • Failed: {total_failed:,} pages")
    if (total_updated + total_failed) > 0:
        print(f"   • Success rate: {100*total_updated//(total_updated+total_failed)}%")

if __name__ == "__main__":
    main()

