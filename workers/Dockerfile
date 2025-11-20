FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker scripts
COPY client_following_worker.py .
COPY profile_scrape_worker.py .

# Default to client following worker (can be overridden)
CMD ["python", "client_following_worker.py"]

