# IG Follower Analyzer - Workers

Background workers that process scraping jobs from the queue.

## Workers

### 1. Client Following Worker (`client_following_worker.py`)
- Polls `scrape_runs` table for `client_following` jobs
- Scrapes Instagram following lists via Apify
- Calculates coverage vs expected count
- Stores results in `pages` and `client_following` tables
- Updates scrape run status and results

### 2. Profile Scraper Worker (`profile_scrape_worker.py`)
- Polls `scrape_runs` table for `profile_scrape` jobs
- Scrapes profile details (bio, posts, profile pic) via Apify
- Downloads and base64-encodes images
- Detects promo openness and contact emails
- Stores results in `page_profiles` table

## Environment Variables

Required for all workers:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
APIFY_TOKEN=your-apify-token
```

## Local Development

### Run directly with Python
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="..."
export SUPABASE_SERVICE_KEY="..."
export APIFY_TOKEN="..."

# Run client following worker
python client_following_worker.py

# Or run profile scraper worker
python profile_scrape_worker.py
```

### Run with Docker
```bash
# Build image
docker build -t ig-worker .

# Run client following worker
docker run --env-file ../.env ig-worker python client_following_worker.py

# Run profile scraper worker
docker run --env-file ../.env ig-worker python profile_scrape_worker.py
```

### Run with Docker Compose
```bash
# From the workers directory
docker-compose up

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Deployment

### Render (Recommended)
1. Create a new **Background Worker** service
2. Connect your GitHub repo
3. Set build command: `cd workers && pip install -r requirements.txt`
4. Set start command: `python client_following_worker.py`
5. Add environment variables in Render dashboard
6. Deploy!

Create a second worker service for the profile scraper with start command: `python profile_scrape_worker.py`

### Railway
Similar to Render, create worker services with the appropriate start commands.

### Fly.io
1. Create `fly.toml` in workers directory
2. Deploy: `fly deploy`

## Monitoring

Workers log to stdout with structured logging:
- `INFO` level for normal operations
- `WARNING` for recoverable issues (failed images, missing data)
- `ERROR` for job failures

In production, pipe logs to a monitoring service like:
- Datadog
- Logtail
- CloudWatch
- Render Logs (built-in)

## Scaling

- Each worker runs a single-threaded poll loop
- To scale, run multiple worker instances
- Workers automatically compete for jobs (first to update status wins)
- For high throughput, run 2-5 instances of each worker type

## Health Checks

Workers don't expose HTTP endpoints. For health monitoring:
- Check if process is running
- Monitor log output for errors
- Query `scrape_runs` table for stuck jobs (processing > 10 minutes)

## Troubleshooting

### Worker not picking up jobs
- Check environment variables are set correctly
- Verify Supabase connection: check service key permissions
- Check `scrape_runs` table has `pending` jobs with correct `scrape_type`

### Jobs stuck in "processing"
- Worker likely crashed mid-job
- Manually reset: `UPDATE scrape_runs SET status='pending' WHERE status='processing' AND started_at < NOW() - INTERVAL '10 minutes'`

### Apify errors
- Check APIFY_TOKEN is valid and has credits
- Review Apify actor logs in Apify console
- Some Instagram accounts may be private/deleted

### Image download failures
- Non-critical: worker will continue with null images
- Check network connectivity
- Instagram image URLs expire quickly (scrape profile soon after getting URL)

