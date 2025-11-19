"""Quick test script to scrape a single client from terminal"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        elif hasattr(sys.stdout, 'encoding'):
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass

from main import IGFollowerAnalyzer

# Load token from config or environment
apify_token = os.environ.get("APIFY_TOKEN")
if not apify_token:
    try:
        import config
        apify_token = getattr(config, 'APIFY_TOKEN', None)
    except ImportError:
        pass

if not apify_token:
    print("❌ APIFY_TOKEN not found! Set it in environment or config.py")
    sys.exit(1)

# Test scraping
username = "kobe5starqb1"
print(f"Testing scrape for @{username}...")
print("=" * 50)

analyzer = IGFollowerAnalyzer(apify_token, "dummy")

# Try with validation skipped (like Streamlit does)
print("\n🔍 Attempting scrape (validation skipped)...")
result = analyzer.scrape_client_following(username, validate_first=False)

if result:
    print(f"\n✅ SUCCESS! Scraped {len(result)} accounts")
    print(f"   First few accounts: {[acc.get('username') for acc in result[:5]]}")
else:
    print("\n❌ FAILED - Could not scrape")
    print("   This matches the Streamlit behavior")

