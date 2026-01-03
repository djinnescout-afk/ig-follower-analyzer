# Staging Environment Quick Reference

Quick reference guide for using the staging environment.

## URLs

- **Staging Frontend**: Check Vercel dashboard for staging URL
- **Staging API**: Check Render dashboard for staging service URL
- **Staging Database**: Your staging Supabase project

## Quick Commands

### Deploy to Staging

```bash
git checkout staging
git merge your-feature-branch
git push origin staging
```

### Sync Production Data to Staging

```bash
# Load environment variables
source .env.staging-sync  # or set them in your shell

# Full sync (truncates staging first)
python scripts/sync_prod_to_staging.py --full

# Incremental sync (adds/updates only)
python scripts/sync_prod_to_staging.py --incremental
```

### Deploy to Production

```bash
git checkout main
git merge staging
git push origin main
```

## Environment Variables for Sync Script

Create `.env.staging-sync`:

```bash
PROD_SUPABASE_URL=https://your-prod-project.supabase.co
PROD_SUPABASE_SERVICE_KEY=your-prod-service-key
STAGING_SUPABASE_URL=https://your-staging-project.supabase.co
STAGING_SUPABASE_SERVICE_KEY=your-staging-service-key
```

## Workflow

1. **Develop** → Feature branch
2. **Test** → Merge to `staging`, test on staging URL
3. **Deploy** → Merge `staging` to `main`, deploys to production

## Troubleshooting

- **Staging not deploying?** Check Vercel/Render logs
- **Data sync failing?** Verify environment variables
- **Auth issues?** Check Supabase credentials in Vercel/Render

For detailed information, see `docs/STAGING_ENVIRONMENT.md`


