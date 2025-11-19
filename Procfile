# Railway runs the web service
# Streamlit on main port, sync API on port 8081
web: python -c "import subprocess, os; subprocess.Popen(['python', 'sync_api.py']); subprocess.run(['streamlit', 'run', 'categorize_app.py', '--server.port', os.environ.get('PORT', '8080'), '--server.address', '0.0.0.0'])"

# For scraping (runs on Railway, not as a service - use Railway CLI to trigger)
# To run: railway run --service web python railway_scraper.py [mode]


