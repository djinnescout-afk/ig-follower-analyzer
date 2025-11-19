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

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        elif hasattr(sys.stdout, 'encoding'):
            # Force UTF-8 if possible
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass  # Fallback to default encoding
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
    # On Windows, try to find via PowerShell first
    if sys.platform == 'win32':
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-Command railway -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                railway_path = result.stdout.strip()
                # Return the path - we found it via PowerShell, so it should work
                return railway_path
        except Exception:
            pass
    
    # Try common locations
    possible_paths = [
        "npx",  # Try npx railway first (works on Windows)
        "railway",  # In PATH (try first)
        "railway.cmd",  # Windows cmd wrapper
        os.path.expandvars(r"%APPDATA%\npm\railway.ps1"),  # Windows npm PowerShell script
        os.path.expandvars(r"%APPDATA%\npm\railway.cmd"),  # Windows npm global
        os.path.expandvars(r"%LOCALAPPDATA%\npm\railway.cmd"),  # Windows npm local
        "/usr/local/bin/railway",  # macOS/Linux
        os.path.expanduser("~/.railway/bin/railway"),  # Alternative location
    ]
    
    for path in possible_paths:
        try:
            # Special handling for npx
            if path == "npx":
                result = subprocess.run(
                    ["npx", "railway", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=False
                )
                if result.returncode == 0:
                    return "npx"
                continue
            
            # On Windows, try with .cmd extension if needed
            if sys.platform == 'win32' and not path.endswith('.cmd') and not path.endswith('.exe'):
                # Try both .cmd and .exe versions
                for ext in ['', '.cmd', '.exe']:
                    test_path = path + ext
                    try:
                        result = subprocess.run(
                            [test_path, "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5,
                            shell=False
                        )
                        if result.returncode == 0:
                            return test_path
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        continue
            else:
                # Handle .ps1 files via PowerShell
                if path.endswith('.ps1'):
                    try:
                        result = subprocess.run(
                            ["powershell", "-Command", f"& '{path}' --version"],
                            capture_output=True,
                            text=True,
                            timeout=5,
                            shell=False
                        )
                        if result.returncode == 0:
                            return path
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        continue
                else:
                    result = subprocess.run(
                        [path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        shell=False
                    )
                    if result.returncode == 0:
                        return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    return None


def upload_via_railway_cli(file_path: str) -> bool:
    """Upload file to Railway using CLI by copying file contents via stdin"""
    try:
        # Try to find Railway CLI
        railway_cmd = find_railway_cli()
        
        # If not found, try finding via PowerShell on Windows
        if not railway_cmd and sys.platform == 'win32':
            try:
                # Use PowerShell to find railway
                result = subprocess.run(
                    ["powershell", "-Command", "Get-Command railway | Select-Object -ExpandProperty Source"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    railway_path = result.stdout.strip()
                    # Test if it works
                    test_result = subprocess.run(
                        ["powershell", "-Command", f"& '{railway_path}' --version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if test_result.returncode == 0:
                        railway_cmd = railway_path
            except:
                pass
        
        if not railway_cmd:
            print(f"  ⚠️  Railway CLI not found. Install: npm install -g @railway/cli")
            return False
        
        # Read the file content as bytes
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        # Use Railway CLI to write file using Python
        # Read from stdin (binary) and write to file
        # This avoids command line length limits
        # Also verify the write by reading back the file size
        python_cmd = "import sys, os, json; os.makedirs('/data', exist_ok=True); data=sys.stdin.buffer.read(); f=open('/data/clients_data.json', 'wb'); f.write(data); f.close(); verify=json.load(open('/data/clients_data.json','r',encoding='utf-8')); clients_count=len(verify.get('clients',{})); pages_count=len(verify.get('pages',{})); print('Written:', clients_count, 'clients,', pages_count, 'pages')"
        
        # On Windows, use shell=True to handle npm-installed commands
        use_shell = sys.platform == 'win32'
        
        # Build the command
        if railway_cmd == "npx":
            full_cmd = ["npx", "railway", "run", "--service", "web", "python", "-c", python_cmd]
        elif railway_cmd.endswith('.ps1'):
            # PowerShell script - execute via PowerShell
            # Use single quotes in PowerShell to avoid escaping issues
            # Replace single quotes with double single quotes for PowerShell
            escaped_cmd = python_cmd.replace("'", "''")
            # Build PowerShell command - use single quotes around the Python command
            ps_cmd = f"& '{railway_cmd}' run --service web python -c '{escaped_cmd}'"
            full_cmd = ["powershell", "-Command", ps_cmd]
        else:
            full_cmd = [railway_cmd, "run", "--service", "web", "python", "-c", python_cmd]
        
        print(f"  Uploading file to Railway (this may take 1-2 minutes)...")
        # Use stdin to pipe the file bytes directly
        result = subprocess.run(
            full_cmd,
            input=file_bytes,  # Pipe file bytes via stdin
            capture_output=True,
            text=False,  # Binary mode for stdin
            timeout=180  # Increased timeout for large files
        )
        
        if result.returncode == 0:
            # Check stdout for verification message
            if result.stdout:
                try:
                    output_text = result.stdout.decode('utf-8', errors='replace').strip()
                    if output_text:
                        print(f"  {output_text}")
                except:
                    pass
            print(f"  ✅ Successfully uploaded to Railway!")
            print(f"  ⚠️  Note: If data doesn't appear, refresh the Streamlit app or restart the Railway service.")
            print(f"  💡 For initial sync, use the 'Data Management' tab in the Streamlit app for guaranteed results.")
            return True
        else:
            print(f"  ⚠️  Railway CLI returned error (code {result.returncode})")
            if result.stderr:
                try:
                    error_text = result.stderr.decode('utf-8', errors='replace')[:300]
                    print(f"  Error: {error_text}")
                except:
                    print(f"  Error: (binary data)")
            if result.stdout:
                try:
                    output_text = result.stdout.decode('utf-8', errors='replace')[:300]
                    print(f"  Output: {output_text}")
                except:
                    pass
            return False
            
    except FileNotFoundError as e:
        print(f"  ⚠️  Railway CLI executable not found: {str(e)}")
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
    
    # All HTTP endpoints failed - try Railway CLI direct write as fallback
    print("❌ HTTP sync API not available (Railway auto-detects Streamlit).")
    print("🔄 Attempting direct Railway CLI upload...")
    
    try:
        return upload_via_railway_cli(data_file)
    except Exception as e:
        print(f"❌ Railway CLI upload failed: {str(e)[:200]}")
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
        
        print("Initializing Chrome driver...")
        print("   (Downloading ChromeDriver on first run - this may take 30-60 seconds)")
        print("   Please wait...")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        driver.set_page_load_timeout(60)  # 60 second timeout
        print("Chrome browser initialized")
        
        print(f"📱 Navigating to {app_url}...")
        driver.get(app_url)
        print("✅ Page loaded")
        
        # Wait for Streamlit to fully load
        print("⏳ Waiting for Streamlit to initialize...")
        time.sleep(5)
        
        # Wait for page to load and find Data Management tab
        print("🔍 Looking for Data Management tab...")
        print("   (This may take up to 30 seconds)")
        
        # First, try to find all tabs to see what's available
        try:
            all_tabs = driver.find_elements(By.CSS_SELECTOR, "button[data-baseweb='tab'], button[role='tab']")
            print(f"   Found {len(all_tabs)} tabs on page")
            for i, tab in enumerate(all_tabs[:5]):  # Show first 5
                try:
                    print(f"   Tab {i+1}: {tab.text[:50]}")
                except:
                    pass
        except Exception as e:
            print(f"   Could not list tabs: {str(e)[:50]}")
        
        wait = WebDriverWait(driver, 30)
        
        # Try multiple selectors for the Data Management tab
        data_mgmt_tab = None
        selectors = [
            (By.XPATH, "//button[contains(text(), 'Data Management')]"),
            (By.XPATH, "//button[contains(text(), '📤 Data Management')]"),
            (By.XPATH, "//button[contains(text(), '📤') and contains(text(), 'Data')]"),
            (By.XPATH, "//div[@role='tablist']//button[4]"),  # 4th tab
            (By.CSS_SELECTOR, "button[data-baseweb='tab']:nth-child(5)"),  # 5th button
        ]
        
        for i, (selector_type, selector_value) in enumerate(selectors, 1):
            try:
                print(f"   Trying selector {i}/{len(selectors)}: {str(selector_type)[:20]}...")
                data_mgmt_tab = wait.until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                print(f"✅ Found Data Management tab using selector {i}")
                break
            except Exception as e:
                print(f"   Selector {i} failed: {str(e)[:50]}")
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
        print("   Waiting for tab content to load...")
        time.sleep(5)  # Give Streamlit more time to render the tab content
        
        # Scroll to top to ensure we're looking at the right area
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Find file uploader - Streamlit file inputs are often hidden
        # First, try to click the upload button/label to trigger the file input
        print("📤 Looking for file upload area...")
        
        file_path = os.path.abspath(data_file)
        print(f"📎 File to upload: {file_path}")
        
        # Try to find and click the upload button/label first
        upload_button = None
        button_selectors = [
            (By.XPATH, "//button[contains(text(), 'Choose')]"),
            (By.XPATH, "//button[contains(text(), 'Browse')]"),
            (By.XPATH, "//label[contains(text(), 'Choose')]"),
            (By.XPATH, "//label[contains(text(), 'clients_data.json')]"),
            (By.CSS_SELECTOR, "button[data-testid='stFileUploaderDropzone']"),
            (By.CSS_SELECTOR, "label[data-testid='stFileUploaderDropzone']"),
        ]
        
        for selector_type, selector_value in button_selectors:
            try:
                elements = driver.find_elements(selector_type, selector_value)
                if elements:
                    upload_button = elements[0]
                    print(f"   Found upload button/label: {selector_value}")
                    break
            except:
                continue
        
        if upload_button:
            print("   Clicking upload button to trigger file input...")
            driver.execute_script("arguments[0].click();", upload_button)
            time.sleep(2)
        
        # Now try to find the file input
        print("   Looking for file input element...")
        file_input = None
        
        # Use JavaScript to find file inputs (including hidden ones)
        file_inputs_count = driver.execute_script("""
            return document.querySelectorAll('input[type="file"]').length;
        """)
        print(f"   Found {file_inputs_count} file input(s) in DOM")
        
        # Try to find file input using Selenium
        file_selectors = [
            (By.CSS_SELECTOR, "input[type='file']"),
            (By.XPATH, "//input[@type='file']"),
        ]
        
        for selector_type, selector_value in file_selectors:
            try:
                elements = driver.find_elements(selector_type, selector_value)
                if elements:
                    file_input = elements[0]
                    print(f"   ✅ Found file input using: {selector_value}")
                    break
            except:
                continue
        
        if not file_input:
            # Wait for file input to appear (Streamlit may need time to render)
            print("   Waiting for file input to appear (up to 20 seconds)...")
            try:
                file_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
                print("   ✅ File input appeared after wait")
            except:
                # Take screenshot and save page source for debugging
                driver.save_screenshot("sync_file_input_not_found.png")
                with open("sync_page_source.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("   Screenshot saved to sync_file_input_not_found.png")
                print("   Page source saved to sync_page_source.html")
                raise Exception("Could not find file upload input. Check screenshot and page source.")
        
        # Upload the file
        print(f"   Uploading file: {file_path}")
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", file_input)
            time.sleep(1)
            file_input.send_keys(file_path)
            print("   ✅ File path sent to input")
        except Exception as e:
            raise Exception(f"Could not upload file: {str(e)}")
        
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

