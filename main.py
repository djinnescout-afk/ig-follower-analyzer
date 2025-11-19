"""
Instagram Follower Analyzer for Coaching Business
Analyzes which pages your clients follow to identify high-value promotional opportunities
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import requests
from apify_client import ApifyClient
from categorizer import InstagramCategorizer, CATEGORIES

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        elif hasattr(sys.stdout, 'encoding'):
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass  # Fallback to default encoding


class IGFollowerAnalyzer:
    def __init__(self, apify_token: str, openai_api_key: str = None, data_file: str = None):
        """Initialize with Apify API token, optional OpenAI key, and optional custom data file"""
        self.apify_token = apify_token  # Store token for categorizer
        self.client = ApifyClient(apify_token)
        self.data_file = data_file or "clients_data.json"
        self.clients_data = self.load_data()
        self.openai_api_key = openai_api_key
        self._categorizer = None
    
    def load_data(self) -> Dict:
        """Load existing client data from JSON file"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "clients": {},
            "pages": {},
            "last_updated": None
        }
    
    def save_data(self, sync_remote: bool = False, sync_reason: Optional[str] = None, silent_sync: bool = False):
        """Save client data to JSON file and optionally sync to Railway"""
        self.clients_data["last_updated"] = datetime.now().isoformat()
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.clients_data, f, indent=2, ensure_ascii=False)
        
        if sync_remote:
            self._sync_to_railway(reason=sync_reason, silent=silent_sync)

    def _sync_to_railway(self, reason: Optional[str] = None, silent: bool = False) -> bool:
        """Helper to sync clients_data.json to Railway with optional messaging"""
        try:
            from railway_sync import sync_to_railway
        except ImportError:
            if not silent:
                print("💡 Railway sync skipped (railway_sync.py not available).")
            return False
        except Exception as e:
            if not silent:
                print(f"⚠️ Railway sync import failed: {str(e)[:120]}")
            return False
        
        if not silent:
            prefix = f"🔄 Syncing to Railway ({reason})..." if reason else "🔄 Syncing to Railway..."
            print(f"\n{prefix}")
        
        try:
            success = sync_to_railway(self.data_file, preserve_va_work=True)
            if not silent:
                if success:
                    print("✅ Railway sync complete.")
                else:
                    print("⚠️ Railway sync reported a failure (see logs above).")
            return success
        except Exception as e:
            if not silent:
                print(f"⚠️ Railway sync failed: {str(e)[:200]}")
            return False
    
    def add_client(self, client_name: str, ig_username: str):
        """Add a new client to the database"""
        if ig_username in self.clients_data["clients"]:
            print(f"⚠️  Client with username @{ig_username} already exists!")
            return False
        
        self.clients_data["clients"][ig_username] = {
            "name": client_name,
            "username": ig_username,
            "added_date": datetime.now().isoformat(),
            "following": [],
            "following_count": 0,
            "last_scraped": None
        }
        self.save_data(sync_remote=True, sync_reason=f"Client added (@{ig_username})")
        print(f"✅ Added client: {client_name} (@{ig_username})")
        return True
    
    def list_clients(self):
        """List all clients with their status"""
        clients = self.clients_data.get("clients", {})
        
        if not clients:
            print("\n📋 No clients added yet.")
            print("   Use Option 1, 2, 3, or 4 to add clients.\n")
            return
        
        print("\n" + "="*60)
        print(f"📋 CLIENT LIST ({len(clients)} clients)")
        print("="*60)
        
        for i, (username, client_data) in enumerate(clients.items(), 1):
            name = client_data.get("name", username)
            following_count = client_data.get("following_count", 0)
            last_scraped = client_data.get("last_scraped")
            added_date = client_data.get("added_date", "")
            
            # Format date
            if added_date:
                try:
                    date_obj = datetime.fromisoformat(added_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%Y-%m-%d")
                except:
                    date_str = added_date[:10] if len(added_date) >= 10 else added_date
            else:
                date_str = "Unknown"
            
            # Status indicator
            if following_count > 0:
                status = "✅ Scraped"
                status_info = f"{following_count:,} accounts"
            else:
                status = "⏳ Not scraped"
                status_info = "No data yet"
            
            # Last scraped info
            if last_scraped:
                try:
                    scraped_date = datetime.fromisoformat(last_scraped.replace('Z', '+00:00'))
                    scraped_str = scraped_date.strftime("%Y-%m-%d %H:%M")
                except:
                    scraped_str = last_scraped[:16] if len(last_scraped) >= 16 else last_scraped
                status_info += f" (last: {scraped_str})"
            
            print(f"\n{i}. {name} (@{username})")
            print(f"   Status: {status}")
            print(f"   Accounts: {status_info}")
            print(f"   Added: {date_str}")
        
        print("\n" + "="*60 + "\n")
    
    def validate_account(self, ig_username: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that an Instagram account exists and is public before scraping
        Returns: (is_valid, error_message)
        """
        profile_data = None  # Initialize outside try block
        try:
            # Use Instagram Profile Scraper to check account status
            # Actor: apify/instagram-profile-scraper
            run_input = {
                "usernames": [ig_username],
                "resultsLimit": 1,  # We only need to check if it exists
            }
            
            print(f"  🔍 Validating account @{ig_username}...")
            run = self.client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
            
            # Check if we got any results
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                profile_data = item
                break
            
            if not profile_data:
                return False, "Account not found or doesn't exist"
            
            # Check if account is private
            is_private = profile_data.get("isPrivate", False)
            if is_private:
                return False, "Account is private - cannot scrape following list without authentication"
            
            # Check if account exists
            if not profile_data.get("username"):
                return False, "Account data incomplete"
            
            print(f"  ✅ Account @{ig_username} is valid and public")
            return True, None
            
        except Exception as e:
            error_msg = str(e)
            # Validation can give false negatives due to rate limiting, temporary Instagram issues, etc.
            # So we'll be more lenient - only fail on clear errors
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                # 401 might be temporary - allow scraping to proceed
                print(f"  ⚠️  Validation check returned 401 (might be temporary): {error_msg[:100]}, will attempt scrape anyway...")
                return True, None  # Allow scraping to proceed
            elif "404" in error_msg or "not found" in error_msg.lower():
                # 404 might also be a false negative - Instagram/Apify can be inconsistent
                # Check if we actually got profile data despite the error
                if profile_data and profile_data.get("username"):
                    # We got data, so account exists - validation error was false
                    print(f"  ✅ Account @{ig_username} exists (validation error was false negative)")
                    return True, None
                else:
                    # No data, likely doesn't exist - but allow scraping anyway (might be false negative)
                    print(f"  ⚠️  Validation returned 404, but allowing scrape attempt (might be false negative): {error_msg[:100]}")
                    return True, None  # Allow scraping to proceed - validation is unreliable
            else:
                # If validation fails, we'll still try scraping (might be temporary)
                print(f"  ⚠️  Validation check failed: {error_msg[:100]}, will attempt scrape anyway...")
                return True, None  # Allow scraping to proceed
    
    def scrape_client_following(self, ig_username: str, max_retries: int = 3, validate_first: bool = True) -> Optional[List[Dict]]:
        """
        Scrape the accounts that a client follows using Apify with retry logic
        Uses: instagram-following-scraper by louisdeconinck
        
        Args:
            ig_username: Instagram username to scrape
            max_retries: Maximum number of retry attempts
            validate_first: If True, validate account exists and is public before scraping
        
        Returns: List of following accounts, or None if failed after retries
        """
        if ig_username not in self.clients_data["clients"]:
            raise ValueError(f"Client @{ig_username} not found. Add them first!")
        
        # Validate account first to prevent errors
        if validate_first:
            is_valid, error_msg = self.validate_account(ig_username)
            if not is_valid:
                print(f"  ❌ Cannot scrape @{ig_username}: {error_msg}")
                return None
        
        # Add delay before scraping to avoid rate limits
        time.sleep(3)  # 3 second delay before each scrape
        
        # Run the Apify actor
        # Actor: louisdeconinck/instagram-following-scraper
        run_input = {
            "usernames": [ig_username],  # Note: expects array of usernames
        }
        
        last_error = None
        permanent_failure = False  # Track if error is permanent (don't retry)
        
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1 and not permanent_failure:
                    # Shorter wait times: 15s, 30s, 45s
                    wait_time = 15 * attempt
                    print(f"  ⏳ Retry attempt {attempt}/{max_retries} (waiting {wait_time}s before retry)...")
                    # Show countdown during wait
                    for remaining in range(wait_time, 0, -5):
                        if remaining > 5:
                            print(f"     {remaining}s remaining...", end='\r')
                        time.sleep(min(5, remaining))
                    print("     Starting retry...     ")
                
                print(f"🔍 Scraping following list for @{ig_username}... (attempt {attempt}/{max_retries})")
                
                run = self.client.actor("louisdeconinck/instagram-following-scraper").call(run_input=run_input)
                
                # Check run status for clues about failure
                run_status = run.get("status", "").upper()
                
                # Fetch results
                following_list = []
                try:
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        following_list.append({
                            "username": item.get("username"),
                            "full_name": item.get("full_name", ""),
                            "follower_count": item.get("follower_count", 0),
                            "is_verified": item.get("is_verified", False),
                            "is_private": item.get("is_private", False),
                        })
                except Exception as dataset_error:
                    # If we can't even access the dataset, it's likely a permanent failure
                    error_str = str(dataset_error)
                    if "401" in error_str or "unauthorized" in error_str.lower():
                        permanent_failure = True
                        last_error = "Cannot access account - likely private or doesn't exist (401)"
                        print(f"  ❌ Account not accessible (401): {error_str[:100]}")
                        break
                    raise
                
                # Check if we got results
                if len(following_list) == 0:
                    # Check if this is a permanent failure (401) vs temporary (rate limit)
                    # The Apify logs showed 401 errors for @Ryan.walkwitz
                    # If the run succeeded but returned 0 results, it might be:
                    # 1. Account is private (permanent - don't retry)
                    # 2. Account doesn't exist (permanent - don't retry)
                    # 3. Rate limit (temporary - retry)
                    # 4. Network issue (temporary - retry)
                    
                    # Look for 401 in the run output/logs - if we see it, it's permanent
                    if attempt == 1:
                        # First attempt with 0 results - could be temporary, retry once
                        print(f"  ⚠️  Got 0 results - might be temporary failure, will retry once...")
                        last_error = "No results returned"
                        continue
                    else:
                        # Already retried - likely permanent
                        print(f"  ⚠️  Got 0 results after {attempt} attempts")
                        print(f"  💡 Likely causes: account is private, doesn't exist, or permanently blocked")
                        permanent_failure = True
                        break
                
                # Success! Update client data
                self.clients_data["clients"][ig_username]["following"] = following_list
                self.clients_data["clients"][ig_username]["following_count"] = len(following_list)
                self.clients_data["clients"][ig_username]["last_scraped"] = datetime.now().isoformat()
                
                # Update pages database
                self._update_pages_database(ig_username, following_list)
                
                # Use silent sync to avoid noisy logs when scraping multiple clients
                self.save_data(sync_remote=True, sync_reason=f"Scraped @{ig_username}", silent_sync=True)
                print(f"✅ Scraped {len(following_list)} accounts for @{ig_username}")
                return following_list
                
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                
                # Check for Apify actor authentication issues
                if "authentication token is not valid" in error_msg.lower() or "token is not valid" in error_msg.lower():
                    error_type = "Apify actor authentication issue"
                    # This could be:
                    # 1. The actor's Instagram session expired (temporary - retry might help)
                    # 2. Instagram is blocking the actor (permanent for this account)
                    # 3. The actor needs reconfiguration (permanent until fixed)
                    # Since we can't distinguish, we'll retry once but then mark as permanent
                    if attempt >= 2:
                        permanent_failure = True
                        print(f"  ❌ {error_type}: The Apify actor's Instagram authentication may be expired or blocked")
                        print(f"  💡 This usually means:")
                        print(f"     - The actor's Instagram session expired (try again later)")
                        print(f"     - Instagram is blocking the actor's requests")
                        print(f"     - The account might be private or restricted")
                    else:
                        print(f"  ❌ {error_type}: {error_msg[:100]}")
                        print(f"  💡 Retrying - this might be a temporary authentication issue")
                # Categorize the error and determine if it's permanent
                elif "401" in error_msg or "unauthorized" in error_msg.lower():
                    error_type = "Account not found/private (401)"
                    permanent_failure = True  # 401 is permanent - don't retry
                    print(f"  ❌ {error_type}: Account is private or doesn't exist")
                    print(f"  💡 Skipping retries - this is a permanent failure")
                    break
                elif "403" in error_msg or "blocked" in error_msg.lower():
                    error_type = "Instagram blocking (403)"
                    # 403 might be temporary (rate limit) or permanent (IP ban)
                    # Retry once, but if it persists, it's likely permanent
                    if attempt >= 2:
                        permanent_failure = True
                    print(f"  ❌ {error_type}: {error_msg[:100]}")
                elif "rate limit" in error_msg.lower():
                    error_type = "Rate limit"
                    # Rate limits are temporary - always retry
                    print(f"  ❌ {error_type}: {error_msg[:100]}")
                else:
                    error_type = "Unknown error"
                    print(f"  ❌ {error_type}: {error_msg[:100]}")
                
                if permanent_failure:
                    break
                
                if attempt < max_retries:
                    print(f"  ⏳ Will retry in {15 * (attempt + 1)} seconds...")
                else:
                    print(f"  ❌ Failed after {max_retries} attempts")
                    return None
        
        # If we get here, all retries failed or permanent failure detected
        if permanent_failure:
            print(f"❌ Permanent failure for @{ig_username} - account likely private or doesn't exist")
        else:
            print(f"❌ Failed to scrape @{ig_username} after {max_retries} attempts")
        
        if last_error:
            print(f"   Reason: {last_error[:200]}")
        return None
    
    def _update_pages_database(self, client_username: str, following_list: List[Dict]):
        """Update the pages database with follower information"""
        for page in following_list:
            page_username = page["username"]
            
            if page_username not in self.clients_data["pages"]:
                self.clients_data["pages"][page_username] = {
                    "username": page_username,
                    "full_name": page.get("full_name", ""),
                    "follower_count": page.get("follower_count", 0),
                    "is_verified": page.get("is_verified", False),
                    "clients_following": [],
                    "promo_price": None,  # To be filled in later
                    "category": None,  # Auto-detected category
                    "category_confidence": None,  # AI confidence score (0-1)
                    "contact_email": None,  # Extracted from bio/contact
                    "promo_status": "Unknown",  # "Warm", "Unknown", "Not Open"
                    "promo_indicators": [],  # List of detected signals
                    "last_categorized": None,  # Timestamp
                    "profile_data": None,  # Scraped profile data (profile_pic_url, posts, etc.)
                    "known_contact_methods": [],  # List: ["IG DM", "Email", "Phone", "WhatsApp", "Other"]
                    "successful_contact_method": None,  # Which method they replied to
                    "current_main_contact_method": None,  # Current primary contact method
                    "ig_account_for_dm": None,  # Which IG account username is used for IG DM (if applicable)
                    "website_url": None,  # Website URL from bio or link in bio
                    "website_promo_info": None  # Info about promo mentions on website (has_promo_mention, has_promo_page, has_contact_email)
                }
            
            # Add this client to the page's followers list
            if client_username not in self.clients_data["pages"][page_username]["clients_following"]:
                self.clients_data["pages"][page_username]["clients_following"].append(client_username)
            
            # Update follower count (in case it changed)
            self.clients_data["pages"][page_username]["follower_count"] = page.get("follower_count", 0)
    
    def scrape_all_clients(self, delay_between: int = 10):
        """
        Scrape following lists for all clients with progress tracking
        
        Args:
            delay_between: Seconds to wait between clients (default: 10 - increased to prevent rate limits)
        """
        clients = list(self.clients_data["clients"].keys())
        total = len(clients)
        succeeded = []
        failed = []
        
        print(f"\n📊 Scraping {total} clients...")
        print("="*60)
        
        for i, ig_username in enumerate(clients, 1):
            print(f"\n[{i}/{total}] Processing @{ig_username}")
            print(f"   Progress: {len(succeeded)} succeeded, {len(failed)} failed so far")
            print("-"*60)
            
            result = self.scrape_client_following(ig_username)
            
            if result is not None:
                succeeded.append(ig_username)
            else:
                failed.append(ig_username)
            
            # Add delay between clients (except for the last one)
            if i < total and delay_between > 0:
                print(f"\n⏳ Waiting {delay_between}s before next client (avoiding rate limits)...")
                time.sleep(delay_between)
        
        # Final summary
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        print(f"✅ Succeeded: {len(succeeded)}/{total}")
        print(f"❌ Failed: {len(failed)}/{total}")
        
        if succeeded:
            print(f"\n✅ Successful clients:")
            for username in succeeded:
                count = self.clients_data["clients"][username].get("following_count", 0)
                print(f"   • @{username}: {count} accounts")
        
        if failed:
            print(f"\n❌ Failed clients:")
            for username in failed:
                print(f"   • @{username}")
            print(f"\n💡 Tip: You can retry failed clients individually using Option 5")
        
        print("="*60 + "\n")
    
    def get_cross_referenced_pages(self, min_clients: int = 2) -> List[Dict]:
        """
        Get pages that are followed by multiple clients
        Returns sorted by number of clients (descending)
        """
        pages_with_multiple = []
        
        for page_username, page_data in self.clients_data["pages"].items():
            client_count = len(page_data["clients_following"])
            
            if client_count >= min_clients:
                follower_count = page_data["follower_count"]
                
                # Calculate concentration metric (clients per follower)
                concentration = client_count / follower_count if follower_count > 0 else 0
                
                # Calculate follower per client ratio
                followers_per_client = follower_count / client_count if client_count > 0 else 0
                
                pages_with_multiple.append({
                    "username": page_username,
                    "full_name": page_data["full_name"],
                    "clients_following": client_count,
                    "total_followers": follower_count,
                    "concentration": concentration,  # Higher = more of their audience is your clients
                    "followers_per_client": followers_per_client,
                    "is_verified": page_data["is_verified"],
                    "clients": page_data["clients_following"],
                    "promo_price": page_data.get("promo_price")
                })
        
        # Sort by number of clients (descending)
        pages_with_multiple.sort(key=lambda x: x["clients_following"], reverse=True)
        return pages_with_multiple
    
    def add_promo_price(self, page_username: str, price: float):
        """Add promotional price for a page"""
        if page_username not in self.clients_data["pages"]:
            print(f"⚠️  Page @{page_username} not found in database!")
            return False
        
        self.clients_data["pages"][page_username]["promo_price"] = price
        self.save_data(sync_remote=True, sync_reason=f"Promo price updated (@{page_username})")
        print(f"✅ Updated price for @{page_username}: ${price}")
        return True
    
    def calculate_roi_metrics(self, min_clients: int = 2) -> List[Dict]:
        """
        Calculate ROI metrics for pages with pricing data
        Returns pages sorted by best value
        """
        pages = self.get_cross_referenced_pages(min_clients)
        pages_with_price = []
        
        for page in pages:
            if page["promo_price"] is not None and page["promo_price"] > 0:
                # Metric 1: Clients per dollar
                clients_per_dollar = page["clients_following"] / page["promo_price"]
                
                # Metric 2: Concentration per dollar (recommended)
                concentration_per_dollar = page["concentration"] / page["promo_price"]
                
                # Metric 3: Cost per client reached
                cost_per_client = page["promo_price"] / page["clients_following"]
                
                page["clients_per_dollar"] = clients_per_dollar
                page["concentration_per_dollar"] = concentration_per_dollar
                page["cost_per_client"] = cost_per_client
                
                pages_with_price.append(page)
        
        # Sort by concentration per dollar (best value)
        pages_with_price.sort(key=lambda x: x["concentration_per_dollar"], reverse=True)
        return pages_with_price
    
    def print_analysis_report(self, min_clients: int = 2):
        """Print a formatted analysis report"""
        total_clients = len(self.clients_data["clients"])
        total_pages = len(self.clients_data["pages"])
        
        print("\n" + "="*80)
        print("📊 INSTAGRAM FOLLOWER ANALYSIS REPORT")
        print("="*80)
        print(f"\n📈 Total Clients: {total_clients}")
        print(f"📄 Total Pages Tracked: {total_pages}")
        print(f"\n🔍 Pages followed by {min_clients}+ clients:\n")
        
        pages = self.get_cross_referenced_pages(min_clients)
        
        if not pages:
            print(f"No pages found with {min_clients}+ clients following.")
            return
        
        for i, page in enumerate(pages[:20], 1):  # Top 20
            page_username = page['username']
            page_data = self.clients_data["pages"].get(page_username, {})
            
            print(f"\n{i}. @{page['username']}")
            print(f"   Name: {page['full_name']}")
            print(f"   Clients Following: {page['clients_following']}/{total_clients} "
                  f"({page['clients_following']/total_clients*100:.1f}%)")
            print(f"   Total Followers: {page['total_followers']:,}")
            print(f"   Concentration: {page['concentration']:.2e} (clients/follower)")
            print(f"   Followers per Client: {page['followers_per_client']:,.0f}")
            
            # Category info
            if page_data.get('category'):
                category_display = page_data['category'].replace('_', ' ')
                confidence = page_data.get('category_confidence', 0)
                print(f"   📁 Category: {category_display} ({confidence*100:.0f}%)")
            
            # Promo status
            promo_status = page_data.get('promo_status', 'Unknown')
            if promo_status == "Warm":
                print(f"   🟢 Promo Status: {promo_status}")
                if page_data.get('contact_email'):
                    print(f"   📧 Email: {page_data['contact_email']}")
            
            if page['is_verified']:
                print(f"   ✓ Verified")
            
            if page['promo_price']:
                print(f"   💰 Promo Price: ${page['promo_price']:,.2f}")
                metrics = self.calculate_roi_metrics(min_clients)
                for metric_page in metrics:
                    if metric_page['username'] == page['username']:
                        print(f"   📊 Value Score: {metric_page['concentration_per_dollar']:.2e} concentration/$")
                        print(f"   💵 Cost per Client: ${metric_page['cost_per_client']:.2f}")
                        break
        
        print("\n" + "="*80 + "\n")
    
    def get_categorizer(self) -> InstagramCategorizer:
        """Lazy-load the categorizer"""
        if self._categorizer is None:
            if not self.openai_api_key:
                raise ValueError("OpenAI API key required for categorization!")
            if not self.apify_token:
                raise ValueError("Apify token required for categorization!")
            self._categorizer = InstagramCategorizer(
                self.apify_token,  # Use the token from analyzer, not environment
                self.openai_api_key
            )
        return self._categorizer
    
    def categorize_pages(self, min_clients: int = 2, force_recategorize: bool = False, 
                         max_followers: int = None, min_concentration: float = None):
        """
        Categorize pages using AI vision analysis with smart filtering
        
        Args:
            min_clients: Minimum clients following (default: 2)
            force_recategorize: Re-categorize already categorized pages
            max_followers: Skip pages with more followers (e.g., 1000000 to skip mega influencers)
            min_concentration: Skip pages below this concentration (e.g., 0.000001)
        """
        # Get pages to categorize
        pages_to_categorize = []
        skipped_low_value = []
        skipped_already_done = []
        
        for page_username, page_data in self.clients_data["pages"].items():
            client_count = len(page_data["clients_following"])
            follower_count = page_data.get("follower_count", 0)
            
            # Check if meets minimum clients threshold
            if client_count < min_clients:
                continue
            
            # Check if already categorized (unless forcing)
            # Don't count "UNKNOWN" with 0 confidence as categorized
            existing_category = page_data.get("category")
            existing_confidence = page_data.get("category_confidence", 0)
            is_validly_categorized = existing_category and existing_category != "UNKNOWN" and existing_confidence > 0
            
            if not force_recategorize and is_validly_categorized:
                skipped_already_done.append((page_username, client_count, follower_count))
                continue
            
            # Calculate concentration
            concentration = client_count / follower_count if follower_count > 0 else 0
            
            # Skip mega influencers if max_followers set
            if max_followers and follower_count > max_followers:
                skipped_low_value.append((page_username, client_count, follower_count, concentration, "too many followers"))
                continue
            
            # Skip low concentration pages if min_concentration set
            if min_concentration and concentration < min_concentration:
                skipped_low_value.append((page_username, client_count, follower_count, concentration, "low concentration"))
                continue
            
            pages_to_categorize.append(page_username)
        
        if not pages_to_categorize:
            if skipped_already_done:
                print(f"✅ All {len(skipped_already_done)} pages with {min_clients}+ clients are already categorized!")
            else:
                print(f"✅ No uncategorized pages found with {min_clients}+ clients")
            
            if skipped_low_value:
                print(f"\n💡 Skipped {len(skipped_low_value)} low-value pages:")
                for username, clients, followers, conc, reason in skipped_low_value[:10]:
                    print(f"   • @{username}: {clients} clients, {followers:,} followers ({reason})")
                if len(skipped_low_value) > 10:
                    print(f"   ... and {len(skipped_low_value) - 10} more")
            return
        
        print(f"\n📊 Found {len(pages_to_categorize)} pages to categorize")
        print(f"   (Pages followed by {min_clients}+ clients)")
        
        if skipped_already_done:
            print(f"   ✅ {len(skipped_already_done)} pages already categorized (will skip)")
        
        if skipped_low_value:
            print(f"   ⏭️  {len(skipped_low_value)} low-value pages skipped (saving ${len(skipped_low_value) * 0.25:.2f})")
            print(f"      Skipped reasons: mega influencers or low concentration")
        
        # Categorize with cost estimate
        categorizer = self.get_categorizer()
        results = categorizer.categorize_pages_batch(pages_to_categorize, show_cost_estimate=True)
        
        # Update database with results
        for username, result in results.items():
            if username in self.clients_data["pages"]:
                self.clients_data["pages"][username]["category"] = result["category"]
                self.clients_data["pages"][username]["category_confidence"] = result["category_confidence"]
                self.clients_data["pages"][username]["contact_email"] = result["contact_email"]
                self.clients_data["pages"][username]["promo_status"] = result["promo_status"]
                self.clients_data["pages"][username]["promo_indicators"] = result["promo_indicators"]
                self.clients_data["pages"][username]["last_categorized"] = result["last_categorized"]
        
        self.save_data(sync_remote=True, sync_reason="Categorization updates")
        print(f"\n✅ Updated {len(results)} pages in database")
    
    def get_pages_by_category(self, min_clients: int = 1) -> Dict[str, List[Dict]]:
        """Group pages by category"""
        by_category = {}
        
        for page_username, page_data in self.clients_data["pages"].items():
            client_count = len(page_data["clients_following"])
            
            if client_count < min_clients:
                continue
            
            category = page_data.get("category", "UNCATEGORIZED")
            if category not in by_category:
                by_category[category] = []
            
            # Build page info
            follower_count = page_data["follower_count"]
            concentration = client_count / follower_count if follower_count > 0 else 0
            
            page_info = {
                "username": page_username,
                "full_name": page_data["full_name"],
                "clients_following": client_count,
                "total_followers": follower_count,
                "concentration": concentration,
                "category_confidence": page_data.get("category_confidence"),
                "contact_email": page_data.get("contact_email"),
                "promo_status": page_data.get("promo_status", "Unknown"),
                "promo_indicators": page_data.get("promo_indicators", []),
                "promo_price": page_data.get("promo_price"),
                "is_verified": page_data.get("is_verified", False)
            }
            
            by_category[category].append(page_info)
        
        # Sort each category by clients following
        for category in by_category:
            by_category[category].sort(key=lambda x: x["clients_following"], reverse=True)
        
        return by_category
    
    def print_category_report(self, min_clients: int = 2):
        """Print analysis report grouped by category"""
        total_clients = len(self.clients_data["clients"])
        by_category = self.get_pages_by_category(min_clients)
        
        print("\n" + "="*80)
        print("📊 INSTAGRAM PAGES BY CATEGORY")
        print("="*80)
        print(f"\n📈 Total Clients: {total_clients}")
        print(f"🔍 Showing pages followed by {min_clients}+ clients\n")
        
        # Count categorized vs uncategorized
        categorized_count = sum(len(pages) for cat, pages in by_category.items() if cat != "UNCATEGORIZED")
        uncategorized_count = len(by_category.get("UNCATEGORIZED", []))
        
        print(f"✅ Categorized: {categorized_count} pages")
        if uncategorized_count > 0:
            print(f"⚠️  Uncategorized: {uncategorized_count} pages\n")
        
        # Display by category
        for category in sorted(by_category.keys()):
            if category == "UNCATEGORIZED":
                continue
            
            pages = by_category[category]
            category_display = category.replace("_", " ")
            
            print(f"\n{'='*80}")
            print(f"📁 {category_display} ({len(pages)} pages)")
            print(f"{'='*80}")
            
            for i, page in enumerate(pages[:10], 1):  # Top 10 per category
                print(f"\n{i}. @{page['username']}")
                print(f"   Name: {page['full_name']}")
                print(f"   Clients: {page['clients_following']}/{total_clients} "
                      f"({page['clients_following']/total_clients*100:.1f}%)")
                print(f"   Followers: {page['total_followers']:,}")
                print(f"   Concentration: {page['concentration']:.2e}")
                
                if page.get('category_confidence'):
                    print(f"   Confidence: {page['category_confidence']*100:.0f}%")
                
                # Promo status
                if page['promo_status'] == "Warm":
                    emoji = "🟢"
                elif page['promo_status'] == "Not Open":
                    emoji = "🔴"
                else:
                    emoji = "⚪"
                
                print(f"   {emoji} Promo Status: {page['promo_status']}")
                
                if page.get('contact_email'):
                    print(f"   📧 Email: {page['contact_email']}")
                
                if page.get('promo_indicators'):
                    print(f"   💡 Indicators: {', '.join(page['promo_indicators'][:2])}")
                
                if page.get('promo_price'):
                    print(f"   💰 Price: ${page['promo_price']:,.2f}")
                
                if page.get('is_verified'):
                    print(f"   ✓ Verified")
        
        # Show uncategorized at the end
        if "UNCATEGORIZED" in by_category:
            pages = by_category["UNCATEGORIZED"]
            print(f"\n{'='*80}")
            print(f"❓ UNCATEGORIZED ({len(pages)} pages)")
            print(f"{'='*80}")
            print(f"\nRun 'Categorize pages with AI' to categorize these pages:\n")
            for page in pages[:20]:
                print(f"  • @{page['username']} ({page['clients_following']} clients)")
        
        print("\n" + "="*80 + "\n")
    
    def export_to_csv(self, filename: str = "ig_analysis.csv"):
        """Export analysis to CSV file with category data and client lists"""
        import csv
        
        pages = self.get_cross_referenced_pages(min_clients=1)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['username', 'full_name', 'clients_following', 'clients_list', 'total_followers', 
                         'concentration', 'followers_per_client', 'is_verified', 'promo_price',
                         'category', 'category_confidence', 'contact_email', 'promo_status', 'promo_indicators']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for page in pages:
                # Get additional data from database
                page_data = self.clients_data["pages"].get(page['username'], {})
                
                # Get list of client usernames following this page
                clients_list = page_data.get('clients_following', [])
                clients_list_str = ', '.join(clients_list) if clients_list else ''
                
                # Get client names (more readable)
                client_names = []
                for client_username in clients_list:
                    client_info = self.clients_data["clients"].get(client_username, {})
                    client_name = client_info.get('name', client_username)
                    client_names.append(f"{client_name} (@{client_username})")
                clients_names_str = '; '.join(client_names) if client_names else ''
                
                # Format category for display
                category = page_data.get('category', '')
                if category:
                    category = category.replace('_', ' ')
                
                # Format category confidence as percentage
                confidence = page_data.get('category_confidence', '')
                if confidence and isinstance(confidence, (int, float)):
                    confidence = f"{confidence * 100:.0f}%"
                
                # Format promo indicators
                indicators = page_data.get('promo_indicators', [])
                indicators_str = '; '.join(indicators) if indicators else ''
                
                writer.writerow({
                    'username': page['username'],
                    'full_name': page['full_name'],
                    'clients_following': page['clients_following'],
                    'clients_list': clients_names_str,  # Shows which clients follow this page
                    'total_followers': page['total_followers'],
                    'concentration': page['concentration'],
                    'followers_per_client': page['followers_per_client'],
                    'is_verified': page['is_verified'],
                    'promo_price': page.get('promo_price', ''),
                    'category': category,
                    'category_confidence': confidence,
                    'contact_email': page_data.get('contact_email', ''),
                    'promo_status': page_data.get('promo_status', 'Unknown'),
                    'promo_indicators': indicators_str
                })
        
        print(f"✅ Exported to {filename}")
        print(f"   📊 {len(pages)} pages exported")
        print(f"   📋 Includes: client lists, categories, contact info, promo status")


def main():
    """Main CLI interface"""
    import sys
    
    # Check for API tokens - try environment variables first, then config file
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
        print("❌ APIFY_TOKEN not found!")
        print("   Set it as environment variable OR create config.py with APIFY_TOKEN")
        print("   Get your token from: https://console.apify.com/account/integrations")
        print("\n   Quick fix: Run 'set_permanent_env.bat' to set it permanently")
        sys.exit(1)
    
    # OpenAI key is optional (only needed for categorization)
    
    analyzer = IGFollowerAnalyzer(apify_token, openai_key)
    
    print("\n🎯 Instagram Follower Analyzer")
    print("=" * 50)
    print("\n📋 RECOMMENDED WORKFLOW (VA Strategy):")
    print("   1️⃣  Add clients (Option 1 or 2)")
    print("   2️⃣  Scrape following lists (Option 3 or 4)")
    print("   3️⃣  Pre-scrape profile data (Option 5 or run: python scrape_profiles.py)")
    print("   4️⃣  Use Streamlit app for categorization: streamlit run categorize_app.py")
    print("\n💡 The Streamlit app is your main interface for:")
    print("   • Categorizing pages (one at a time, with hotlist priority)")
    print("   • Editing contact info, pricing, promo status")
    print("   • Viewing pages by category (sorted by ROI)")
    print("\n" + "=" * 50)
    print("\n👥 Client Management:")
    print("1. Add new client (single)")
    print("2. Add multiple clients (bulk)")
    print("3. Scrape client's following list")
    print("4. Scrape all clients' following lists")
    print("16. List all clients")
    print("\n📸 Profile Data (Required for Streamlit):")
    print("5. Pre-scrape profile data (run scrape_profiles.py)")
    print("   → This scrapes profile pics, bios, posts for VA categorization")
    print("\n📊 Analysis & Reports:")
    print("6. View analysis report")
    print("7. View pages by category")
    print("8. View ROI analysis (with prices)")
    print("\n💰 Pricing & Export:")
    print("9. Add promo price for a page")
    print("10. Export to CSV")
    print("\n🤖 AI Categorization (Optional - Not Recommended):")
    print("11. Categorize pages with AI (uncategorized only)")
    print("12. Smart Categorize (skip mega influencers)")
    print("13. Re-categorize all pages")
    print("\n15. Exit")
    
    while True:
        choice = input("\nSelect option (1-16): ").strip()
        
        if choice == "1":
            # Add new client (single)
            name = input("Client name: ").strip()
            username = input("Instagram username (without @): ").strip().lstrip('@')
            if not username:
                print("❌ Username required!")
                continue
            analyzer.add_client(name, username)
            print(f"✅ Client @{username} added!")
            print(f"💡 Next: Use option 3 to scrape their following list")
        
        elif choice == "2":
            # Add multiple clients (bulk)
            print("\n📋 BULK ADD CLIENTS")
            print("="*60)
            usernames_input = input("Enter Instagram usernames (comma or space separated): ").strip()
            if not usernames_input:
                print("❌ No usernames provided!")
                continue
            
            # Parse usernames
            usernames = []
            for username in usernames_input.replace(',', ' ').split():
                username = username.strip().lstrip('@')
                if username:
                    usernames.append(username)
            
            if not usernames:
                print("❌ No valid usernames found!")
                continue
            
            print(f"\n📋 Adding {len(usernames)} clients...")
            added = 0
            for username in usernames:
                if username not in analyzer.clients_data["clients"]:
                    analyzer.add_client(username, username)
                    added += 1
                else:
                    print(f"  ⚠️  @{username} already exists, skipping...")
            
            print(f"\n✅ Added {added} new clients!")
            print(f"💡 Next: Use option 4 to scrape all clients' following lists")
        
        elif choice == "3":
            # Scrape client's following list
            username = input("Instagram username to scrape: ").strip().lstrip('@')
            if not username:
                print("❌ Username required!")
                continue
            
            skip_validation = input("Skip account validation? (faster but may fail on private accounts) (y/n, default n): ").strip().lower() == 'y'
            result = analyzer.scrape_client_following(username, validate_first=not skip_validation)
            if result is None:
                print(f"❌ Failed to scrape @{username}")
                print(f"💡 This might mean: account is private, doesn't exist, or Instagram blocked the request")
            else:
                print(f"✅ Successfully scraped @{username}")
                print(f"💡 Next: Use option 5 to pre-scrape profile data, then use Streamlit app")
        
        elif choice == "4":
            # Scrape all clients
            confirm = input("Scrape all clients? This may take a while and use API credits. (y/n): ")
            if confirm.lower() == 'y':
                delay = input("Delay between clients in seconds (default 10, recommended 10-15): ").strip()
                delay = int(delay) if delay else 10
                if delay < 5:
                    confirm_low = input(f"⚠️  Warning: {delay}s delay is very low and may cause rate limiting. Continue? (y/n): ")
                    if confirm_low.lower() != 'y':
                        continue
                analyzer.scrape_all_clients(delay_between=delay)
                print(f"\n💡 Next: Use option 5 to pre-scrape profile data, then use Streamlit app")
        
        elif choice == "5":
            # Pre-scrape profile data (for Streamlit)
            print("\n📸 PRE-SCRAPE PROFILE DATA")
            print("="*60)
            print("This will scrape profile pictures, bios, and posts for all pages.")
            print("This data is required for the Streamlit categorization app.")
            print("\n💡 Tip: Run 'python scrape_profiles.py' directly for more control")
            print("   (Priority scrape for fast results, or scrape all for complete data)")
            confirm = input("\nContinue with profile scraping? (y/n): ")
            if confirm.lower() == 'y':
                import subprocess
                import sys
                print("\n🚀 Launching scrape_profiles.py...")
                print("="*60)
                subprocess.run([sys.executable, "scrape_profiles.py"])
            else:
                print("💡 To run manually: python scrape_profiles.py")
        
        elif choice == "6":
            # View analysis report
            min_clients = input("Minimum clients following (default 2): ").strip()
            min_clients = int(min_clients) if min_clients else 2
            analyzer.print_analysis_report(min_clients)
        
        elif choice == "7":
            # View pages by category
            min_clients = input("Minimum clients following (default 2): ").strip()
            min_clients = int(min_clients) if min_clients else 2
            analyzer.print_category_report(min_clients)
        
        elif choice == "8":
            # View ROI analysis
            min_clients = input("Minimum clients following (default 2): ").strip()
            min_clients = int(min_clients) if min_clients else 2
            pages = analyzer.calculate_roi_metrics(min_clients)
            
            print("\n" + "="*80)
            print("💰 ROI ANALYSIS (BEST VALUE PAGES)")
            print("="*80 + "\n")
            
            for i, page in enumerate(pages[:10], 1):
                print(f"{i}. @{page['username']}")
                print(f"   Clients: {page['clients_following']} | Followers: {page['total_followers']:,}")
                print(f"   Price: ${page['promo_price']:,.2f}")
                print(f"   ⭐ Value Score: {page['concentration_per_dollar']:.2e} concentration/$")
                print(f"   📊 Clients per $: {page['clients_per_dollar']:.4f}")
                print(f"   💵 Cost per client: ${page['cost_per_client']:.2f}\n")
        
        elif choice == "9":
            # Add promo price
            username = input("Page username: ").strip().lstrip('@')
            if not username:
                print("❌ Username required!")
                continue
            try:
                price = float(input("Promo price ($): ").strip())
                analyzer.add_promo_price(username, price)
            except ValueError:
                print("❌ Invalid price!")
        
        elif choice == "10":
            # Export to CSV
            filename = input("Filename (default: ig_analysis.csv): ").strip()
            filename = filename if filename else "ig_analysis.csv"
            analyzer.export_to_csv(filename)
        
        elif choice == "11":
            # AI Categorize (optional - not recommended)
            if not openai_key:
                print("❌ OPENAI_API_KEY not set!")
                print("💡 Note: For VA strategy, use Streamlit app instead: streamlit run categorize_app.py")
                continue
            
            print("⚠️  AI Categorization is not recommended for VA strategy.")
            print("💡 Use Streamlit app instead: streamlit run categorize_app.py")
            confirm = input("Continue anyway? (y/n): ")
            if confirm.lower() != 'y':
                continue
            
            min_clients = input("Minimum clients following (default 2): ").strip()
            min_clients = int(min_clients) if min_clients else 2
            
            try:
                analyzer.categorize_pages(min_clients, force_recategorize=False)
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif choice == "12":
            # Smart Categorize (optional)
            if not openai_key:
                print("❌ OPENAI_API_KEY not set!")
                print("💡 Note: For VA strategy, use Streamlit app instead")
                continue
            
            print("⚠️  AI Categorization is not recommended for VA strategy.")
            confirm = input("Continue anyway? (y/n): ")
            if confirm.lower() != 'y':
                continue
            
            min_clients = input("Minimum clients following (default 2): ").strip()
            min_clients = int(min_clients) if min_clients else 2
            
            try:
                analyzer.categorize_pages(min_clients, force_recategorize=False)
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif choice == "13":
            # Re-categorize all (optional)
            if not openai_key:
                print("❌ OPENAI_API_KEY not set!")
                print("💡 Note: For VA strategy, use Streamlit app instead")
                continue
            
            print("⚠️  AI Categorization is not recommended for VA strategy.")
            confirm = input("Re-categorize ALL pages? (y/n): ")
            if confirm.lower() != 'y':
                continue
            
            min_clients = input("Minimum clients following (default 2): ").strip()
            min_clients = int(min_clients) if min_clients else 2
            
            try:
                analyzer.categorize_pages(min_clients, force_recategorize=True)
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif choice == "16":
            # List all clients
            analyzer.list_clients()
        
        elif choice == "15":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please select 1-16.")


if __name__ == "__main__":
    main()

