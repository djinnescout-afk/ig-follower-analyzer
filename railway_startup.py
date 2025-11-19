#!/usr/bin/env python3
"""
Railway startup script - runs Flask sync API and Streamlit app
"""

import subprocess
import os
import sys
import time
import signal

def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    print("\n🛑 Shutting down services...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Ensure /data directory exists
if os.path.exists("/data") and not os.path.exists("/data/clients_data.json"):
    import json
    with open("/data/clients_data.json", 'w', encoding='utf-8') as f:
        json.dump({"clients": {}, "pages": {}}, f, indent=2)
    print("📝 Created empty /data/clients_data.json")

# Start Streamlit in background on internal port
print("🚀 Starting Streamlit app on internal port 8080...")
streamlit_port = "8080"
streamlit_process = subprocess.Popen([
    sys.executable, "-m", "streamlit", "run", "categorize_app.py",
    "--server.port", streamlit_port,
    "--server.address", "0.0.0.0"
])

# Give Streamlit a moment to start
time.sleep(3)

# Start Flask sync API (foreground - handles /sync and proxies to Streamlit)
print("🚀 Starting Flask sync API (proxy mode) on port $PORT...")
main_port = os.environ.get("PORT", "8080")
flask_process = subprocess.run([
    sys.executable, "sync_api.py"],
    env={**os.environ, "SYNC_PORT": main_port, "STREAMLIT_URL": f"http://localhost:{streamlit_port}"}
)

# If Streamlit exits, kill Flask too
flask_process.terminate()
flask_process.wait()

