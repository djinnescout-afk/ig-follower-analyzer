"""
Quick test script to categorize a single page
Usage: python test_single_page.py username
"""
import sys
import os
from categorizer import InstagramCategorizer

def test_single_page(username: str):
    """Test categorization on a single page"""
    apify_token = os.environ.get("APIFY_TOKEN")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    # Try loading from config.py if not in environment
    if not apify_token or not openai_key:
        try:
            import config
            if not apify_token:
                apify_token = getattr(config, 'APIFY_TOKEN', None)
            if not openai_key:
                openai_key = getattr(config, 'OPENAI_API_KEY', None)
        except ImportError:
            pass  # config.py doesn't exist, that's okay
    
    if not apify_token:
        print("❌ APIFY_TOKEN not set!")
        print("   Set it in config.py or as environment variable")
        return
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not set!")
        print("   Set it in config.py or as environment variable")
        return
    
    print(f"🧪 Testing categorization for @{username}")
    print("="*60)
    
    categorizer = InstagramCategorizer(apify_token, openai_key)
    
    result = categorizer.categorize_page(username)
    
    if result:
        print("\n✅ CATEGORIZATION RESULT:")
        print("="*60)
        print(f"Username: @{username}")
        print(f"Category: {result['category']}")
        print(f"Confidence: {result['category_confidence']*100:.0f}%")
        print(f"Contact Email: {result['contact_email'] or 'Not found'}")
        print(f"Promo Status: {result['promo_status']}")
        if result['promo_indicators']:
            print(f"Promo Indicators: {', '.join(result['promo_indicators'])}")
    else:
        print(f"\n❌ Failed to categorize @{username}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_single_page.py <username>")
        print("Example: python test_single_page.py blacksuccesslive")
        sys.exit(1)
    
    username = sys.argv[1].lstrip('@')
    test_single_page(username)

