# Setting Environment Variables in Render

## Why We Need These Variables

### 1. `ENVIRONMENT=production`
- **Purpose**: Tells the app it's running in production mode
- **Effect**: 
  - JWT secret becomes **required** (app won't start without it)
  - Disables insecure fallbacks (like unverified token decoding)
  - Enables production-level security checks
- **What happens if missing**: App runs in development mode (less secure)

### 2. `CORS_ORIGINS=https://ig-follower-analyzer.vercel.app`
- **Purpose**: Restricts which websites can make API requests to your backend
- **Effect**: Only your frontend domain can call the API
- **Security**: Prevents other websites from making unauthorized requests
- **What happens if missing**: Allows all origins (`*`) - less secure but works

### 3. `SUPABASE_JWT_SECRET` (Already Set)
- **Purpose**: Secret key to verify JWT tokens from Supabase
- **Effect**: Validates that tokens are legitimate and not tampered with
- **What happens if missing**: In production, app won't start (by design)

## How to Set Environment Variables in Render

### Step-by-Step Instructions

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Log in to your account

2. **Select Your Backend Service**
   - Click on your backend service (e.g., "ig-follower-analyzer")
   - This should be the FastAPI/Python service

3. **Navigate to Environment Tab**
   - In the left sidebar, click **"Environment"**
   - Or look for a tab/section labeled "Environment Variables"

4. **Add/Update Variables**
   - Click **"Add Environment Variable"** or **"Add Variable"**
   - For each variable:
     - **Key**: `ENVIRONMENT`
     - **Value**: `production`
     - Click **"Save Changes"**
   
   - Repeat for:
     - **Key**: `CORS_ORIGINS`
     - **Value**: `https://ig-follower-analyzer.vercel.app`
     - (Replace with your actual Vercel domain if different)

5. **Verify Existing Variables**
   - Check that these are already set:
     - `SUPABASE_URL`
     - `SUPABASE_SERVICE_KEY`
     - `SUPABASE_JWT_SECRET`
     - `APIFY_TOKEN`

6. **Redeploy (if needed)**
   - After adding variables, Render may auto-redeploy
   - Or manually trigger a redeploy from the "Manual Deploy" section

## Visual Guide

```
Render Dashboard
├── Your Service (ig-follower-analyzer)
    ├── Overview
    ├── Logs
    ├── Environment  ← Click here
    ├── Settings
    └── ...
```

In the Environment tab, you'll see:
```
Environment Variables
┌─────────────────────────┬─────────────────────────────────────┐
│ Key                     │ Value                               │
├─────────────────────────┼─────────────────────────────────────┤
│ SUPABASE_URL            │ https://xxx.supabase.co             │
│ SUPABASE_SERVICE_KEY    │ eyJ...                              │
│ SUPABASE_JWT_SECRET     │ tc8WOSG92c0PLGzuxTPVNaXuoDfzHdt0... │
│ APIFY_TOKEN             │ apify_api_xxx                       │
│ ENVIRONMENT             │ production                          │ ← Add this
│ CORS_ORIGINS            │ https://ig-follower-analyzer.vercel.app │ ← Add this
└─────────────────────────┴─────────────────────────────────────┘
```

## Current Status

### Already Set ✅
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_JWT_SECRET`
- `APIFY_TOKEN`

### Need to Add ⚠️
- `ENVIRONMENT` = `production`
- `CORS_ORIGINS` = `https://ig-follower-analyzer.vercel.app`

## After Setting Variables

1. **Check Logs**: After redeploy, check Render logs to verify:
   - App starts successfully
   - No errors about missing JWT secret
   - CORS is configured correctly

2. **Test API**: Make a request from your frontend to verify:
   - API calls work
   - CORS headers are correct
   - Authentication works

3. **Monitor**: Watch for any errors in the first few minutes after deployment

## Troubleshooting

### "App won't start after setting ENVIRONMENT=production"
- **Cause**: `SUPABASE_JWT_SECRET` might be missing or incorrect
- **Fix**: Verify `SUPABASE_JWT_SECRET` is set correctly

### "CORS errors in browser"
- **Cause**: `CORS_ORIGINS` might not match your frontend URL exactly
- **Fix**: Check that `CORS_ORIGINS` matches your Vercel domain exactly (including `https://`)

### "Can't find Environment tab"
- **Cause**: You might be looking at the wrong service
- **Fix**: Make sure you're in your **backend/API service**, not the frontend

