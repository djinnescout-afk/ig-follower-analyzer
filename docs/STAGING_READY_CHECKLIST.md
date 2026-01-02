# Staging Environment - Ready Checklist

Use this checklist to verify your staging environment is fully set up and ready for testing.

## ✅ Infrastructure Setup

- [x] **Staging Supabase Project** created
- [x] **Staging Database Schema** deployed (COMPLETE_MIGRATION_SCRIPT.sql)
- [x] **Vercel Staging Deployment** configured (staging branch → staging URL)
- [x] **Render Staging Service** configured (staging branch → staging API)
- [x] **Git Staging Branch** exists and is up to date

## ✅ Environment Variables

### Vercel Staging
- [x] `NEXT_PUBLIC_SUPABASE_URL` → Staging Supabase URL
- [x] `NEXT_PUBLIC_SUPABASE_ANON_KEY` → Staging Supabase anon key
- [x] `NEXT_PUBLIC_API_URL` → Staging Render API URL

### Render Staging
- [x] `SUPABASE_URL` → Staging Supabase URL (for JWKS)
- [x] `SUPABASE_SERVICE_KEY` → Staging Supabase service key
- [x] `SUPABASE_JWT_SECRET` → (if using HS256, otherwise not needed)
- [x] `ADMIN_EMAILS` → Admin email addresses
- [x] `FRONTEND_URL` → Staging Vercel URL
- [x] `ENVIRONMENT` → `staging`

### Render Production
- [x] `SUPABASE_URL` → Production Supabase URL (for JWKS)
- [x] All other production env vars set

## ✅ Data & Authentication

- [x] **Production Data Synced** to staging (via sync script)
- [x] **User Accounts Created** in staging (dragodbusiness@gmail.com, etc.)
- [x] **Data Assigned** to correct users in staging
- [x] **JWT Authentication** working (ES256/JWKS support)
- [x] **Admin Access** configured in staging

## ✅ Code & Deployment

- [x] **Staging Branch** auto-deploys to staging
- [x] **Main Branch** auto-deploys to production
- [x] **Hotfix Process** documented (for urgent fixes)
- [x] **Git Workflow** documented (feature → staging → main)

## ✅ Testing Workflow

### Ready to Test New Features

1. **Create Feature Branch:**
   ```bash
   git checkout staging
   git pull origin staging
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes & Commit:**
   ```bash
   # Make your changes
   git add .
   git commit -m "Add: your feature description"
   ```

3. **Deploy to Staging:**
   ```bash
   git checkout staging
   git merge feature/your-feature-name
   git push origin staging
   ```
   → Auto-deploys to staging environment

4. **Test on Staging:**
   - Visit staging URL
   - Test all functionality
   - Check browser console for errors
   - Verify data displays correctly

5. **Deploy to Production (when ready):**
   ```bash
   git checkout main
   git merge staging
   git push origin main
   ```
   → Auto-deploys to production

## ✅ Data Sync (When Needed)

To sync fresh production data to staging:

```bash
# Set environment variables
export PROD_SUPABASE_URL=...
export PROD_SUPABASE_SERVICE_KEY=...
export STAGING_SUPABASE_URL=...
export STAGING_SUPABASE_SERVICE_KEY=...

# Run sync
python scripts/sync_prod_to_staging.py --full
```

Then reassign data to users if needed:
```bash
python scripts/reassign_staging_data_by_email.py --email dragodbusiness@gmail.com
```

## 🎉 You're Ready!

Your staging environment is fully set up and ready for testing. You can now:

- ✅ Test new features safely on staging
- ✅ Verify changes before deploying to production
- ✅ Sync production data when needed
- ✅ Deploy confidently to production after testing

## Important Reminders

- **ALWAYS** push to `staging` first, never directly to `main`
- **TEST** thoroughly on staging before merging to `main`
- **SYNC** production data to staging periodically (weekly/monthly)
- **REASSIGN** data to users after syncing if needed

