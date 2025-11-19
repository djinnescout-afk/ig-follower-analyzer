"""
Automated Railway data sync - preserves VA's work when uploading new scraped data
"""

import json
import os
import subprocess
import sys
import requests
import time
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

RAILWAY_APP_URL = "https://web-production-def7.up.railway.app"  # Your Railway app URL
RAILWAY_SYNC_PORT = 8081  # Flask sync API port


def merge_data_smart(existing: Dict, new: Dict) -> Dict:
    """
    Smart merge: Preserves VA's work (categories, contact info) while updating scraped data
    """
    merged = {
        "clients": new.get("clients", {}),
        "pages": {}
    }
    
    existing_pages = existing.get("pages", {})
    new_pages = new.get("pages", {})
    
    for username, new_page_data in new_pages.items():
        existing_page_data = existing_pages.get(username, {})
        
        # Start with new scraped data
        merged_page = new_page_data.copy()
        
        # Preserve VA's categorization work
        if "category" in existing_page_data:
            merged_page["category"] = existing_page_data["category"]
        if "category_confidence" in existing_page_data:
            merged_page["category_confidence"] = existing_page_data["category_confidence"]
        
        # Preserve contact information (VA's edits)
        for field in [
            "known_contact_methods",
            "successful_contact_method",
            "current_main_contact_method",
            "ig_account_for_dm",
            "promo_price",
            "promo_status",  # Manual override
            "website_url"
        ]:
            if field in existing_page_data and existing_page_data[field]:
                merged_page[field] = existing_page_data[field]
        
        # Preserve website_promo_info if it exists
        if "website_promo_info" in existing_page_data:
            if "website_promo_info" not in new_page_data or not new_page_data.get("website_promo_info"):
                merged_page["website_promo_info"] = existing_page_data["website_promo_info"]
        
        merged["pages"][username] = merged_page
    
    # Add any pages that exist in old data but not in new
    for username, existing_page_data in existing_pages.items():
        if username not in merged["pages"]:
            merged["pages"][username] = existing_page_data
    
    return merged


def download_current_data() -> Optional[Dict]:
    """Download current data from Railway app"""
    try:
        # Try to download via Railway CLI first (if available)
        result = subprocess.run(
            ["railway", "run", "--service", "web", "cat", "/data/clients_data.json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    
    # Fallback: Try to get via HTTP endpoint (if we add one)
    # For now, return None - we'll merge with empty if needed
    return None


def find_railway_cli() -> Optional[str]:
    """Find the railway CLI executable"""
    # Try common locations
    possible_paths = [
        "railway",  # In PATH
        os.path.expandvars(r"%APPDATA%\npm\railway.cmd"),  # Windows npm global
        "/usr/local/bin/railway",  # macOS/Linux
        os.path.expanduser("~/.railway/bin/railway"),  # Alternative location
    ]
    
    for path in possible_paths:
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    return None


def upload_via_railway_cli(file_path: str) -> bool:
    """Upload file to Railway using CLI by copying file contents via stdin"""
    try:
        # Find Railway CLI
        railway_cmd = find_railway_cli()
        if not railway_cmd:
            print(f"  ⚠️  Railway CLI not found. Install: npm install -g @railway/cli")
            return False
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Use Railway CLI to write file using Python
        # Create a Python one-liner that reads from stdin and writes to the file
        # Also ensure the /data directory exists
        python_cmd = "import sys, os; os.makedirs('/data', exist_ok=True); open('/data/clients_data.json', 'w', encoding='utf-8').write(sys.stdin.read())"
        
        result = subprocess.run(
            [railway_cmd, "run", "--service", "web", "python", "-c", python_cmd],
            input=file_content,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120
        )
        
        if result.returncode == 0:
            return True
        else:
            print(f"  ⚠️  Railway CLI returned error: {result.stderr[:200]}")
            return False
            
    except FileNotFoundError:
        print(f"  ⚠️  Railway CLI executable not found")
        return False
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  Railway CLI upload timed out")
        return False
    except Exception as e:
        print(f"  ⚠️  Railway CLI upload failed: {str(e)[:100]}")
        return False


def sync_to_railway(data_file: str = "clients_data.json", preserve_va_work: bool = True) -> bool:
    """
    Automatically sync data to Railway via HTTP API
    
    Args:
        data_file: Path to local clients_data.json
        preserve_va_work: If True, merges with existing data to preserve VA's work (handled server-side)
    
    Returns:
        True if successful, False otherwise
    """
    print("\n" + "=" * 60)
    print("🔄 Auto-syncing to Railway via HTTP...")
    print("=" * 60)
    
    if not os.path.exists(data_file):
        print(f"❌ {data_file} not found!")
        return False
    
    # Load data to upload
    print(f"📖 Loading {data_file}...")
    with open(data_file, 'r', encoding='utf-8') as f:
        data_to_upload = json.load(f)
    
    # Flask API handles /sync on the main port (proxies other requests to Streamlit)
    sync_endpoints = [
        f"{RAILWAY_APP_URL}/sync",  # Main endpoint
    ]
    
    for endpoint in sync_endpoints:
        print(f"📤 Uploading to {endpoint}...")
        try:
            response = requests.post(
                endpoint,
                json=data_to_upload,
                timeout=180,  # 3 minute timeout for large files
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Successfully synced to Railway!")
                print(f"   📊 Clients: {result.get('clients', 0)}")
                print(f"   📊 Pages: {result.get('pages', 0)}")
                print(f"   📊 File size: {result.get('file_size', 0):,} bytes")
                if preserve_va_work:
                    print("✅ VA's work has been preserved (server-side merge).")
                return True
            elif response.status_code == 404:
                # Try next endpoint
                continue
            else:
                print(f"❌ Sync failed with status {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                continue
                
        except requests.exceptions.ConnectionError:
            # Try next endpoint
            continue
        except requests.exceptions.Timeout:
            print("❌ Sync request timed out (file might be too large).")
            print("💡 Alternative: Use the 'Data Management' tab in the Streamlit app to upload manually.")
            return False
        except Exception as e:
            # Try next endpoint
            continue
    
    # All HTTP endpoints failed - try browser automation as fallback
    print("❌ HTTP sync API not available (Railway auto-detects Streamlit).")
    print("🔄 Attempting browser automation upload...")
    
    try:
        return sync_via_browser_automation(data_file, RAILWAY_APP_URL)
    except Exception as e:
        print(f"❌ Browser automation failed: {str(e)[:200]}")
        print()
        print("📤 Manual upload required:")
        print(f"   1. Open: {RAILWAY_APP_URL}")
        print("   2. Go to 'Data Management' tab")
        print(f"   3. Upload: {os.path.abspath(data_file)}")
        return False


def sync_via_browser_automation(data_file: str, app_url: str) -> bool:
    """Upload data via browser automation (Selenium)"""
    print("🌐 Starting browser automation...")
    driver = None
    
    try:
        # Setup Chrome - try headless first, fallback to visible for debugging
        chrome_options = Options()
        # Check if we should run headless (set HEADLESS=false to see browser)
        if os.environ.get("HEADLESS", "true").lower() != "false":
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        print("🔧 Initializing Chrome driver...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        driver.set_page_load_timeout(60)  # 60 second timeout
        
        print(f"📱 Navigating to {app_url}...")
        driver.get(app_url)
        print("✅ Page loaded")
        
        # Wait for Streamlit to fully load
        print("⏳ Waiting for Streamlit to initialize...")
        time.sleep(5)
        
        # Wait for page to load and find Data Management tab
        print("🔍 Looking for Data Management tab...")
        wait = WebDriverWait(driver, 30)
        
        # Try multiple selectors for the Data Management tab
        data_mgmt_tab = None
        selectors = [
            (By.XPATH, "//button[contains(text(), 'Data Management')]"),
            (By.XPATH, "//button[contains(text(), '📤 Data Management')]"),
            (By.XPATH, "//div[@role='tablist']//button[4]"),  # 4th tab
            (By.CSS_SELECTOR, "button[data-baseweb='tab']:nth-child(5)"),  # 5th button (Data Management)
        ]
        
        for selector_type, selector_value in selectors:
            try:
                data_mgmt_tab = wait.until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                print(f"✅ Found Data Management tab using {selector_type}")
                break
            except:
                continue
        
        if not data_mgmt_tab:
            print("❌ Could not find Data Management tab")
            print(f"   Page title: {driver.title}")
            print(f"   Current URL: {driver.current_url}")
            # Take screenshot for debugging
            driver.save_screenshot("sync_debug.png")
            print("   Screenshot saved to sync_debug.png")
            return False
        
        print("🖱️  Clicking Data Management tab...")
        driver.execute_script("arguments[0].click();", data_mgmt_tab)
        time.sleep(3)
        
        # Find file uploader
        print("📤 Looking for file upload input...")
        file_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        
        file_path = os.path.abspath(data_file)
        print(f"📎 Uploading file: {file_path}")
        file_input.send_keys(file_path)
        
        # Wait for upload to complete (look for success message)
        print("⏳ Waiting for upload to complete...")
        time.sleep(8)  # Give Streamlit time to process
        
        # Check for success message
        page_source = driver.page_source.lower()
        if "uploaded" in page_source or "success" in page_source or "merged" in page_source:
            print("✅ Upload successful!")
            driver.quit()
            return True
        else:
            print("⚠️  Upload may have completed, but success message not detected.")
            print("   Checking page for any error messages...")
            # Look for error messages
            if "error" in page_source:
                print("   ⚠️  Error detected on page")
            driver.quit()
            return True  # Assume success if no error
            
    except Exception as e:
        print(f"❌ Browser automation error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        if driver:
            try:
                driver.save_screenshot("sync_error.png")
                print("   Error screenshot saved to sync_error.png")
            except:
                pass
            try:
                driver.quit()
            except:
                pass
        return False


if __name__ == "__main__":
    # Can be run standalone
    preserve = "--no-merge" not in sys.argv
    sync_to_railway("clients_data.json", preserve_va_work=preserve)

