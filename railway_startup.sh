#!/bin/bash
# Startup script for Railway - runs before Streamlit

# If clients_data.json doesn't exist in volume, create empty structure
if [ ! -f "/data/clients_data.json" ]; then
    echo '{"clients": {}, "pages": {}}' > /data/clients_data.json
    echo "Created empty /data/clients_data.json"
fi

# Start Streamlit
exec streamlit run categorize_app.py --server.port $PORT --server.address 0.0.0.0

