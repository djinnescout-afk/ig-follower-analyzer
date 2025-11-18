# Deploying Streamlit App for Remote VA Access

## Option 1: Streamlit Cloud (Recommended - Free & Easy)

### Step 1: Push Code to GitHub
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit - Instagram Follower Analyzer"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/ig-follower-analyzer.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your repository: `YOUR_USERNAME/ig-follower-analyzer`
5. Main file path: `categorize_app.py`
6. Click "Deploy"

### Step 3: Share with VA
- Streamlit Cloud gives you a public URL like: `https://your-app-name.streamlit.app`
- Share this URL with your VA
- They can access it from anywhere in the world

### Important Notes:
- **Data Storage**: Streamlit Cloud doesn't persist files between deployments
- **Solution**: Use GitHub to store `clients_data.json` or use a cloud database
- **Better Option**: See Option 2 (Railway) for persistent storage

---

## Option 2: Railway.app (Recommended for Persistent Data)

Railway can host both the scraper AND the Streamlit app with persistent storage.

### Step 1: Update Railway Configuration

Create/update `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "streamlit run categorize_app.py --server.port $PORT --server.address 0.0.0.0",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 2: Update Procfile
```
web: streamlit run categorize_app.py --server.port $PORT --server.address 0.0.0.0
```

### Step 3: Deploy
1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select your repository
4. Railway will auto-detect and deploy
5. Add environment variables:
   - `APIFY_TOKEN` (optional - only if VA needs to scrape)
   - `OPENAI_API_KEY` (optional - not needed for VA workflow)

### Step 4: Get Public URL
- Railway provides a public URL automatically
- You can set a custom domain if needed
- Share URL with VA

### Advantages:
- ✅ Persistent file storage (clients_data.json stays)
- ✅ Can run both scraper and Streamlit app
- ✅ Free tier available

---

## Option 3: Streamlit Community Cloud (Alternative)

Similar to Option 1, but with different features. Follow Streamlit Cloud instructions above.

---

## Option 4: Self-Hosted (Advanced)

If you have a server/VPS:

### Using Streamlit
```bash
streamlit run categorize_app.py --server.port 8501 --server.address 0.0.0.0
```

### Using Nginx Reverse Proxy (for HTTPS)
Set up Nginx to proxy to `localhost:8501` with SSL certificate.

---

## Data Persistence Solutions

### Problem:
Streamlit Cloud doesn't persist `clients_data.json` between deployments.

### Solutions:

**Option A: GitHub Storage (Simple)**
- Commit `clients_data.json` to GitHub
- Streamlit app reads from GitHub on startup
- Updates are pushed back to GitHub

**Option B: Cloud Database (Better)**
- Use Supabase, MongoDB Atlas, or similar
- Store all data in cloud database
- App reads/writes to database

**Option C: Railway Persistent Volume (Best)**
- Railway provides persistent storage
- `clients_data.json` stays on the volume
- No need for external storage

---

## Recommended Setup for VA Access

1. **Use Railway.app** (Option 2)
   - Deploy Streamlit app
   - Persistent storage for `clients_data.json`
   - Can also run scraper on Railway

2. **Workflow:**
   - You run scraping locally or on Railway
   - VA accesses Streamlit app via Railway URL
   - All data persists in Railway's storage

3. **Security (Optional):**
   - Add password protection to Streamlit app
   - Or use Railway's built-in authentication

---

## Quick Start (Railway)

```bash
# 1. Push to GitHub
git add .
git commit -m "Add Streamlit app"
git push

# 2. Deploy on Railway
# - Go to railway.app
# - New Project → GitHub
# - Select repo
# - Add environment variables if needed
# - Deploy

# 3. Share URL with VA
```

---

## Adding Password Protection (Optional)

Add to `categorize_app.py` at the top of `main()`:

```python
import streamlit as st

# Simple password protection
if 'authenticated' not in st.session_state:
    password = st.text_input("Enter password", type="password")
    if password == "YOUR_PASSWORD_HERE":
        st.session_state.authenticated = True
        st.rerun()
    elif password:
        st.error("Incorrect password")
        st.stop()
    else:
        st.stop()
```

Or use Streamlit's built-in secrets management for production.


