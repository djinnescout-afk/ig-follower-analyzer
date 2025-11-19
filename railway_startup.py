#!/usr/bin/env python3
"""
Railway startup script - runs Flask sync API and Streamlit app
"""

import subprocess
import os
import sys
import time
import signal
import atexit

def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    print("\n🛑 Shutting down services...")
    if 'streamlit_process' in globals():
        streamlit_process.terminate()
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
print("=" * 60)
print("🚀 RAILWAY STARTUP SCRIPT")
print("=" * 60)
print(f"📁 Working directory: {os.getcwd()}")
print(f"🐍 Python: {sys.executable}")
print(f"🔌 PORT env var: {os.environ.get('PORT', 'NOT SET')}")

streamlit_port = "8080"
print(f"\n🚀 Starting Streamlit app on internal port {streamlit_port}...")
streamlit_process = subprocess.Popen([
    sys.executable, "-m", "streamlit", "run", "categorize_app.py",
    "--server.port", streamlit_port,
    "--server.address", "0.0.0.0"
], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Register cleanup
atexit.register(lambda: streamlit_process.terminate())

# Give Streamlit a moment to start
print("⏳ Waiting for Streamlit to start...")
time.sleep(5)
print("✅ Streamlit should be running")

# Start Flask sync API (foreground - handles /sync and proxies to Streamlit)
main_port = os.environ.get("PORT", "8080")
print(f"\n🚀 Starting Flask sync API (proxy mode) on port {main_port}...")
print(f"   Streamlit URL: http://localhost:{streamlit_port}")
print(f"   Flask will handle /sync and proxy other requests to Streamlit")
print("=" * 60)

# Run Flask in foreground (this blocks)
flask_env = {**os.environ, "SYNC_PORT": main_port, "STREAMLIT_URL": f"http://localhost:{streamlit_port}"}
try:
    subprocess.run([
        sys.executable, "sync_api.py"],
        env=flask_env
    )
except KeyboardInterrupt:
    print("\n🛑 Shutting down...")
    streamlit_process.terminate()
    streamlit_process.wait()

