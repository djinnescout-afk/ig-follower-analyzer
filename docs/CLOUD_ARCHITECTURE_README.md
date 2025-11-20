# IG Follower Analyzer - Cloud-Native Architecture 🚀

Complete cloud-based system for managing Instagram client following lists, with a web dashboard for VAs.

## What's New?

### Old System (File-Based)
- ❌ Manual CLI on local machine
- ❌ JSON file storage (132MB, unscalable)
- ❌ Manual Railway syncs
- ❌ Single-user, local-only
- ❌ No real-time updates

### New System (Cloud-Native)
- ✅ Modern web dashboard (accessible anywhere)
- ✅ Managed database (Supabase PostgreSQL)
- ✅ Background workers (automatic scraping)
- ✅ REST API (programmatic access)
- ✅ Multi-user ready
- ✅ Real-time job monitoring
- ✅ Auto-deploy via GitHub
- ✅ Scalable to 1000s of clients

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                      FRONTEND                             │
│  Next.js Web UI (Vercel) - VA Dashboard                  │
│  • Add clients                                           │
│  • Trigger scrapes                                       │
│  • Browse pages                                          │
│  • Monitor jobs                                          │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTPS/REST API
┌────────────────────▼─────────────────────────────────────┐
│                      BACKEND API                          │
│  FastAPI (Render) - Business Logic                       │
│  • /api/clients - CRUD operations                        │
│  • /api/pages - Browse & filter                          │
│  • /api/scrapes - Queue & monitor jobs                   │
└────────────────────┬─────────────────────────────────────┘
                     │ Queue jobs
┌────────────────────▼─────────────────────────────────────┐
│                    BACKGROUND WORKERS                     │
│  Python Workers (Render)                                 │
│  • Client Following Worker - Scrapes following lists     │
│  • Profile Scraper Worker - Scrapes page details         │
│  Poll database for jobs → Execute → Update results       │
└────────────────────┬─────────────────────────────────────┘
                     │ Read/Write
┌────────────────────▼─────────────────────────────────────┐
│                      DATABASE                             │
│  Supabase PostgreSQL                                     │
│  • clients - Client records                              │
│  • pages - Instagram pages                               │
│  • client_following - Relationships                      │
│  • scrape_runs - Job queue & history                     │
│  • page_profiles - Detailed page data                    │
└──────────────────────────────────────────────────────────┘
                     ▲
                     │ API calls
┌────────────────────┴─────────────────────────────────────┐
│                    EXTERNAL SERVICES                      │
│  • Apify - Instagram scraping                            │
│  • GitHub - Code hosting & CI/CD                         │
└──────────────────────────────────────────────────────────┘
```

## Project Structure

```
ig-follower-analyzer/
├── api/                      # FastAPI Backend
│   ├── app/
│   │   ├── main.py          # API entry point
│   │   ├── config.py        # Configuration
│   │   ├── db.py            # Supabase connection
│   │   ├── routes/          # API endpoints
│   │   │   ├── clients.py   # Client CRUD
│   │   │   ├── pages.py     # Page browsing
│   │   │   └── scrapes.py   # Scrape job management
│   │   ├── schemas/         # Pydantic models
│   │   └── services/        # Business logic
│   ├── requirements.txt
│   └── README.md
│
├── workers/                  # Background Workers
│   ├── client_following_worker.py  # Scrapes following lists
│   ├── profile_scrape_worker.py    # Scrapes profile details
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── README.md
│
├── web/                      # Next.js Web UI
│   ├── app/
│   │   ├── page.tsx         # Main dashboard
│   │   ├── layout.tsx       # Root layout
│   │   ├── components/
│   │   │   ├── ClientsTab.tsx    # Client management
│   │   │   ├── PagesTab.tsx      # Page browsing
│   │   │   └── ScrapesTab.tsx    # Job monitoring
│   │   └── lib/
│   │       └── api.ts       # API client
│   ├── package.json
│   ├── next.config.js
│   └── README.md
│
├── scripts/                  # Migration & Utilities
│   ├── migrate_clients_json.py   # JSON → Supabase migration
│   └── README.md
│
├── docs/                     # Documentation
│   ├── CURRENT_ARCHITECTURE.md   # Old system overview
│   ├── DATA_MODEL_SUPABASE.md    # Database schema
│   ├── DEPLOYMENT.md             # Deploy guide
│   ├── MONITORING.md             # Monitoring setup
│   └── CLOUD_ARCHITECTURE_README.md  # This file
│
├── .github/workflows/        # CI/CD
│   └── ci.yml               # GitHub Actions pipeline
│
├── docker-compose.yml        # Local development setup
├── env.template             # Environment variable template
└── README.md                # Project overview

# Legacy files (still present, but replaced by new system)
├── main.py                  # Old CLI (deprecated)
├── categorize_app.py        # Old Streamlit UI (deprecated)
├── scrape_profiles.py       # Old scraper (replaced by workers)
└── clients_data.json        # Old storage (migrated to DB)
```

## Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Query** - Data fetching & caching
- **Vercel** - Hosting (auto-deploy from GitHub)

### Backend
- **FastAPI** - Modern Python web framework
- **Supabase** - PostgreSQL database + REST API
- **Pydantic** - Data validation
- **Render** - Hosting (API + workers)

### Workers
- **Python 3.11** - Worker scripts
- **Apify Client** - Instagram scraping
- **Docker** - Containerization
- **Render** - Background worker hosting

### Infrastructure
- **GitHub Actions** - CI/CD pipeline
- **Docker Compose** - Local development
- **Environment Variables** - Secret management

## Getting Started

### Prerequisites

1. **Supabase Account** (free)
   - Create project: https://supabase.com
   - Note Project URL and service_role key

2. **Apify Account**
   - Sign up: https://apify.com
   - Add $5-10 credits
   - Get API token

3. **GitHub Account**
   - For code hosting and CI/CD

4. **Hosting Accounts** (all free tiers available)
   - Vercel (web UI)
   - Render (API + workers)

### Local Development

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-username/ig-follower-analyzer.git
   cd ig-follower-analyzer
   ```

2. **Set Environment Variables**
   ```bash
   cp env.template .env
   # Edit .env with your credentials
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up
   ```

   This starts:
   - API on http://localhost:8000
   - Web UI on http://localhost:3000
   - 2 background workers

4. **Or Run Services Individually**
   
   **API:**
   ```bash
   cd api
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

   **Workers:**
   ```bash
   cd workers
   pip install -r requirements.txt
   python client_following_worker.py
   # In another terminal:
   python profile_scrape_worker.py
   ```

   **Web UI:**
   ```bash
   cd web
   npm install
   npm run dev
   ```

### Cloud Deployment

Follow the detailed guide: [`docs/DEPLOYMENT.md`](./DEPLOYMENT.md)

**Quick Summary:**
1. Set up Supabase database (run SQL schema)
2. Deploy API to Render
3. Deploy workers to Render (2 services)
4. Deploy web UI to Vercel
5. Migrate existing data (if you have `clients_data.json`)

### Migration from Old System

If you have existing data in `clients_data.json`:

```bash
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_SERVICE_KEY="your-key"
python scripts/migrate_clients_json.py
```

This will transfer all clients, pages, and relationships to Supabase.

## Key Features

### 1. Web Dashboard

Access from anywhere at your Vercel URL:

**Clients Tab:**
- Add new clients (name + Instagram username)
- View all clients with following counts
- Select multiple clients for batch scraping
- Delete clients
- See last scraped timestamp

**Pages Tab:**
- Browse pages followed by multiple clients
- Filter by minimum client count (e.g., show pages followed by 3+ clients)
- Click page to view detailed profile:
  - Profile picture
  - Bio
  - Contact email
  - Promo status (warm/unknown)
  - Recent posts grid
- See follower counts and verification badges

**Scrape Jobs Tab:**
- Real-time job monitoring (auto-refresh every 5s)
- See job status: pending → processing → completed/failed
- View scrape results:
  - Accounts scraped
  - Coverage % (with color-coded alerts)
  - Failed usernames
- Job history with timestamps

### 2. Automated Background Processing

Workers continuously poll for jobs and execute automatically:

- **Client Following Worker**: Scrapes who clients follow
  - Gets total following count from Instagram
  - Scrapes via Apify
  - Calculates coverage % (target: ≥95%)
  - Stores results in database
  - Updates client record

- **Profile Scraper Worker**: Scrapes page details
  - Gets profile picture, bio, recent posts
  - Downloads and encodes images as base64
  - Detects promo openness (keywords in bio)
  - Extracts contact emails
  - Stores in `page_profiles` table

### 3. REST API

Programmatic access for integrations:

**Endpoints:**
- `GET /api/clients` - List all clients
- `POST /api/clients` - Add client
- `DELETE /api/clients/:id` - Delete client
- `GET /api/pages?min_client_count=2` - List pages
- `GET /api/pages/:id/profile` - Get profile details
- `GET /api/scrapes` - List scrape jobs
- `POST /api/scrapes/client-following` - Queue client scrape
- `POST /api/scrapes/profile-scrape` - Queue profile scrape

Full API docs: http://your-api-url.com/docs

### 4. Coverage Tracking

Every client scrape now tracks coverage:
- Gets Instagram's reported following count
- Compares to accounts retrieved
- Flags if coverage <95%
- Automatically retries if coverage <90%

Example output:
```
✅ Excellent! Got 99.8% of accounts (≥95% threshold)
```

### 5. Real-Time Monitoring

- Job status updates every 5 seconds
- See which jobs are processing
- View results immediately when complete
- Detailed error messages for failures

## Monitoring & Alerts

Set up monitoring for production:

1. **Health Checks**
   - Use UptimeRobot (free) to ping API `/health` endpoint
   - Get alerts if API goes down

2. **Coverage Alerts**
   - Workers can send Discord/Slack webhooks when coverage <95%
   - Set environment variables: `DISCORD_WEBHOOK_URL` or `SLACK_WEBHOOK_URL`

3. **Platform Monitoring**
   - Render dashboard: CPU, memory, logs
   - Vercel analytics: Page loads, errors
   - Supabase reports: Database performance

Full guide: [`docs/MONITORING.md`](./MONITORING.md)

## Cost Breakdown

### Free Tier (Development)
- **Supabase**: $0 (500MB database, enough for ~5,000 pages)
- **Render API**: $0 (spins down after 15min inactivity)
- **Render Workers**: $0 × 2
- **Vercel**: $0 (unlimited bandwidth)
- **Apify**: ~$0.10-0.50 per scrape (pay-per-use)

**Total**: $0/month + Apify usage

### Production (Recommended)
- **Supabase Pro**: $25/month (8GB, better performance, backups)
- **Render Starter**: $7/month × 3 services = $21/month (always-on, no spin-down)
- **Vercel Pro**: $20/month (optional - custom domain, analytics)
- **Apify**: $20-50/month depending on volume

**Total**: ~$66-96/month + Apify usage

## Advantages Over Old System

### Scalability
- **Old**: Single JSON file (132MB), would break at ~10K pages
- **New**: PostgreSQL database, scales to millions of records

### Accessibility
- **Old**: CLI on local machine, VA needs remote access to your computer
- **New**: Web dashboard accessible from anywhere, just share URL

### Automation
- **Old**: Manual scrapes via terminal, manual Railway syncs
- **New**: Click "Scrape" in UI, workers handle everything automatically

### Reliability
- **Old**: If script crashes mid-scrape, data may be lost
- **New**: Jobs are queued, workers retry failures, all tracked in database

### Collaboration
- **Old**: Single-user, file conflicts if multiple people
- **New**: Multi-user ready, database handles concurrency

### Monitoring
- **Old**: Check terminal output, no history
- **New**: Real-time job monitoring, full history, coverage tracking

### Deployment
- **Old**: Manual setup, Railway volume uploads
- **New**: Push to GitHub → Auto-deploys everything

## Troubleshooting

### API Not Responding
- Check Render logs: https://dashboard.render.com
- Verify environment variables are set
- Free tier may spin down (first request takes 30s to wake up)

### Workers Not Processing Jobs
- Check worker logs on Render
- Verify Supabase connection (check service key)
- Check Apify credits

### Scrapes Failing
- Verify `APIFY_TOKEN` is valid
- Check Apify credits balance
- Some Instagram accounts may be private/deleted

### Web UI Can't Connect to API
- Check `NEXT_PUBLIC_API_URL` in Vercel settings
- Make sure it points to your Render API URL
- Check CORS settings in API

## Next Steps

After deployment:

1. **Migrate Data**: Run migration script to transfer old JSON data
2. **Test Workflow**: Add a client, trigger scrape, verify results
3. **Set Up Monitoring**: Configure alerts for coverage/failures
4. **Share with VA**: Send Vercel URL, they can start using it
5. **Archive Old System**: Backup `clients_data.json`, remove old CLI scripts

## Support & Documentation

- **Deployment Guide**: [`docs/DEPLOYMENT.md`](./DEPLOYMENT.md)
- **Database Schema**: [`docs/DATA_MODEL_SUPABASE.md`](./DATA_MODEL_SUPABASE.md)
- **Monitoring Setup**: [`docs/MONITORING.md`](./MONITORING.md)
- **API Docs**: Visit `/docs` on your API URL
- **Migration Guide**: [`scripts/README.md`](../scripts/README.md)

## Contributing

To add features:
1. Create feature branch
2. Make changes
3. Push to GitHub
4. CI runs tests automatically
5. Merge to `main` → Auto-deploys

## License

Free to use for your business!

---

**Built with ❤️ for a scalable, cloud-native VA workflow**

