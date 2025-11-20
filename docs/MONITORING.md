# Monitoring & Alerts

Comprehensive monitoring setup for the IG Follower Analyzer system.

## Overview

Monitor three key areas:
1. **System Health**: API uptime, worker status, database connections
2. **Scrape Performance**: Success rates, coverage %, failed jobs
3. **Business Metrics**: Clients added, pages discovered, categorization progress

## Built-in Logging

All services use structured logging to stdout:

### API Logs
```
2025-11-20 10:00:00 - INFO - Received request: POST /api/scrapes/client-following
2025-11-20 10:00:01 - INFO - Created scrape run: abc-123 for client xyz-456
2025-11-20 10:00:01 - INFO - Response: 201 Created
```

### Worker Logs
```
2025-11-20 10:05:00 - INFO - Worker started, polling for jobs...
2025-11-20 10:05:10 - INFO - Processing job abc-123 for client xyz-456
2025-11-20 10:05:15 - INFO - Scraping following list for @username...
2025-11-20 10:08:30 - INFO - ✅ Job abc-123 completed: 2659 accounts, 99.8% coverage
```

## Platform Monitoring

### Render

Built-in monitoring for API + workers:

**Metrics Available:**
- CPU usage
- Memory usage
- Request rate
- Response times
- Error rates

**Access:**
https://dashboard.render.com → Your Service → Metrics

**Set Up Alerts:**
1. Go to service settings
2. "Notifications" tab
3. Add webhook or email for:
   - Service goes down
   - High error rate (>5%)
   - Memory/CPU threshold exceeded

### Vercel

Built-in monitoring for web UI:

**Metrics Available:**
- Page load times
- Function execution times
- Bandwidth usage
- Error rates

**Access:**
https://vercel.com/dashboard → Your Project → Analytics

**Alerts:**
Automatic email notifications for:
- Build failures
- Runtime errors in functions

### Supabase

Database monitoring:

**Metrics Available:**
- Query performance
- Connection pool usage
- Database size
- API usage

**Access:**
https://supabase.com/dashboard → Your Project → Reports

## Custom Monitoring

### 1. Health Check Endpoint

Add to `api/app/main.py`:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        result = supabase.table("clients").select("id").limit(1).execute()
        db_healthy = True
    except:
        db_healthy = False
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }
```

Monitor with UptimeRobot or similar (free):
- https://uptimerobot.com
- Check `/health` every 5 minutes
- Alert if down for 2+ checks

### 2. Scrape Coverage Alerts

Add to workers after completing a scrape:

```python
# In client_following_worker.py
def send_coverage_alert(username, coverage_percent):
    """Send alert if coverage is below threshold"""
    if coverage_percent < 95:
        # Option 1: Discord webhook
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url:
            requests.post(webhook_url, json={
                "content": f"⚠️ Low coverage alert!\n"
                           f"Client: @{username}\n"
                           f"Coverage: {coverage_percent:.1f}%\n"
                           f"Expected >95%"
            })
        
        # Option 2: Slack webhook
        slack_url = os.getenv("SLACK_WEBHOOK_URL")
        if slack_url:
            requests.post(slack_url, json={
                "text": f"⚠️ Low coverage: @{username} - {coverage_percent:.1f}%"
            })
        
        # Option 3: Email via SendGrid
        # ... implement email sending
```

Add environment variables to Render:
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 3. Failed Job Monitoring

Query Supabase for stuck jobs:

```python
# Add to API as /api/admin/stuck-jobs
@app.get("/api/admin/stuck-jobs")
async def get_stuck_jobs():
    """Find jobs stuck in processing for >10 minutes"""
    threshold = datetime.utcnow() - timedelta(minutes=10)
    
    result = supabase.table("scrape_runs")\
        .select("*")\
        .eq("status", "processing")\
        .lt("started_at", threshold.isoformat())\
        .execute()
    
    return {"stuck_jobs": result.data}
```

Set up a cron job to check this and reset if needed.

### 4. Business Metrics Dashboard

Add to API:

```python
@app.get("/api/stats")
async def get_stats():
    """Get system stats for monitoring"""
    # Total clients
    clients_count = supabase.table("clients")\
        .select("id", count="exact")\
        .execute()
    
    # Total pages
    pages_count = supabase.table("pages")\
        .select("id", count="exact")\
        .execute()
    
    # Recent scrapes (last 24h)
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    recent_scrapes = supabase.table("scrape_runs")\
        .select("status")\
        .gte("created_at", yesterday)\
        .execute()
    
    # Calculate success rate
    total = len(recent_scrapes.data)
    completed = len([s for s in recent_scrapes.data if s["status"] == "completed"])
    success_rate = (completed / total * 100) if total > 0 else 0
    
    return {
        "clients": clients_count.count,
        "pages": pages_count.count,
        "scrapes_24h": {
            "total": total,
            "completed": completed,
            "success_rate": success_rate
        },
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Alert Integrations

### Discord Webhook

1. Create Discord channel
2. Settings → Integrations → Webhooks → New Webhook
3. Copy webhook URL
4. Add to Render environment: `DISCORD_WEBHOOK_URL=...`

Send alerts:
```python
requests.post(webhook_url, json={"content": "Alert message"})
```

### Slack Webhook

1. Create Slack app: https://api.slack.com/apps
2. Enable Incoming Webhooks
3. Add to workspace and select channel
4. Copy webhook URL
5. Add to Render: `SLACK_WEBHOOK_URL=...`

Send alerts:
```python
requests.post(webhook_url, json={"text": "Alert message"})
```

### Email (SendGrid)

1. Sign up: https://sendgrid.com
2. Create API key
3. Add to Render: `SENDGRID_API_KEY=...`
4. Install: `pip install sendgrid`

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_alert_email(subject, body):
    message = Mail(
        from_email='alerts@yourdomain.com',
        to_emails='you@example.com',
        subject=subject,
        html_content=body
    )
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    sg.send(message)
```

## Monitoring Checklist

Daily:
- [ ] Check API uptime (UptimeRobot)
- [ ] Review scrape success rate (last 24h)
- [ ] Check worker logs for errors

Weekly:
- [ ] Review database size and performance
- [ ] Check Apify credit usage
- [ ] Verify all alerts are working

Monthly:
- [ ] Analyze scrape coverage trends
- [ ] Review and optimize slow queries
- [ ] Check for stuck jobs and reset if needed
- [ ] Review hosting costs vs usage

## Key Metrics to Track

### System Health
- **API Uptime**: Target 99.5%+
- **Worker Availability**: Both workers running 24/7
- **Database Response Time**: <100ms for most queries

### Scrape Performance
- **Success Rate**: Target >95%
- **Average Coverage**: Target >95%
- **Failed Job Rate**: Target <5%
- **Average Scrape Time**: 2-5 minutes per client

### Business Metrics
- **Clients Added**: Track growth over time
- **Pages Discovered**: Total unique pages
- **Pages per Client**: Average following count
- **High-Value Pages**: Pages followed by 3+ clients

## Dashboards

### Option 1: Grafana (Self-Hosted)

Free, open-source monitoring:
1. Deploy Grafana on Render
2. Connect to Supabase as data source
3. Create custom dashboards

### Option 2: Datadog (Managed)

Commercial monitoring service:
1. Sign up: https://www.datadoghq.com
2. Install agent on Render services
3. Use pre-built dashboards

### Option 3: Custom Dashboard

Build a simple monitoring page in Next.js:
- Query `/api/stats` endpoint
- Display key metrics
- Show recent scrape jobs
- Add coverage chart

## Error Handling Best Practices

### Worker Error Recovery

```python
# Wrap main loop in try-except
while True:
    try:
        job = get_next_job()
        process_job(job)
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        # Mark job as failed and continue
        mark_job_failed(job_id, str(e))
        time.sleep(5)  # Brief pause before continuing
```

### API Error Responses

Return helpful error messages:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )
```

### Graceful Degradation

If database is down:
- API returns 503 Service Unavailable
- Workers pause and retry after 30s
- Web UI shows "System maintenance" message

## Incident Response

### If API is Down
1. Check Render dashboard for service status
2. Review recent deploy logs
3. Check database connection
4. Restart service if needed
5. If issue persists, roll back to previous deploy

### If Workers Stop Processing
1. Check worker logs for errors
2. Verify database connection
3. Check Apify credits
4. Restart worker services
5. Manually reset stuck jobs in database

### If Scrapes Are Failing
1. Check Apify actor status
2. Verify Instagram accounts are valid
3. Check for rate limiting (wait 1-2 hours)
4. Review worker logs for specific errors

### If Database is Slow
1. Check Supabase dashboard for performance
2. Identify slow queries
3. Add indexes if needed
4. Upgrade to Pro tier if needed
5. Review connection pool settings

## Future Enhancements

- [ ] Real-time monitoring dashboard in web UI
- [ ] Automated anomaly detection
- [ ] Performance benchmarking over time
- [ ] Cost tracking and optimization alerts
- [ ] Predictive alerts (e.g., "database will fill up in 30 days")
- [ ] SLA tracking and reporting

