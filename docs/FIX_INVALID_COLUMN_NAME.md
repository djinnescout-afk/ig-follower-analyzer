# Fix Invalid Column Name: "website last scraped at"

## Problem

The production `pages` table has a column named `website last scraped at` with **spaces**, which is an invalid SQL identifier. Column names with spaces require quotes in SQL and cause issues with ORMs and API clients.

## Root Cause

This column was likely created in one of these ways:

1. **Manual creation in Supabase UI**: Someone manually added a column and typed "website last scraped at" with spaces
2. **Incorrect SQL migration**: A migration was run with SQL like:
   ```sql
   ALTER TABLE pages ADD COLUMN "website last scraped at" TIMESTAMPTZ;
   ```
   (Note the quotes around the column name)

## Correct Column Name

The column should be named: **`website_last_scraped_at`** (snake_case, no spaces)

## Fix Steps

### Step 1: Rename the column in production

Run this SQL in your **production** Supabase SQL Editor:

```sql
-- Rename the invalid column to the correct name
ALTER TABLE pages 
RENAME COLUMN "website last scraped at" TO website_last_scraped_at;
```

### Step 2: Verify the fix

Check that the column was renamed:

```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'pages' 
  AND column_name LIKE '%website%scraped%';
```

You should see `website_last_scraped_at` (not `website last scraped at`).

### Step 3: Re-run the sync script

After renaming, re-run the staging sync:

```bash
python scripts/sync_prod_to_staging.py --full
```

## Prevention

**Always use snake_case for column names:**
- ✅ `website_last_scraped_at`
- ❌ `website last scraped at`
- ❌ `websiteLastScrapedAt`
- ❌ `WebsiteLastScrapedAt`

When creating columns manually in Supabase UI, ensure there are no spaces. If you must use SQL, always use unquoted identifiers with underscores.

