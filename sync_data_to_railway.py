"""
Sync clients_data.json to Railway while preserving VA's categorization work

This script:
1. Downloads current data from Railway (preserves VA's categories/edits)
2. Merges new scraped data with existing data (preserves categories, contact info, etc.)
3. Uploads merged data back to Railway

Usage:
    python sync_data_to_railway.py
"""

import json
import os
import subprocess
import sys
from typing import Dict, Any

RAILWAY_SERVICE = "web"  # Your Railway service name
LOCAL_DATA_FILE = "clients_data.json"
RAILWAY_DATA_PATH = "/data/clients_data.json"  # Path in Railway volume


def run_railway_cmd(cmd: list) -> tuple[str, bool]:
    """Run a Railway CLI command"""
    try:
        result = subprocess.run(
            ["railway"] + cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout, True
    except subprocess.CalledProcessError as e:
        print(f"❌ Railway CLI error: {e.stderr}")
        return "", False
    except FileNotFoundError:
        print("❌ Railway CLI not found. Install it with: npm install -g @railway/cli")
        return "", False


def download_from_railway() -> Dict[str, Any] | None:
    """Download current data from Railway"""
    print("📥 Downloading current data from Railway...")
    
    # Railway CLI command to copy file from service
    # Note: Railway CLI might need different syntax - check their docs
    cmd = ["run", "--service", RAILWAY_SERVICE, "cat", RAILWAY_DATA_PATH]
    output, success = run_railway_cmd(cmd)
    
    if not success:
        print("⚠️  Could not download from Railway. Starting with empty data.")
        return {"clients": {}, "pages": {}}
    
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print("⚠️  Invalid JSON from Railway. Starting with empty data.")
        return {"clients": {}, "pages": {}}


def merge_data(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge new scraped data with existing data, preserving VA's work:
    - Preserves categories, contact methods, promo info, etc.
    - Updates follower counts, profile data, etc.
    """
    print("🔄 Merging data (preserving VA's work)...")
    
    merged = {
        "clients": new.get("clients", {}),  # Use new clients
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
        
        # Preserve website_promo_info if it exists (VA might have edited it)
        if "website_promo_info" in existing_page_data:
            # Merge: use new if available, otherwise keep existing
            if "website_promo_info" not in new_page_data or not new_page_data.get("website_promo_info"):
                merged_page["website_promo_info"] = existing_page_data["website_promo_info"]
        
        merged["pages"][username] = merged_page
    
    # Add any pages that exist in old data but not in new (shouldn't happen, but safety)
    for username, existing_page_data in existing_pages.items():
        if username not in merged["pages"]:
            merged["pages"][username] = existing_page_data
    
    return merged


def upload_to_railway(data: Dict[str, Any]) -> bool:
    """Upload merged data to Railway"""
    print("📤 Uploading merged data to Railway...")
    
    # Save to temp file
    temp_file = "clients_data_temp.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    try:
        # Railway CLI command to copy file to service
        # Note: Railway CLI syntax may vary - check their docs
        cmd = ["run", "--service", RAILWAY_SERVICE, "cp", temp_file, RAILWAY_DATA_PATH]
        _, success = run_railway_cmd(cmd)
        
        if success:
            print("✅ Data uploaded successfully!")
        else:
            print("❌ Upload failed. Check Railway CLI connection.")
        
        return success
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)


def main():
    """Main sync process"""
    print("=" * 60)
    print("🔄 Syncing clients_data.json to Railway")
    print("=" * 60)
    
    # Check if local file exists
    if not os.path.exists(LOCAL_DATA_FILE):
        print(f"❌ {LOCAL_DATA_FILE} not found locally!")
        return
    
    # Load local (new) data
    print(f"📖 Loading local {LOCAL_DATA_FILE}...")
    with open(LOCAL_DATA_FILE, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    
    # Download existing data from Railway
    existing_data = download_from_railway()
    
    # Merge (preserving VA's work)
    merged_data = merge_data(existing_data, new_data)
    
    # Upload merged data
    if upload_to_railway(merged_data):
        print("\n✅ Sync complete! VA's work has been preserved.")
    else:
        print("\n❌ Sync failed. Check Railway CLI connection and try again.")


if __name__ == "__main__":
    main()


