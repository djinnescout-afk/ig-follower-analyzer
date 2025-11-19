"""
Railway scraper service - runs scraping on Railway instead of local machine
Can be triggered via Railway CLI or scheduled jobs
"""

import os
import sys
from scrape_profiles import priority_scrape, scrape_all, re_scrape_priority, re_scrape_all

if __name__ == "__main__":
    # Check for mode from environment variable or command line
    scrape_mode = os.environ.get("SCRAPE_MODE", "").lower()
    
    if not scrape_mode and len(sys.argv) > 1:
        scrape_mode = sys.argv[1].lower()
    
    if scrape_mode in ["priority", "1"]:
        print("🚀 Starting Priority Scrape on Railway...")
        priority_scrape()
    elif scrape_mode in ["all", "2"]:
        print("🚀 Starting Full Scrape on Railway...")
        scrape_all()
    elif scrape_mode in ["re-scrape-priority", "3", "re-scrape-priority"]:
        print("🚀 Starting Re-scrape Priority on Railway...")
        re_scrape_priority()
    elif scrape_mode in ["re-scrape-all", "4", "re-scrape-all"]:
        print("🚀 Starting Re-scrape All on Railway...")
        re_scrape_all()
    else:
        print("Usage: python railway_scraper.py [priority|all|re-scrape-priority|re-scrape-all]")
        print("\nModes:")
        print("  priority          - Fast scrape (Tiers 1-3: hotlist + 2+ clients)")
        print("  all               - Full scrape (all tiers, overnight run)")
        print("  re-scrape-priority - Force re-scrape priority pages (Tiers 1-3)")
        print("  re-scrape-all     - Force re-scrape all pages")
        print("\nOr set SCRAPE_MODE environment variable")
        sys.exit(1)

