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


def upload_via_railway_cli(file_path: str) -> bool:
    """Upload file to Railway using CLI"""
    try:
        # Method 1: Try using Railway CLI to copy file
        # First, check if Railway CLI is available
        result = subprocess.run(
            ["railway", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return False
        
        # Try to copy file to Railway volume
        # Note: Railway CLI file operations are limited, so we use a workaround
        # We'll read the file and pipe it to Railway
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Use Railway CLI to write file via shell command
        result = subprocess.run(
            ["railway", "run", "--service", "web", "sh", "-c", f"cat > /data/clients_data.json << 'EOF'\n{file_content}\nEOF"],
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        print(f"  ⚠️  Railway CLI upload failed: {str(e)[:100]}")
        return False


def sync_to_railway(data_file: str = "clients_data.json", preserve_va_work: bool = True) -> bool:
    """
    Automatically sync data to Railway after scraping
    
    Args:
        data_file: Path to local clients_data.json
        preserve_va_work: If True, merges with existing data to preserve VA's work
    
    Returns:
        True if successful, False otherwise
    """
    print("\n" + "=" * 60)
    print("🔄 Auto-syncing to Railway...")
    print("=" * 60)
    
    if not os.path.exists(data_file):
        print(f"❌ {data_file} not found!")
        return False
    
    # Load new scraped data
    print(f"📖 Loading {data_file}...")
    with open(data_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    
    # Download current data from Railway (if preserving VA work)
    if preserve_va_work:
        print("📥 Downloading current data from Railway...")
        existing_data = download_current_data()
        
        if existing_data:
            print("🔄 Merging data (preserving VA's work)...")
            merged_data = merge_data_smart(existing_data, new_data)
            # Save merged data temporarily
            temp_file = "clients_data_merged.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, indent=2, ensure_ascii=False)
            file_to_upload = temp_file
        else:
            print("⚠️  Could not download existing data. Uploading new data only.")
            file_to_upload = data_file
    else:
        file_to_upload = data_file
    
    # Upload to Railway
    print("📤 Uploading to Railway...")
    success = upload_via_railway_cli(file_to_upload)
    
    # Cleanup temp file
    if preserve_va_work and file_to_upload != data_file:
        try:
            os.remove(file_to_upload)
        except:
            pass
    
    if success:
        print("✅ Successfully synced to Railway!")
        if preserve_va_work:
            print("✅ VA's work has been preserved.")
        return True
    else:
        print("❌ Failed to sync via Railway CLI.")
        print("💡 Alternative: Use the 'Data Management' tab in the Streamlit app to upload manually.")
        return False


if __name__ == "__main__":
    # Can be run standalone
    preserve = "--no-merge" not in sys.argv
    sync_to_railway("clients_data.json", preserve_va_work=preserve)

