# Railway Data Sync Guide

## Problem
- Your `clients_data.json` is 124 MB (too large for GitHub)
- Need to sync it to Railway for the VA to use
- Need to preserve VA's categorization work when uploading new scraped data

## Solution: Use Railway Volumes + Smart Merge

### Step 1: Set Up Railway Volume (One-Time Setup)

1. **In Railway Dashboard:**
   - Go to your "web" service
   - Right-click on the service card → **"Attach Volume"**
   - Mount path: `/data`
   - Click "Attach"

2. **Update App to Use Volume:**
   - The app will automatically use `/data/clients_data.json` if the volume exists
   - Falls back to local `clients_data.json` if no volume

### Step 2: Initial Upload (One Time)

**Option A: Using Railway CLI (Recommended)**
```bash
# 1. Login to Railway (if not already)
railway login

# 2. Link to your project
railway link

# 3. Upload your data file
railway run --service web cp clients_data.json /data/clients_data.json
```

**Option B: Manual Upload via Railway Dashboard**
- Railway doesn't have a direct file upload UI
- Use Railway CLI (Option A) or the sync script

### Step 3: Automated Sync (After Scraping)

After you scrape new data, run:
```bash
python sync_data_to_railway.py
```

This script:
1. ✅ Downloads current data from Railway (preserves VA's work)
2. ✅ Merges new scraped data with existing data
3. ✅ Preserves: categories, contact info, promo status, etc.
4. ✅ Updates: follower counts, profile data, posts, etc.
5. ✅ Uploads merged data back to Railway

**What Gets Preserved:**
- ✅ Page categories (VA's categorization)
- ✅ Contact methods (IG DM, Email, etc.)
- ✅ Promo prices and status
- ✅ IG account for DM
- ✅ Website URLs and promo info
- ✅ Any other VA edits

**What Gets Updated:**
- ✅ Follower counts
- ✅ Profile pictures and posts (base64 images)
- ✅ Bio and profile data
- ✅ New pages from scraping

## Alternative: Manual Process

If Railway CLI doesn't work, you can:

1. **Download current data from Railway:**
   - Use Railway's web terminal (if available)
   - Or export via the app

2. **Merge locally:**
   - Use the merge logic from `sync_data_to_railway.py`
   - Or manually copy categories/contact info

3. **Upload back:**
   - Use Railway CLI or web terminal

## Notes

- **Railway Volumes persist** between deployments
- **Data is safe** - VA's work won't be wiped
- **Sync is smart** - only updates what changed
- **Can be automated** - add to your scraping workflow

## Troubleshooting

**Railway CLI not found:**
```bash
npm install -g @railway/cli
```

**Can't find "Attach Volume" option:**
- Make sure you're on Hobby plan ($5/month)
- Try right-clicking the service card
- Or check Settings → Volumes

**Upload fails:**
- Check Railway CLI is logged in: `railway whoami`
- Verify service name matches: `railway status`


