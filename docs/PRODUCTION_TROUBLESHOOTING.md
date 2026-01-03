# Production Troubleshooting: Clients/Pages Not Loading

## Quick Checks

### 1. Frontend Environment Variables (Vercel Production)

**Required:** `NEXT_PUBLIC_API_URL` must point to your Render API:
```
https://ig-follower-analyzer.onrender.com
```

**To check:**
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Verify `NEXT_PUBLIC_API_URL` is set for **Production** environment
3. If missing or wrong, add/update it and **redeploy**

### 2. Backend Environment Variables (Render Production)

**Required:** `SUPABASE_URL` must be set:
```
https://your-production-project.supabase.co
```

**To check:**
1. Go to Render Dashboard → Your API Service → Environment
2. Verify `SUPABASE_URL` is set
3. If missing, add it and **restart the service**

### 3. Check Browser Console

Open browser DevTools (F12) → Console tab and look for:
- `[API] 401 Unauthorized error` → JWT verification failing
- `[API] Connection failed` → API URL wrong or Render sleeping
- `[AUTH] Token verification failed` → Check Render logs

### 4. Check Render Logs

In Render Dashboard → Logs, look for:
- `[AUTH] ES256 token verified successfully` → ✅ Working
- `[AUTH] Invalid token: The specified alg value is not allowed` → Missing SUPABASE_URL
- `[AUTH] ES256/RS256 token detected but SUPABASE_URL not set!` → Need to set SUPABASE_URL

### 5. Verify User Data Assignment

If JWT verification succeeds but data doesn't load, check user_id:

**In Supabase SQL Editor (Production):**
```sql
-- Check your user_id
SELECT id, email FROM auth.users WHERE email = 'your-email@example.com';

-- Check if you have data
SELECT COUNT(*) FROM clients WHERE user_id = 'your-user-id';
SELECT COUNT(*) FROM pages WHERE user_id = 'your-user-id';
```

If counts are 0, your data might not be assigned to your user_id.

## Common Issues

### Issue: "No clients yet" / "No pages found"
**Cause:** Data not assigned to your user_id
**Fix:** Run SQL to assign data (see `docs/assign_production_data_to_user.sql`)

### Issue: 401 Unauthorized errors
**Cause:** JWT verification failing
**Fix:** 
1. Check `SUPABASE_URL` is set in Render
2. Check Render logs for specific error
3. Verify Supabase project uses ES256 (new) or HS256 (legacy)

### Issue: Network errors / API not responding
**Cause:** Wrong API URL or Render service sleeping
**Fix:**
1. Verify `NEXT_PUBLIC_API_URL` in Vercel points to Render API
2. Wait 30 seconds for Render to wake up (free tier)
3. Check Render service is running

## Debug Steps

1. **Check frontend API URL:**
   - Open browser console
   - Look for `[API] Using API_URL: ...`
   - Should be `https://ig-follower-analyzer.onrender.com`

2. **Check backend JWT verification:**
   - Check Render logs for `[AUTH]` messages
   - Should see successful token verification

3. **Check data exists:**
   - Run SQL queries above
   - Verify data is assigned to your user_id

4. **Test API directly:**
   ```bash
   # Get your JWT token from browser (Application → Local Storage → supabase.auth.token)
   curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
        https://ig-follower-analyzer.onrender.com/api/clients/
   ```


