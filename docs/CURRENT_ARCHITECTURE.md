## Current Architecture Overview

### High-Level Flow
1. **Data store** – All structured data (clients, pages, categorization results, scrape history) lives in a single JSON file: `clients_data.json`. Streamlit, CLI, and scripts read/write this file locally and on Railway’s `/data` volume.
2. **CLI (`main.py`)** – Provides the legacy workflow for adding clients, scraping following lists via Apify actors, and running reports. After every write it triggers `railway_sync.sync_to_railway()` so the remote `clients_data.json` stays in sync.
3. **Streamlit UI (`categorize_app.py`)** – Browser app for VAs to manage clients, trigger scrapes, and categorize pages. It loads the JSON file (local or `/data/clients_data.json` on Railway), caches it for 60s, and exposes tabs for Workflow Control, Categorization Queue, View by Category, Edit Page Details, and Data Management.
4. **Scraping scripts** – 
   - `main.py` option “Scrape following list” invokes Apify actor `louisdeconinck/instagram-following-scraper`.
   - `scrape_profiles.py` pre-scrapes profile data, stores base64 images, and now includes “Re-scrape Priority/All” plus failed-page reporting.
   - `categorizer.py` uses `apify/instagram-profile-scraper` + OpenAI Vision for deep profile analysis when requested.
5. **Sync tooling (`railway_sync.py`)** – Uploads/downloads `clients_data.json` to Railway’s persistent volume by calling `railway run --service web python -c ...`. All CLI and scripts call into this module to ensure remote sync after mutations.
6. **Deployment** – Railway hosts the Streamlit app (auto-detected) with `/data` volume attached. Manual instructions exist in `DEPLOY_STREAMLIT.md`, `RAILWAY_DATA_SYNC.md`, etc. No separate API service; Streamlit directly manipulates the JSON file on the volume.

### Key Modules
| File | Responsibility |
| --- | --- |
| `main.py` | IGFollowerAnalyzer CLI (client CRUD, scraping, merging results, CSV export, coverage logging) |
| `categorize_app.py` | Streamlit VA dashboard, forms for adding clients, triggering scrapes, manual data upload, cached file access |
| `scrape_profiles.py` | Batch profile scraping with re-scrape options, base64 image persistence, failed-page reporting |
| `categorizer.py` | Apify + GPT-4 Vision categorization pipeline (profile/post scraping, promo/contact detection) |
| `railway_sync.py` | Finds Railway CLI, uploads/downloads `clients_data.json`, called after scrapes/client adds |
| `railway_startup.py` / `Procfile` | Attempted multi-process startup for Railway (Streamlit + Flask sync API) but currently Streamlit auto-detect remains |

### Data Contracts
`clients_data.json` shape:
```json
{
  "clients": {
    "username": {
      "name": "...",
      "following": ["acct1", "acct2"],
      "following_count": 1984,
      "last_scraped": "2025-11-20T00:18:00Z",
      ...
    }
  },
  "pages": {
    "username": {
      "clients_following": ["client1", "client2"],
      "category": "BLACK_THEME",
      "profile_pic_base64": "...",
      "promo_signals": [],
      ...
    }
  }
}
```
The Streamlit tabs mutate this structure directly and then call `save_data()` → `railway_sync` if running locally.

### Current Pain Points
- **Single JSON file** – No concurrent writes; sync conflicts can overwrite VA edits. File is ~130MB, slow to load.
- **Manual / fragile syncing** – Although `railway_sync.py` automates uploads, it depends on the Railway CLI being installed and logged in locally; Streamlit scrapes in the browser still write locally and require pushes.
- **Streamlit as monolith** – UI logic, scraping invocations, and storage access all live in one process. Hard to scale or share across multiple VAs.
- **Secrets exposure** – Apify/OpenAI keys need to exist on any machine running the scripts or Streamlit app.
- **Lack of centralized API** – No REST layer or database; everything revolves around manipulating a file through Streamlit or CLI.
- **Limited observability** – Scrape coverage logs print to console but aren’t persisted beyond the JSON fields, making it hard to audit or alert on failures.

### Migration Targets
This audit informs the new architecture plan (`architecture_overhaul.plan.md`) that proposes:
- Supabase Postgres for structured storage.
- FastAPI service with webhook endpoints and managed secrets.
- Cloud workers for scraping jobs.
- React/Next.js web UI for VA workflow.
- Dedicated deployment + CI/CD, monitoring, and migration tooling.

