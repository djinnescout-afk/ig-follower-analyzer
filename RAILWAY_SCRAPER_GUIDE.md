# Running Scraper on Railway (Cloud)

## Option 1: Run via Railway CLI (Recommended)

Run the scraper remotely on Railway from your local computer:

```bash
# Priority scrape (fast - Tiers 1-3)
railway run --service web python railway_scraper.py priority

# Full scrape (all pages - overnight run)
railway run --service web python railway_scraper.py all

# Re-scrape priority (force update Tiers 1-3)
railway run --service web python railway_scraper.py re-scrape-priority

# Re-scrape all (force update everything)
railway run --service web python railway_scraper.py re-scrape-all
```

**Benefits:**
- ✅ Runs on Railway's servers (not your computer)
- ✅ Can run overnight without using your PC
- ✅ Automatically syncs to Railway volume
- ✅ No need to keep your computer on

## Option 2: Create a Separate Scraper Service

You can create a dedicated Railway service just for scraping:

1. **In Railway Dashboard:**
   - Click "Add a Service"
   - Select "GitHub Repository"
   - Choose your repo
   - Railway will auto-detect it

2. **Configure the service:**
   - Set start command: `python railway_scraper.py all`
   - Or leave it as a one-time job (runs and exits)

3. **Run it:**
   - Manually trigger from Railway dashboard
   - Or use Railway CLI: `railway run --service scraper python railway_scraper.py all`

## Option 3: Scheduled Jobs (Cron)

Railway doesn't have built-in cron, but you can:

1. **Use external cron service** (like cron-job.org):
   - Set up a webhook that triggers Railway CLI
   - Schedule it to run daily/weekly

2. **Use Railway's scheduled deployments:**
   - Create a service that runs on a schedule
   - Or use GitHub Actions to trigger Railway

## Option 4: Add Trigger Endpoint to Streamlit App

Add a secret admin endpoint to trigger scraping from the web:

```python
# In categorize_app.py - add admin tab
if st.secrets.get("admin_password"):
    # Add trigger button
    if st.button("🚀 Run Scraper on Railway"):
        # Trigger Railway scraper
        pass
```

## Recommended Setup

**For regular use:**
- Use **Option 1** (Railway CLI) - simple and flexible
- Run overnight: `railway run --service web python railway_scraper.py all`

**For automation:**
- Set up **Option 3** (external cron) to trigger Railway CLI
- Or use GitHub Actions to run on schedule

## Environment Variables Needed

Make sure these are set in Railway:
- `APIFY_TOKEN` - Your Apify API token
- `OPENAI_API_KEY` - (Optional, for AI categorization)
- `AUTO_SYNC_RAILWAY` - Set to `true` (auto-sync is built-in now)

## Notes

- **Data location**: Scraper reads/writes to `/data/clients_data.json` (Railway volume)
- **Auto-sync**: Built-in - preserves VA's work automatically
- **Cost**: Uses Railway's compute time (included in Hobby plan)
- **Monitoring**: Check Railway logs to see scraping progress

