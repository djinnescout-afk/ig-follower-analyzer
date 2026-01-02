# Staging Environment - Exact Replica Checklist

This checklist ensures staging is an **exact replica** of production. Follow it systematically.

## ✅ Step 1: Database Schema - MUST MATCH EXACTLY

### Run ALL migrations in order:

1. **Base Schema**:
   ```sql
   -- Run in staging Supabase SQL Editor
   -- File: docs/supabase_schema.sql
   ```

2. **VA Categorization Fields**:
   ```sql
   -- File: docs/add_va_categorization_fields.sql
   ```

3. **Multi-Tenant Auth**:
   ```sql
   -- File: docs/add_multi_tenant_auth_STAGED.sql
   ```

4. **Client Count Column**:
   ```sql
   -- File: docs/add_client_count_column.sql
   ```

5. **Date Closed Column**:
   ```sql
   -- File: docs/add_date_closed_to_clients.sql
   ```

6. **Category Counts Function**:
   ```sql
   -- File: docs/add_category_counts_function.sql
   ```

7. **Concentration Sorting RPC**:
   ```sql
   -- File: docs/add_concentration_sorting_rpc.sql
   ```

8. **Change Successful Contact Method to Array**:
   ```sql
   -- File: docs/change_successful_contact_method_to_array.sql
   ```

9. **All Missing Pages Columns** (if any):
   ```sql
   -- File: docs/add_missing_pages_columns.sql
   ```

### Verify Schema Matches:

```sql
-- Run this in BOTH production and staging to compare
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('pages', 'clients', 'client_following', 'outreach_tracking')
ORDER BY table_name, ordinal_position;
```

**Compare the results** - they must be identical.

## ✅ Step 2: Vercel Frontend Environment Variables

Go to **Vercel Dashboard → Staging Project → Settings → Environment Variables**

**MUST SET THESE** (for staging branch):

```
NEXT_PUBLIC_SUPABASE_URL=https://your-staging-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-staging-anon-key
NEXT_PUBLIC_API_URL=https://your-staging-api.onrender.com
```

**CRITICAL**: 
- `NEXT_PUBLIC_API_URL` **MUST** point to your **staging** Render API
- If this is wrong, all API calls will fail
- Check your Render dashboard for the exact staging API URL

## ✅ Step 3: Render Backend Environment Variables

Go to **Render Dashboard → Staging API Service → Environment**

**MUST SET THESE**:

```
SUPABASE_URL=https://your-staging-project.supabase.co
SUPABASE_SERVICE_KEY=your-staging-service-key
SUPABASE_JWT_SECRET=your-staging-jwt-secret
CORS_ORIGINS=https://your-staging-vercel-url.vercel.app
FRONTEND_URL=https://your-staging-vercel-url.vercel.app
ENVIRONMENT=staging
ADMIN_EMAILS=your-admin@email.com
APIFY_TOKEN=your-apify-token
```

**CRITICAL**:
- All Supabase values must be from **staging** project
- `CORS_ORIGINS` and `FRONTEND_URL` must be your **staging** Vercel URL
- After changing, **verify service restarted** (check Events tab)

## ✅ Step 4: Verify API Connection

### Test 1: Check API is reachable
```bash
curl https://your-staging-api.onrender.com/api/health
```

### Test 2: Check from browser console (on staging frontend)
```javascript
// Should return JSON, not HTML error
fetch('https://your-staging-api.onrender.com/api/admin/test-admin', {
  headers: {
    'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
  }
})
.then(r => r.text())
.then(console.log)
```

If you get HTML or CORS errors, the API URL is wrong.

## ✅ Step 5: Verify Data Sync

After schema matches, sync data:

```bash
python scripts/sync_prod_to_staging.py --full
```

**Verify**:
- No schema mismatch errors
- All tables synced successfully
- Row counts match (approximately, accounting for user filtering)

## ✅ Step 6: Test Critical Features

1. **Login**: Sign in with staging user account
2. **Load Clients**: Should see client list
3. **Load Pages**: Should see pages list
4. **Admin Tab**: Should be accessible if email in ADMIN_EMAILS
5. **API Calls**: Check browser Network tab - all should go to staging Render API, not Vercel

## 🔍 Debugging: Why Things Don't Match

### Issue: Frontend calls fail / return HTML
**Cause**: `NEXT_PUBLIC_API_URL` not set or wrong in Vercel
**Fix**: Set it to staging Render API URL in Vercel environment variables

### Issue: Admin doesn't work
**Cause**: 
- `ADMIN_EMAILS` not set in Render
- User email doesn't match exactly
- Service didn't restart after env var change
**Fix**: Check Render logs for `[ADMIN]` messages

### Issue: Clients/Pages don't load
**Cause**: 
- Wrong Supabase project (pointing to production instead of staging)
- Schema mismatch (missing columns)
- RLS policies blocking access
**Fix**: 
- Verify `SUPABASE_URL` in Render points to staging
- Run all migration scripts
- Check RLS policies match production

### Issue: CORS errors
**Cause**: `CORS_ORIGINS` in Render doesn't include staging Vercel URL
**Fix**: Add staging Vercel URL to `CORS_ORIGINS` in Render

## 📋 Pre-Deploy Verification

Before considering staging "ready":

- [ ] All migration scripts run successfully
- [ ] Schema comparison shows identical columns
- [ ] Vercel environment variables set correctly
- [ ] Render environment variables set correctly
- [ ] API health check returns 200
- [ ] Frontend can call API (check Network tab)
- [ ] Login works
- [ ] Clients load
- [ ] Pages load
- [ ] Admin access works (if applicable)
- [ ] Data sync completed without errors

## 🚨 Common Mistakes

1. **Using production URLs in staging** - Always double-check which project you're configuring
2. **Forgetting to restart Render service** - Env var changes require restart
3. **Missing migrations** - One missing migration breaks everything
4. **Wrong branch in Vercel** - Make sure "Production Branch" is set to `staging`
5. **Not verifying after changes** - Always test after making config changes

