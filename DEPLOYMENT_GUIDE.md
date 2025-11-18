# Cloud Deployment Guide - Railway.app

This guide explains how to deploy the profile scraping script to Railway.app so it can run overnight without using your local PC.

## Prerequisites

1. **GitHub Account** - Your code needs to be in a GitHub repository
2. **Railway Account** - Sign up at https://railway.app (free tier available)
3. **API Keys** - Your Apify and OpenAI keys (stored securely in Railway)

## Step 1: Prepare Your Repository

Make sure your code is committed to GitHub:

```bash
git add .
git commit -m "Add Railway deployment support"
git push origin main
```

## Step 2: Set Up Railway Project

1. **Go to Railway.app**: https://railway.app
2. **Sign in** with your GitHub account
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your repository** (`ig-follower-analyzer`)
6. **Railway will auto-detect** Python and install dependencies

## Step 3: Configure Environment Variables

In your Railway project dashboard:

1. Go to your project → **Variables** tab
2. Add these environment variables:
   - `APIFY_TOKEN` = `your_apify_token_here`
   - `OPENAI_API_KEY` = `your_openai_key_here`

**Important**: These are stored securely and won't be visible in logs.

## Step 4: Set Up Data File Sync

Since `clients_data.json` needs to persist, you have two options:

### Option A: GitHub Sync (Recommended)

1. **Before running on Railway**: Commit your latest `clients_data.json` to GitHub
2. **After scraping completes**: Pull the updated file back to your local machine

**Workflow:**
```bash
# Before running on Railway
git add clients_data.json
git commit -m "Update data before cloud scrape"
git push

# After Railway completes, pull the updated file
git pull
```

### Option B: Railway Volumes (Persistent Storage)

1. In Railway project → **Volumes** tab
2. Click **"Add Volume"**
3. Mount path: `/app/data`
4. Update `scrape_profiles.py` to use `/app/data/clients_data.json`
5. This keeps data persistent across deployments

## Step 5: Run the Scraper

### For Priority Scrape (Fast):

1. In Railway project → **Variables** tab
2. Add environment variable: `SCRAPE_MODE=priority`
3. Set **Start Command** to: `python scrape_profiles.py`
4. Deploy - the script will automatically run in priority mode
5. Or manually trigger and select option 1 when prompted (if `SCRAPE_MODE` not set)

### For Full Scrape (Overnight):

1. In Railway project → **Variables** tab
2. Add environment variable: `SCRAPE_MODE=all`
3. Set **Start Command** to: `python scrape_profiles.py`
4. Deploy - the script will automatically run in full mode
5. The script will run until complete (can take 6-13 hours for 4,758 pages)
6. Or manually trigger and select option 2 when prompted (if `SCRAPE_MODE` not set)

**Note**: Setting `SCRAPE_MODE` environment variable makes the script run non-interactively, perfect for cloud deployment.

## Step 6: Monitor Progress

1. Go to Railway project → **Deployments** tab
2. Click on the active deployment
3. View **Logs** to see real-time progress
4. You'll see tier breakdowns and progress updates

## Step 7: Download Results

After scraping completes:

1. **If using GitHub sync**: Pull the updated `clients_data.json`
2. **If using Railway volumes**: Download the file from the volume
3. **Or**: Use Railway's file download feature in the deployment logs

## Cost Estimate

- **Railway Free Tier**: 500 hours/month, $5 credit
- **For overnight scrape** (8-12 hours): Well within free tier
- **Apify costs**: ~$2.50-$6.50 per 4,758 pages (unchanged)

## Troubleshooting

### Script stops early
- Check Railway logs for errors
- Ensure API keys are set correctly
- Check Apify rate limits

### Data file not updating
- Verify file path is correct
- Check Railway volume mount (if using volumes)
- Ensure script has write permissions

### Out of memory
- Railway free tier has memory limits
- Consider upgrading or splitting into smaller batches
- Or run priority scrape first, then full scrape later

## Alternative: Scheduled Runs

You can also set up Railway to run on a schedule:

1. Use Railway's **Cron Jobs** feature
2. Or use external scheduler (GitHub Actions, cron-job.org) to trigger Railway deployments
3. This allows automatic overnight runs

## Tips

- **Start with priority scrape** to test the setup
- **Monitor first run** to ensure everything works
- **Save progress** happens every 10 pages automatically
- **Can stop/resume**: If script stops, just restart and it will skip already-scraped pages

## Support

If you encounter issues:
1. Check Railway logs for error messages
2. Verify environment variables are set
3. Ensure `clients_data.json` exists in the repository
4. Check Apify dashboard for API usage/errors

