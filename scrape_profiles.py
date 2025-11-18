"""
Script to pre-scrape Instagram profile data for all pages
Stores profile pictures, bios, and recent posts for use in Streamlit app
"""

import json
import os
import sys
import time
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from categorizer import InstagramCategorizer, CATEGORIES

# Hotlist keywords for priority categorization (same as categorize_app.py)
# Note: Uses partial matching - "black" matches "blacksuccess", "hustl" matches "hustlersimage"
HOTLIST_KEYWORDS = [
    "hustl",      # Matches: hustlersimage, hustlingquiet, etc.
    "afri",       # Matches: african, afro-american, etc.
    "afro",       # Matches: afro-american, etc.
    "black",      # Matches: blacksuccess, blackbillionaire, etc.
    "melanin",    # Matches: melaninmagic, melaninpoppin, etc.
    "blvck",      # Alternative spelling of black
    "culture",    # Matches: culture, cultural, etc.
    "kulture",    # Alternative spelling of culture
    "brown",      # Matches: brownskin, brownbeauty, brownsuccess, etc.
    "noir",       # French for black, used in some contexts
    "ebony"       # Another term for black/dark
]

# Failure tracking constants
CONSECUTIVE_FAILURE_THRESHOLD = 5  # After 5 consecutive failures, mark as long-term failed
LONG_TERM_FAILURE_RETRY_DAYS = 30   # Retry long-term failed pages after 30 days

# Try to load API tokens from config or environment
def load_tokens():
    apify_token = os.environ.get("APIFY_TOKEN")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    if not apify_token or not openai_key:
        try:
            import config
            if not apify_token:
                apify_token = getattr(config, 'APIFY_TOKEN', None)
            if not openai_key:
                openai_key = getattr(config, 'OPENAI_API_KEY', None)
        except ImportError:
            pass
    
    if not apify_token:
        print("❌ APIFY_TOKEN not found! Set it in environment or config.py")
        sys.exit(1)
    
    if not openai_key:
        print("⚠️  OPENAI_API_KEY not found, but continuing (not needed for scraping)")
    
    return apify_token, openai_key


def matches_hotlist(page_data: Dict) -> bool:
    """Check if page matches hotlist keywords"""
    username = page_data.get("username", "").lower()
    full_name = page_data.get("full_name", "").lower()
    text = f"{username} {full_name}"
    
    return any(keyword.lower() in text for keyword in HOTLIST_KEYWORDS)


def prioritize_pages(pages: Dict, pages_to_scrape: List[str]) -> Tuple[List[Tuple[str, Dict, int]], Dict[str, int]]:
    """
    Sort pages into priority tiers
    
    Returns:
        - List of (username, page_data, tier) tuples sorted by priority
        - Dictionary of tier counts for reporting
    """
    tier_1 = []  # 2+ clients AND hotlist
    tier_2 = []  # Hotlist only (but not 2+ clients)
    tier_3 = []  # 2+ clients only (but not hotlist)
    tier_4 = []  # Everything else
    
    for username in pages_to_scrape:
        page_data = pages[username]
        client_count = len(page_data.get("clients_following", []))
        is_hotlist = matches_hotlist(page_data)
        
        if client_count >= 2 and is_hotlist:
            tier_1.append((username, page_data, 1))
        elif is_hotlist:
            tier_2.append((username, page_data, 2))
        elif client_count >= 2:
            tier_3.append((username, page_data, 3))
        else:
            tier_4.append((username, page_data, 4))
    
    # Combine in priority order
    prioritized = tier_1 + tier_2 + tier_3 + tier_4
    
    tier_counts = {
        "Tier 1 (2+ clients + hotlist)": len(tier_1),
        "Tier 2 (hotlist only)": len(tier_2),
        "Tier 3 (2+ clients only)": len(tier_3),
        "Tier 4 (others)": len(tier_4)
    }
    
    return prioritized, tier_counts


def scrape_pages(data: Dict, prioritized_list: List[Tuple[str, Dict, int]], data_file: str, mode: str = "all"):
    """Core scraping logic shared by both priority_scrape and scrape_all"""
    
    apify_token, openai_key = load_tokens()
    categorizer = InstagramCategorizer(apify_token, openai_key or "dummy")
    
    pages = data.get("pages", {})
    total = len(prioritized_list)
    successful = 0
    failed = 0
    failed_pages = []  # Track which pages failed
    current_tier = None
    
    print(f"\n📊 Starting {mode} scrape: {total} pages")
    print("=" * 60)
    
    for i, (username, page_data, tier) in enumerate(prioritized_list, 1):
        # Show tier transitions
        if tier != current_tier:
            current_tier = tier
            tier_names = {
                1: "Tier 1: 2+ clients + hotlist",
                2: "Tier 2: Hotlist only",
                3: "Tier 3: 2+ clients only",
                4: "Tier 4: Others"
            }
            print(f"\n🔥 {tier_names[tier]}\n")
        
        print(f"[{i}/{total}] Scraping @{username}...")
        
        try:
            profile_data = categorizer.scrape_page_content(username)
            
            if profile_data and profile_data.get("profile_pic_url"):
                # Store in the page's profile_data field
                pages[username]["profile_data"] = {
                    "profile_pic_url": profile_data.get("profile_pic_url", ""),
                    "profile_pic_base64": profile_data.get("profile_pic_base64"),  # Base64 encoded (doesn't expire)
                    "profile_pic_mime_type": profile_data.get("profile_pic_mime_type"),
                    "bio": profile_data.get("bio", ""),
                    "posts": profile_data.get("posts", []),  # Posts include image_base64 and image_mime_type
                    "follower_count": profile_data.get("follower_count", 0),
                    "full_name": profile_data.get("full_name", ""),
                    "is_verified": profile_data.get("is_verified", False),
                    "scraped_at": profile_data.get("scraped_at") or datetime.now().isoformat(),
                    "promo_status": profile_data.get("promo_status", "Unknown"),
                    "promo_indicators": profile_data.get("promo_indicators", []),
                    "website_url": profile_data.get("website_url"),
                    "website_promo_info": profile_data.get("website_promo_info"),
                    "failed": False,  # Mark as successful
                    "consecutive_failures": 0  # Reset failure counter on success
                }
                
                # Also update follower count if it changed
                if profile_data.get("follower_count"):
                    pages[username]["follower_count"] = profile_data["follower_count"]
                
                # Update promo status and indicators from scraped data
                if profile_data.get("promo_status"):
                    pages[username]["promo_status"] = profile_data["promo_status"]
                if profile_data.get("promo_indicators"):
                    pages[username]["promo_indicators"] = profile_data["promo_indicators"]
                
                # Update website URL from scraped data
                if profile_data.get("website_url"):
                    pages[username]["website_url"] = profile_data["website_url"]
                
                # Update website promo info from scraped data
                if profile_data.get("website_promo_info"):
                    pages[username]["website_promo_info"] = profile_data["website_promo_info"]
                
                successful += 1
                print(f"  ✅ Success! Got {len(profile_data.get('posts', []))} posts")
            else:
                # Get current consecutive failure count
                existing_data = pages[username].get("profile_data", {})
                consecutive_failures = existing_data.get("consecutive_failures", 0) + 1
                
                # Mark as failed
                failure_data = {
                    "failed": True,
                    "last_attempt": datetime.now().isoformat(),
                    "error": "No profile data or profile picture returned",
                    "consecutive_failures": consecutive_failures
                }
                
                # Check if we've hit the threshold for long-term failure
                if consecutive_failures >= CONSECUTIVE_FAILURE_THRESHOLD:
                    failure_data["long_term_failed"] = True
                    pages[username]["profile_data"] = failure_data
                    failed += 1
                    failed_pages.append(username)
                    print(f"  ❌ Failed to scrape (long-term failure - will retry after 30 days)")
                else:
                    pages[username]["profile_data"] = failure_data
                    failed += 1
                    failed_pages.append(username)
                    print(f"  ❌ Failed to scrape (failure {consecutive_failures}/{CONSECUTIVE_FAILURE_THRESHOLD} - will retry after 1 hour)")
        
        except Exception as e:
            # Get current consecutive failure count
            existing_data = pages[username].get("profile_data", {})
            consecutive_failures = existing_data.get("consecutive_failures", 0) + 1
            
            # Mark as failed
            failure_data = {
                "failed": True,
                "last_attempt": datetime.now().isoformat(),
                "error": str(e)[:200],
                "consecutive_failures": consecutive_failures
            }
            
            # Check if we've hit the threshold for long-term failure
            if consecutive_failures >= CONSECUTIVE_FAILURE_THRESHOLD:
                failure_data["long_term_failed"] = True
                pages[username]["profile_data"] = failure_data
                failed += 1
                failed_pages.append(username)
                print(f"  ❌ Error: {str(e)[:100]} (long-term failure - will retry after 30 days)")
            else:
                pages[username]["profile_data"] = failure_data
                failed += 1
                failed_pages.append(username)
                print(f"  ❌ Error: {str(e)[:100]} (failure {consecutive_failures}/{CONSECUTIVE_FAILURE_THRESHOLD} - will retry after 1 hour)")
        
        # Save progress every 10 pages
        if i % 10 == 0:
            data["pages"] = pages
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  💾 Progress saved...")
        
        # Small delay to avoid rate limits
        if i < total:
            time.sleep(2)
    
    # Final save
    data["pages"] = pages
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Done! Scraped {successful} pages successfully, {failed} failed")
    
    # List failed pages if any
    if failed_pages:
        failed_list = ", ".join([f"@{username}" for username in failed_pages])
        print(f"❌ Failures: {failed_list}")
    
    print(f"💾 Data saved to {data_file}")


def priority_scrape(data_file: str = "clients_data.json"):
    """Scrape only high-priority pages (Tiers 1-3): 2+ clients, hotlist, or both"""
    
    # Load existing data
    if not os.path.exists(data_file):
        print(f"❌ {data_file} not found! Run main.py first to add clients.")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages = data.get("pages", {})
    total = len(pages)
    
    # Find pages that need scraping
    # Skip pages that failed recently (within last 24 hours) to avoid infinite retries
    pages_to_scrape = []
    for username, page_data in pages.items():
        profile_data = page_data.get("profile_data")
        
        # Skip if already successfully scraped AND has base64 images (new format)
        # Re-scrape if missing base64 images (old format needs update)
        if profile_data and profile_data.get("profile_pic_url"):
            # Check if it has base64 images (new format)
            if profile_data.get("profile_pic_base64"):
                continue  # Already has base64, skip
            # Otherwise, re-scrape to get base64 images
        
        # Skip if failed recently (within 1 hour) to avoid retrying too quickly
        # Note: Reduced from 24h since failures are often temporary Instagram blocking
        if profile_data and profile_data.get("failed"):
            # Check if it's a long-term failure (many consecutive failures)
            if profile_data.get("long_term_failed"):
                last_attempt = profile_data.get("last_attempt")
                if last_attempt:
                    try:
                        attempt_time = datetime.fromisoformat(last_attempt)
                        if datetime.now() - attempt_time < timedelta(days=LONG_TERM_FAILURE_RETRY_DAYS):
                            continue  # Skip - long-term failed, retry after 30 days
                    except:
                        pass  # Invalid timestamp, try again
            else:
                # Regular failure - retry after 1 hour
                last_attempt = profile_data.get("last_attempt")
                if last_attempt:
                    try:
                        attempt_time = datetime.fromisoformat(last_attempt)
                        if datetime.now() - attempt_time < timedelta(hours=1):
                            continue  # Skip - failed recently (retry after 1 hour)
                    except:
                        pass  # Invalid timestamp, try again
        
        pages_to_scrape.append(username)
    
    if not pages_to_scrape:
        print("✅ All pages already have profile data!")
        return
    
    # Prioritize pages
    prioritized, tier_counts = prioritize_pages(pages, pages_to_scrape)
    
    # Filter to only Tiers 1-3 (high priority)
    priority_pages = [(u, p, t) for u, p, t in prioritized if t <= 3]
    
    if not priority_pages:
        print("✅ No high-priority pages need scraping!")
        print("\nTier breakdown:")
        for tier_name, count in tier_counts.items():
            print(f"  {tier_name}: {count} pages")
        return
    
    print(f"📊 Found {len(priority_pages)} high-priority pages to scrape (out of {len(pages_to_scrape)} total)")
    print("\nTier breakdown:")
    for tier_name, count in tier_counts.items():
        print(f"  {tier_name}: {count} pages")
    print(f"\n⏳ Scraping high-priority pages only (Tiers 1-3)...\n")
    
    # Reload data to get fresh copy
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scrape_pages(data, priority_pages, data_file, mode="priority")


def scrape_all(data_file: str = "clients_data.json"):
    """Scrape all pages that need profile data (all tiers) - for overnight runs"""
    
    # Load existing data
    if not os.path.exists(data_file):
        print(f"❌ {data_file} not found! Run main.py first to add clients.")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages = data.get("pages", {})
    total = len(pages)
    
    # Find pages that need scraping
    # Skip pages that failed recently (within last 24 hours) to avoid infinite retries
    pages_to_scrape = []
    for username, page_data in pages.items():
        profile_data = page_data.get("profile_data")
        
        # Skip if already successfully scraped AND has base64 images (new format)
        # Re-scrape if missing base64 images (old format needs update)
        if profile_data and profile_data.get("profile_pic_url"):
            # Check if it has base64 images (new format)
            if profile_data.get("profile_pic_base64"):
                continue  # Already has base64, skip
            # Otherwise, re-scrape to get base64 images
        
        # Skip if failed recently (within 1 hour) to avoid retrying too quickly
        # Note: Reduced from 24h since failures are often temporary Instagram blocking
        if profile_data and profile_data.get("failed"):
            # Check if it's a long-term failure (many consecutive failures)
            if profile_data.get("long_term_failed"):
                last_attempt = profile_data.get("last_attempt")
                if last_attempt:
                    try:
                        attempt_time = datetime.fromisoformat(last_attempt)
                        if datetime.now() - attempt_time < timedelta(days=LONG_TERM_FAILURE_RETRY_DAYS):
                            continue  # Skip - long-term failed, retry after 30 days
                    except:
                        pass  # Invalid timestamp, try again
            else:
                # Regular failure - retry after 1 hour
                last_attempt = profile_data.get("last_attempt")
                if last_attempt:
                    try:
                        attempt_time = datetime.fromisoformat(last_attempt)
                        if datetime.now() - attempt_time < timedelta(hours=1):
                            continue  # Skip - failed recently (retry after 1 hour)
                    except:
                        pass  # Invalid timestamp, try again
        
        pages_to_scrape.append(username)
    
    if not pages_to_scrape:
        print("✅ All pages already have profile data!")
        return
    
    # Prioritize pages
    prioritized, tier_counts = prioritize_pages(pages, pages_to_scrape)
    
    print(f"📊 Found {len(prioritized)} pages to scrape (out of {total} total)")
    print("\nTier breakdown:")
    for tier_name, count in tier_counts.items():
        print(f"  {tier_name}: {count} pages")
    print(f"\n⏳ This may take a while (overnight run)...\n")
    
    # Reload data to get fresh copy
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scrape_pages(data, prioritized, data_file, mode="all")


def re_scrape_priority(data_file: str = "clients_data.json"):
    """Force re-scrape only high-priority pages (Tiers 1-3), even if they already have profile data"""
    
    # Load existing data
    if not os.path.exists(data_file):
        print(f"❌ {data_file} not found! Run main.py first to add clients.")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages = data.get("pages", {})
    total = len(pages)
    
    if total == 0:
        print("❌ No pages found! Run main.py first to add clients.")
        return
    
    # Get priority pages (Tiers 1-3: 2+ clients, hotlist, or both)
    # Force re-scrape even if they already have base64 images
    pages_to_scrape = []
    for username, page_data in pages.items():
        profile_data = page_data.get("profile_data")
        
        # Only skip if it's a long-term failure (permanently failed)
        # Regular failures and already-scraped pages will be re-scraped
        if profile_data and profile_data.get("failed") and profile_data.get("long_term_failed"):
            last_attempt = profile_data.get("last_attempt")
            if last_attempt:
                try:
                    attempt_time = datetime.fromisoformat(last_attempt)
                    if datetime.now() - attempt_time < timedelta(days=LONG_TERM_FAILURE_RETRY_DAYS):
                        continue  # Skip only long-term failures that haven't passed retry period
                except:
                    pass  # Invalid timestamp, try again
        
        pages_to_scrape.append(username)
    
    if not pages_to_scrape:
        print("✅ No pages to re-scrape (all are long-term failed)")
        return
    
    # Prioritize pages and filter to only Tiers 1-3
    prioritized, tier_counts = prioritize_pages(pages, pages_to_scrape)
    
    # Filter to only priority tiers (1, 2, 3)
    priority_pages = [(u, d, t) for u, d, t in prioritized if t <= 3]
    
    if not priority_pages:
        print("✅ No priority pages found to re-scrape")
        return
    
    # Count priority tiers
    priority_tier_counts = {
        "Tier 1 (2+ clients + hotlist)": len([p for p in priority_pages if p[2] == 1]),
        "Tier 2 (hotlist only)": len([p for p in priority_pages if p[2] == 2]),
        "Tier 3 (2+ clients only)": len([p for p in priority_pages if p[2] == 3])
    }
    
    print(f"🔄 Re-scraping {len(priority_pages)} priority pages (force update)...")
    print("   This will update base64 images and refresh profile data for Tiers 1-3")
    print("   (Skipping only long-term failed pages that haven't passed 30-day retry period)")
    print(f"\n⏳ This may take a while...\n")
    
    print(f"📊 Priority pages to re-scrape: {len(priority_pages)}")
    print("\nTier breakdown:")
    for tier_name, count in priority_tier_counts.items():
        print(f"  {tier_name}: {count} pages")
    print()
    
    # Reload data to get fresh copy
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scrape_pages(data, priority_pages, data_file, mode="re-scrape-priority")


def re_scrape_all(data_file: str = "clients_data.json"):
    """Force re-scrape ALL pages, even if they already have profile data or failed recently"""
    
    # Load existing data
    if not os.path.exists(data_file):
        print(f"❌ {data_file} not found! Run main.py first to add clients.")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages = data.get("pages", {})
    total = len(pages)
    
    if total == 0:
        print("❌ No pages found! Run main.py first to add clients.")
        return
    
    # Get ALL pages (no skipping - force re-scrape everything)
    # Only skip long-term failures (permanently failed pages)
    pages_to_scrape = []
    for username, page_data in pages.items():
        profile_data = page_data.get("profile_data")
        
        # Only skip if it's a long-term failure (permanently failed)
        # Regular failures and already-scraped pages will be re-scraped
        if profile_data and profile_data.get("failed") and profile_data.get("long_term_failed"):
            last_attempt = profile_data.get("last_attempt")
            if last_attempt:
                try:
                    attempt_time = datetime.fromisoformat(last_attempt)
                    if datetime.now() - attempt_time < timedelta(days=LONG_TERM_FAILURE_RETRY_DAYS):
                        continue  # Skip only long-term failures that haven't passed retry period
                except:
                    pass  # Invalid timestamp, try again
        
        pages_to_scrape.append(username)
    
    if not pages_to_scrape:
        print("✅ No pages to re-scrape (all are long-term failed)")
        return
    
    print(f"🔄 Re-scraping {len(pages_to_scrape)} pages (force update)...")
    print("   This will update base64 images and refresh all profile data")
    print("   (Skipping only long-term failed pages that haven't passed 30-day retry period)")
    print(f"\n⏳ This may take a while...\n")
    
    # Prioritize pages (still prioritize, but scrape all)
    prioritized, tier_counts = prioritize_pages(pages, pages_to_scrape)
    
    print(f"📊 Pages to re-scrape: {len(prioritized)}")
    print("\nTier breakdown:")
    for tier_name, count in tier_counts.items():
        print(f"  {tier_name}: {count} pages")
    print()
    
    # Reload data to get fresh copy
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scrape_pages(data, prioritized, data_file, mode="re-scrape")


if __name__ == "__main__":
    # Check for environment variable (for Railway/non-interactive mode)
    scrape_mode = os.environ.get("SCRAPE_MODE", "").lower()
    
    if scrape_mode in ["priority", "1"]:
        priority_scrape()
    elif scrape_mode in ["all", "2"]:
        scrape_all()
    else:
        # Interactive mode
        print("=" * 60)
        print("📸 Instagram Profile Scraper")
        print("=" * 60)
        print("\n🎯 PURPOSE:")
        print("   Pre-scrapes profile data (pics, bios, posts) for Streamlit categorization app")
        print("   This data is REQUIRED before using: streamlit run categorize_app.py")
        print("\n💡 RECOMMENDED:")
        print("   • Start with Priority Scrape (fast, gets hotlist pages first)")
        print("   • Then run Scrape All overnight for complete data")
        print("\n" + "=" * 60)
        print("\nChoose an option:")
        print("  1. Priority Scrape (Fast - Tiers 1-3: hotlist + 2+ clients)")
        print("  2. Scrape All (Complete - All tiers, overnight run)")
        print("  3. Re-scrape Priority (Force update - Re-scrapes Tiers 1-3, including those with base64)")
        print("  4. Re-scrape All (Force update - Re-scrapes ALL pages, including those with base64)")
        print("  5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            priority_scrape()
        elif choice == "2":
            scrape_all()
        elif choice == "3":
            re_scrape_priority()
        elif choice == "4":
            re_scrape_all()
        elif choice == "5":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Exiting.")
            sys.exit(1)
