"""
Automated Railway data sync - preserves VA's work when uploading new scraped data
"""

import json
import os
import subprocess
import sys
import requests
from typing import Dict, Optional

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
    Sync data to Railway - currently requires manual upload via Streamlit UI
    
    Args:
        data_file: Path to local clients_data.json
        preserve_va_work: If True, merges with existing data to preserve VA's work
    
    Returns:
        True if file is ready for upload, False otherwise
    """
    print("\n" + "=" * 60)
    print("🔄 Railway Sync - Manual Upload Required")
    print("=" * 60)
    
    if not os.path.exists(data_file):
        print(f"❌ {data_file} not found!")
        return False
    
    # Check file stats
    file_size = os.path.getsize(data_file)
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    clients_count = len(data.get("clients", {}))
    pages_count = len(data.get("pages", {}))
    
    print(f"📊 Local file ready for upload:")
    print(f"   📁 File: {data_file}")
    print(f"   📊 Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print(f"   👥 Clients: {clients_count}")
    print(f"   📄 Pages: {pages_count}")
    print()
    print("📤 To sync to Railway:")
    print(f"   1. Open: {RAILWAY_APP_URL}")
    print("   2. Go to the 'Data Management' tab")
    print(f"   3. Upload this file: {os.path.abspath(data_file)}")
    print("   4. The app will smart-merge, preserving VA's work")
    print()
    print("✅ File is ready for upload!")
    
    return True


if __name__ == "__main__":
    # Can be run standalone
    preserve = "--no-merge" not in sys.argv
    sync_to_railway("clients_data.json", preserve_va_work=preserve)

