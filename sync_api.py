"""
Simple HTTP API for syncing data to Railway volume
Runs alongside Streamlit to accept data uploads from terminal
"""

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "/data/clients_data.json" if os.path.exists("/data") else "clients_data.json"


def merge_data_smart(existing: dict, new: dict) -> dict:
    """Smart merge preserving VA's work"""
    merged = {
        "clients": new.get("clients", {}),
        "pages": {}
    }
    
    existing_pages = existing.get("pages", {})
    new_pages = new.get("pages", {})
    
    for username, new_page_data in new_pages.items():
        existing_page_data = existing_pages.get(username, {})
        merged_page = new_page_data.copy()
        
        # Preserve VA's categorization
        for field in ["category", "category_confidence"]:
            if field in existing_page_data:
                merged_page[field] = existing_page_data[field]
        
        # Preserve contact info
        for field in [
            "known_contact_methods", "successful_contact_method",
            "current_main_contact_method", "ig_account_for_dm",
            "promo_price", "promo_status", "website_url"
        ]:
            if field in existing_page_data and existing_page_data[field]:
                merged_page[field] = existing_page_data[field]
        
        merged["pages"][username] = merged_page
    
    # Add pages only in existing
    for username, existing_page_data in existing_pages.items():
        if username not in merged["pages"]:
            merged["pages"][username] = existing_page_data
    
    return merged


@app.route('/sync', methods=['POST'])
def sync_data():
    """Accept JSON data and save to volume"""
    try:
        new_data = request.get_json()
        
        if not new_data or not isinstance(new_data, dict):
            return jsonify({"error": "Invalid JSON data"}), 400
        
        # Load existing data
        existing_data = {}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception:
                pass  # If file is corrupt, start fresh
        
        # Merge if existing data has content
        if existing_data.get("clients") or existing_data.get("pages"):
            merged_data = merge_data_smart(existing_data, new_data)
        else:
            merged_data = new_data
        
        # Save
        merged_data["last_updated"] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(DATA_FILE) if os.path.dirname(DATA_FILE) else ".", exist_ok=True)
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            "success": True,
            "clients": len(merged_data.get("clients", {})),
            "pages": len(merged_data.get("pages", {})),
            "file_size": os.path.getsize(DATA_FILE)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    file_exists = os.path.exists(DATA_FILE)
    file_size = os.path.getsize(DATA_FILE) if file_exists else 0
    
    return jsonify({
        "status": "ok",
        "data_file": DATA_FILE,
        "file_exists": file_exists,
        "file_size": file_size
    })


if __name__ == "__main__":
    port = int(os.environ.get("SYNC_PORT", 8081))
    app.run(host="0.0.0.0", port=port)

