"""
Example usage of the Instagram Follower Analyzer
This demonstrates how to use the tool programmatically
"""

import os
from main import IGFollowerAnalyzer

# Set your Apify token (or set as environment variable)
# os.environ["APIFY_TOKEN"] = "your_token_here"

# Or import from config file
try:
    from config import APIFY_TOKEN
    os.environ["APIFY_TOKEN"] = APIFY_TOKEN
except ImportError:
    pass

# Initialize the analyzer
analyzer = IGFollowerAnalyzer(os.environ.get("APIFY_TOKEN"))

# Example 1: Add multiple clients
print("=== Adding Clients ===")
clients = [
    ("John Doe", "johndoe"),
    ("Jane Smith", "janesmith"),
    ("Bob Wilson", "bobwilson123"),
]

for name, username in clients:
    analyzer.add_client(name, username)

# Example 2: Scrape a specific client's following list
print("\n=== Scraping Client ===")
try:
    analyzer.scrape_client_following("johndoe")
except Exception as e:
    print(f"Note: {e}")
    print("(This will work once you have a valid Apify token)")

# Example 3: Get cross-referenced pages (pages followed by 2+ clients)
print("\n=== Cross-Referenced Pages ===")
pages = analyzer.get_cross_referenced_pages(min_clients=2)
for page in pages[:5]:  # Top 5
    print(f"@{page['username']}: {page['clients_following']} clients, {page['total_followers']:,} followers")

# Example 4: Add pricing for a page
print("\n=== Adding Prices ===")
if pages:
    example_page = pages[0]['username']
    analyzer.add_promo_price(example_page, 299.99)

# Example 5: Get ROI analysis
print("\n=== ROI Analysis ===")
roi_pages = analyzer.calculate_roi_metrics(min_clients=2)
for page in roi_pages[:3]:  # Top 3 best value
    print(f"\n@{page['username']}")
    print(f"  Value Score: {page['concentration_per_dollar']:.2e}")
    print(f"  Cost per client: ${page['cost_per_client']:.2f}")

# Example 6: Generate full report
print("\n=== Full Analysis Report ===")
analyzer.print_analysis_report(min_clients=2)

# Example 7: Export to CSV
print("\n=== Exporting ===")
analyzer.export_to_csv("my_analysis.csv")



