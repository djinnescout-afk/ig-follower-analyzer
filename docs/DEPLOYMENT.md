# Deployment Guide

Complete guide to deploying the IG Follower Analyzer cloud-native stack.

## Architecture Overview

```
┌─────────────┐
│  Vercel     │  ← Next.js Web UI
│  (Web)      │
└──────┬──────┘
       │ API calls
       ▼
┌─────────────┐
│  Render     │  ← FastAPI Backend
│  (API)      │
└──────┬──────┘
       │ Queue jobs
       ▼
┌─────────────┐     ┌──────────────┐
│  Render     │────▶│  Supabase    │
│  (Workers)  │     │  (Database)  │
└─────────────┘     └──────────────┘
       │
       ▼ Apify API
┌─────────────┐
│  Instagram  │
└─────────────┘
```

## Prerequisites

1. **Supabase Account** (free tier works)
   - Sign up at https://supabase.com
   - Create a new project
   - Note your `Project URL` and `service_role` key

2. **Apify Account**
   - Sign up at https://apify.com
   - Add credits ($5-10 to start)
   - Get your API token

3. **GitHub Repository**
   - Push your code to GitHub
   - Will be used for CI/CD

4. **Hosting Accounts** (all have free tiers)
   - Vercel (for web UI)
   - Render (for API + workers)

## Step 1: Set Up Supabase Database

### Create Tables

Run the SQL from `docs/DATA_MODEL_SUPABASE.md` in the Supabase SQL Editor:

```sql
-- Copy and paste the CREATE TABLE statements from DATA_MODEL_SUPABASE.md
-- This creates: clients, pages, client_following, scrape_runs, page_profiles
```

### Enable Row Level Security (RLS)

For now, disable RLS since we're using service_role key:

```sql
ALTER TABLE clients DISABLE ROW LEVEL SECURITY;
ALTER TABLE pages DISABLE ROW LEVEL SECURITY;
ALTER TABLE client_following DISABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_runs DISABLE ROW LEVEL SECURITY;
ALTER TABLE page_profiles DISABLE ROW LEVEL SECURITY;
```

Later, you can add RLS policies for multi-user access.

### Get Credentials

1. Go to Project Settings → API
2. Copy `Project URL` (e.g., `https://xxx.supabase.co`)
3. Copy `service_role` key (under "Project API keys" → service_role)

## Step 2: Deploy API to Render

### Create Web Service

1. Go to https://render.com
2. Click "New" → "Web Service"
3. Connect your GitHub repo
4. Configure:
   - **Name**: `ig-analyzer-api`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free (or Starter for better performance)

### Add Environment Variables

In Render dashboard, add:
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
APIFY_TOKEN=your-apify-token
```

### Deploy

Click "Create Web Service" - Render will auto-deploy.

Note the service URL (e.g., `https://ig-analyzer-api.onrender.com`)

## Step 3: Deploy Workers to Render

### Client Following Worker

1. Create new "Background Worker" service
2. Configure:
   - **Name**: `ig-worker-following`
   - **Root Directory**: `workers`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python client_following_worker.py`
   - Add same environment variables as API

### Profile Scraper Worker

1. Create another "Background Worker" service
2. Configure:
   - **Name**: `ig-worker-profile`
   - **Root Directory**: `workers`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python profile_scrape_worker.py`
   - Add same environment variables

## Step 4: Deploy Web UI to Vercel

### Connect GitHub

1. Go to https://vercel.com
2. Click "Add New" → "Project"
3. Import your GitHub repo
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `web`
   - **Build Command**: (auto-detected)
   - **Output Directory**: (auto-detected)

### Add Environment Variable

Add to Vercel project settings:
```
NEXT_PUBLIC_API_URL=https://ig-analyzer-api.onrender.com
```

(Use your actual API URL from Step 2)

### Deploy

Click "Deploy" - Vercel will auto-deploy and give you a URL.

## Step 5: Migrate Existing Data

If you have existing `clients_data.json`, migrate it:

```bash
cd ig-follower-analyzer
python scripts/migrate_clients_json.py
```

This will:
- Read `clients_data.json`
- Upload clients and pages to Supabase
- Preserve all existing data

## Step 6: Test the System

### 1. Open Web UI

Visit your Vercel URL (e.g., `https://ig-analyzer.vercel.app`)

### 2. Add a Test Client

- Go to "Clients" tab
- Click "Add Client"
- Enter test data
- Submit

### 3. Trigger a Scrape

- Select the client
- Click "Scrape Selected"
- Go to "Scrape Jobs" tab
- Watch it process in real-time

### 4. Check Results

- Once completed, go to "Pages" tab
- You should see pages the client follows
- Click a page to view details

## Monitoring & Logs

### Render Logs

- API: https://dashboard.render.com → your service → Logs
- Workers: Check each worker service logs

### Vercel Logs

- Functions: https://vercel.com/dashboard → your project → Logs

### Supabase Logs

- Database: Supabase dashboard → Logs

## Auto-Deploy Setup

Once connected to GitHub:

- **Push to `main`** → Auto-deploys all services
- **Pull Request** → Runs CI tests
- **Vercel** → Auto-creates preview deployments

## Cost Estimates

### Free Tier (Development)

- **Supabase**: Free (up to 500MB database)
- **Render API**: Free (spins down after 15min inactivity)
- **Render Workers**: 2 workers × Free tier
- **Vercel**: Free (unlimited bandwidth)
- **Apify**: Pay-per-use (~$0.10-0.50 per scrape)

**Total**: $0/month + Apify usage

### Production (Paid Tier)

- **Supabase Pro**: $25/month (8GB database, better performance)
- **Render Starter**: $7/month per service × 3 = $21/month
- **Vercel Pro**: $20/month (custom domains, more bandwidth)
- **Apify**: ~$20-50/month depending on scraping volume

**Total**: ~$66-96/month + Apify usage

## Scaling

### Horizontal Scaling

**Workers**: Run 2-5 instances of each worker type for higher throughput.

In Render:
- Go to worker service
- "Manual Deploy" → "Scale"
- Increase instance count

**API**: Render auto-scales (Starter tier and up).

### Vertical Scaling

Upgrade instance types in Render for more CPU/RAM.

### Database Scaling

Supabase automatically handles most scaling. Upgrade to Pro for:
- More storage
- Better performance
- Daily backups

## Security

### Environment Variables

- Never commit `.env` files
- Use hosting platform secret management
- Rotate keys periodically

### API Keys

- Store in environment variables only
- Use `service_role` key for backend (never expose to frontend)
- For multi-user, implement API authentication

### CORS

API has CORS enabled for all origins. In production, restrict to your domain:

```python
# api/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.vercel.app"],  # Restrict
    ...
)
```

## Troubleshooting

### API Not Connecting

- Check `NEXT_PUBLIC_API_URL` in Vercel
- Verify API is deployed and running on Render
- Check Render logs for errors

### Workers Not Processing Jobs

- Check worker logs on Render
- Verify environment variables are set
- Check Supabase connection (run logs should show "Worker started")

### Scrapes Failing

- Check Apify credits
- Verify `APIFY_TOKEN` is correct
- Check worker logs for specific errors
- Some Instagram accounts may be private/deleted

### Database Connection Issues

- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- Check Supabase project is not paused (free tier pauses after 7 days inactivity)
- Check database connection limit (increase in Supabase settings if needed)

## Backup & Recovery

### Database Backups

Supabase Pro includes daily backups. For free tier:

```bash
# Export via Supabase dashboard: Database → Backups → Download
# Or use pg_dump via Supabase connection string
```

### Code Backups

GitHub is your source of truth. Tag releases:

```bash
git tag v1.0.0
git push origin v1.0.0
```

### Data Export

Use the migration script in reverse to export data back to JSON if needed.

## Next Steps

- Set up custom domain (Vercel supports this easily)
- Add authentication for multi-user access
- Set up monitoring/alerts (see `MONITORING.md`)
- Configure auto-scaling rules
- Implement rate limiting on API

## Support

For issues:
1. Check service logs
2. Review this guide
3. Check GitHub Issues
4. Contact platform support (Render, Vercel, Supabase)

