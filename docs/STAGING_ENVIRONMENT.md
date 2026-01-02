# Staging Environment Setup Guide

This guide explains how to set up and use the staging environment for safe testing before deploying to production.

## Overview

The staging environment is a complete copy of production that allows you to:
- Test changes safely without affecting production
- Verify features work correctly before deploying
- Test with realistic data (synced from production)

## Architecture

```
Production:
  main branch → Vercel (production) → Render API (production) → Supabase (production)

Staging:
  staging branch → Vercel (staging) → Render API (staging) → Supabase (staging)
                                                                    ↑
                                                          Data Sync Script
```

## Prerequisites

1. **Staging Supabase Project**: Create a new Supabase project for staging
2. **Git Repository**: Access to the repository with staging branch
3. **Vercel Account**: For frontend staging deployment
4. **Render Account**: For backend staging deployment

## Step 1: Create Staging Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Click "New Project"
3. Name it: `ig-follower-analyzer-staging`
4. Choose a region (same as production recommended)
5. Set a database password
6. Wait for project creation

### Set Up Database Schema

1. Go to SQL Editor in your staging Supabase project
2. Run all migration files in **this exact order**:
   - `docs/supabase_schema.sql` - Base schema (creates core tables)
   - `docs/add_va_categorization_fields.sql` - VA categorization fields (creates outreach_tracking table)
   - `docs/add_multi_tenant_auth_STAGED.sql` - Multi-tenant support (adds user_id to all tables including outreach_tracking)
   - `docs/add_date_closed_to_clients.sql` - Date closed field
   - `docs/add_client_count_column.sql` - Client count tracking
   - `docs/change_successful_contact_method_to_array.sql` - Convert to array
   - `docs/add_category_counts_function.sql` - Helper function
   - `docs/add_concentration_sorting_rpc.sql` - Sorting function (optional)

**Important**: Run `add_va_categorization_fields.sql` BEFORE `add_multi_tenant_auth_STAGED.sql` because the multi-tenant script needs the `outreach_tracking` table to exist.

3. Verify all tables are created:
   - `clients`
   - `pages`
   - `client_following`
   - `scrape_runs`
   - `page_profiles`
   - `outreach_tracking`

### Get Staging Credentials

1. Go to Project Settings → API
2. Note down:
   - **Project URL** (staging Supabase URL)
   - **anon/public key** (for frontend)
   - **service_role key** (for backend - keep secret!)

## Step 2: Configure Vercel Staging Deployment

### Option A: Separate Vercel Project (Recommended)

1. Go to [Vercel Dashboard](https://vercel.com)
2. Click "Add New Project"
3. Import your Git repository (same repo as production)
4. Configure:
   - **Project Name**: `ig-follower-analyzer-staging`
   - **Framework Preset**: Next.js
   - **Root Directory**: `web`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Production Branch**: Leave as `main` for now (we'll change this after)

5. **After project is created**, go to Settings → **Environments** (NOT Git)
   - Scroll down to the **Production** environment section
   - Find **Branch Tracking** or **Production Branch** setting
   - Change it from `main` to `staging`
   - Click **Save** to apply changes
   - This makes the `staging` branch deploy to your staging URL
   
   **Note**: If you don't see this option, it might be in Settings → **Git** → look for "Production Branch" or "Branch" settings

6. Go to Settings → Environment Variables
   Add the following (use placeholders if you don't have values yet):
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://your-staging-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-staging-anon-key
   NEXT_PUBLIC_API_URL=https://placeholder.onrender.com
   ```
   
   **Note**: 
   - Use your **staging Supabase** credentials (from Step 1)
   - For `NEXT_PUBLIC_API_URL`, use a placeholder for now if Render staging isn't set up yet
   - You can update `NEXT_PUBLIC_API_URL` later after Step 3 (Render setup)
   - Make sure to select all environments: Production, Preview, Development

### Option B: Same Project, Different Branch

1. In your existing Vercel project
2. Go to Settings → Git
3. Add branch: `staging` → Deploy to preview URL
4. Add environment variables for staging branch

## Step 3: Configure Render Staging Service

### Create Staging Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your Git repository
4. Configure:
   - **Name**: `ig-analyzer-api-staging`
   - **Region**: Same as production
   - **Branch**: `staging`
   - **Root Directory**: `api`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Set Environment Variables

Go to Environment tab and add:

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

**Note**: Get `SUPABASE_JWT_SECRET` from Supabase Dashboard → Project Settings → API → JWT Secret

## Step 4: Set Up Data Sync Script

### Install Dependencies

The sync script uses the `supabase` Python package (already in requirements.txt).

### Configure Environment Variables

Create a `.env.staging-sync` file (or set in your environment):

```bash
# Production Supabase (source)
PROD_SUPABASE_URL=https://your-production-project.supabase.co
PROD_SUPABASE_SERVICE_KEY=your-production-service-key

# Staging Supabase (destination)
STAGING_SUPABASE_URL=https://your-staging-project.supabase.co
STAGING_SUPABASE_SERVICE_KEY=your-staging-service-key
```

### Run Data Sync

**Full Sync** (truncates staging tables first):
```bash
cd ig-follower-analyzer
source .env.staging-sync  # Load environment variables
python scripts/sync_prod_to_staging.py --full
```

**Incremental Sync** (only adds/updates):
```bash
python scripts/sync_prod_to_staging.py --incremental
```

**Sync Specific Tables**:
```bash
python scripts/sync_prod_to_staging.py --tables clients pages
```

### Automated Sync (Optional)

You can set up automated daily/weekly sync using:

**Cron (Linux/Mac)**:
```bash
# Daily at 2 AM
0 2 * * * cd /path/to/ig-follower-analyzer && source .env.staging-sync && python scripts/sync_prod_to_staging.py --full
```

**Windows Task Scheduler**:
- Create a task that runs daily
- Action: Run Python script with environment variables

**Render Cron Job** (if using Render):
- Create a Cron Job service
- Schedule: `0 2 * * *` (daily at 2 AM)
- Command: `python scripts/sync_prod_to_staging.py --full`

## Step 5: Git Workflow

### Standard Workflow

1. **Work on feature branch**:
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   git commit -m "Add new feature"
   ```

2. **Merge to staging**:
   ```bash
   git checkout staging
   git merge feature/new-feature
   git push origin staging
   ```
   → Auto-deploys to staging environment

3. **Test on staging**:
   - Visit staging Vercel URL
   - Test all functionality
   - Verify data looks correct

4. **Merge to production**:
   ```bash
   git checkout main
   git merge staging
   git push origin main
   ```
   → Auto-deploys to production

### Quick Fix Workflow

For urgent fixes:
```bash
git checkout main
git checkout -b hotfix/fix-name
# Make fix
git commit -m "Fix: description"
git checkout main
git merge hotfix/fix-name
git push origin main
# Then merge to staging to keep in sync
git checkout staging
git merge main
git push origin staging
```

## Environment URLs

After setup, you'll have:

- **Production Frontend**: `https://ig-follower-analyzer.vercel.app`
- **Staging Frontend**: 
  - If separate Vercel project: `https://ig-follower-analyzer-staging.vercel.app`
  - If using branch previews: `https://ig-follower-analyzer-git-staging-[username].vercel.app`
  - **Check your Vercel dashboard** for the exact staging URL after deployment
- **Production API**: `https://ig-analyzer-api.onrender.com`
- **Staging API**: `https://ig-analyzer-api-staging.onrender.com` (check Render dashboard for exact URL)
- **Production Database**: Your production Supabase project
- **Staging Database**: Your staging Supabase project

### Finding Your Staging URL

1. **Vercel Dashboard**:
   - Go to your Vercel project
   - Click on the deployment for the `staging` branch
   - The URL will be shown at the top (e.g., `https://ig-follower-analyzer-staging.vercel.app`)

2. **Render Dashboard**:
   - Go to your staging service
   - The URL will be shown in the service overview (e.g., `https://ig-analyzer-api-staging.onrender.com`)

## Testing Checklist

Before merging staging → main:

- [ ] All features work on staging
- [ ] No console errors
- [ ] Authentication works
- [ ] Data displays correctly
- [ ] Forms submit successfully
- [ ] API endpoints respond correctly
- [ ] No performance issues
- [ ] Mobile/responsive design works

## Troubleshooting

### Staging deployment fails

1. Check Vercel/Render logs
2. Verify environment variables are set
3. Check that staging branch exists and is pushed

### Data sync fails

1. Verify environment variables are correct
2. Check that staging Supabase project exists
3. Ensure staging schema matches production
4. Check Supabase service key permissions

### Authentication issues on staging

1. Verify `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are set
2. Check Supabase Auth settings (should match production)
3. Verify JWT secret is correct in backend

### API connection issues

1. Check `NEXT_PUBLIC_API_URL` points to staging Render URL
2. Verify CORS settings in Render allow staging Vercel URL
3. Check Render service is running

## Safety Measures

1. **Complete Isolation**: Staging uses separate Supabase project
2. **One-Way Sync**: Data only flows production → staging, never reverse
3. **Branch Protection**: Consider protecting `main` branch (require PR approval)
4. **Environment Naming**: Clear naming prevents confusion
5. **URL Differences**: Staging URLs clearly different from production

## Cost Considerations

- **Supabase**: Additional project (check pricing tier)
- **Vercel**: Staging deployments count toward usage (usually free tier sufficient)
- **Render**: Additional service (check pricing)

## Maintenance

### Regular Tasks

1. **Weekly**: Run data sync to keep staging data fresh
2. **After major changes**: Run full sync
3. **Before testing**: Run incremental sync if needed

### Monitoring

- Monitor staging deployments in Vercel/Render dashboards
- Check staging Supabase usage
- Review staging logs for errors

## Support

If you encounter issues:
1. Check this documentation
2. Review error logs
3. Verify all environment variables
4. Check Git branch status

