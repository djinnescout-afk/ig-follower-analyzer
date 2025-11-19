"""
Simple HTTP API for syncing data to Railway volume
Runs alongside Streamlit to accept data uploads from terminal
"""

from flask import Flask, request, jsonify, Response
import json
import os
import requests
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "/data/clients_data.json" if os.path.exists("/data") else "clients_data.json"
STREAMLIT_URL = os.environ.get("STREAMLIT_URL", "http://localhost:8080")


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
        
        # Preserve website_promo_info if it exists
        if "website_promo_info" in existing_page_data:
            if "website_promo_info" not in new_page_data or not new_page_data.get("website_promo_info"):
                merged_page["website_promo_info"] = existing_page_data["website_promo_info"]
        
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


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_streamlit(path):
    """Proxy all other requests to Streamlit"""
    try:
        # Forward request to Streamlit
        streamlit_path = f"/{path}" if path else "/"
        if request.query_string:
            streamlit_path += f"?{request.query_string.decode()}"
        
        # Forward the request
        resp = requests.request(
            method=request.method,
            url=f"{STREAMLIT_URL}{streamlit_path}",
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=30
        )
        
        # Return response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        
        return Response(resp.content, resp.status_code, headers)
    except Exception as e:
        return jsonify({"error": f"Proxy error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("SYNC_PORT", 8080))
    print(f"🌐 Flask sync API listening on port {port}")
    print(f"   /sync - Data sync endpoint")
    print(f"   /health - Health check")
    print(f"   /* - Proxied to Streamlit")
    app.run(host="0.0.0.0", port=port, threaded=True)

