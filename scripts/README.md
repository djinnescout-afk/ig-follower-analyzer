# Migration Scripts

Tools for migrating data from the legacy system to the new cloud-native architecture.

## migrate_clients_json.py

Migrates data from `clients_data.json` to Supabase database.

### Prerequisites

1. **Supabase project set up** with tables created (see `docs/DATA_MODEL_SUPABASE.md`)
2. **Environment variables set**:
   ```bash
   export SUPABASE_URL="https://xxx.supabase.co"
   export SUPABASE_SERVICE_KEY="your-service-role-key"
   ```
3. **Python dependencies**:
   ```bash
   pip install supabase
   ```

### Usage

Default (migrates `clients_data.json` from project root):
```bash
python scripts/migrate_clients_json.py
```

Custom path:
```bash
python scripts/migrate_clients_json.py /path/to/your/data.json
```

### What It Does

1. **Loads JSON data** from the file
2. **Migrates clients**:
   - Creates/updates records in `clients` table
   - Preserves names, usernames, dates
3. **Migrates pages**:
   - Creates/updates records in `pages` table
   - Includes follower counts, verification status
   - Uploads profile data to `page_profiles` table (bio, images, promo status)
4. **Migrates relationships**:
   - Links clients to pages they follow in `client_following` table
5. **Verifies** migration by counting records

### Output

```
📦 IG Follower Analyzer - Data Migration
============================================================
Source: /path/to/clients_data.json
Target: Supabase Database
============================================================

This will upload data to Supabase. Continue? (y/n): y

2025-11-20 11:00:00 - INFO - Connected to Supabase
2025-11-20 11:00:01 - INFO - Loading data from clients_data.json
2025-11-20 11:00:01 - INFO - Loaded 5 clients and 2500 pages
2025-11-20 11:00:02 - INFO - Migrating clients...
2025-11-20 11:00:03 - INFO - Created client: johnsmith123
2025-11-20 11:00:03 - INFO - Created client: janedoe456
...
2025-11-20 11:00:10 - INFO - ✅ Migrated 5 clients
2025-11-20 11:00:11 - INFO - Migrating pages...
2025-11-20 11:00:12 - INFO - Processing pages 1-100 of 2500
...
2025-11-20 11:05:30 - INFO - ✅ Migrated 2500 pages
2025-11-20 11:05:31 - INFO - Migrating following relationships...
2025-11-20 11:05:32 - INFO - Migrating 500 relationships for johnsmith123
...
2025-11-20 11:08:00 - INFO - ✅ Migrated 12450 following relationships
2025-11-20 11:08:01 - INFO - Verifying migration...

Migration Summary:
  Clients:       5/5
  Pages:         2500/2500
  Relationships: 12450

2025-11-20 11:08:02 - INFO - ✅ Migration successful!
============================================================
Migration complete!
============================================================
```

### Error Handling

- **Duplicate records**: Updates existing records instead of failing
- **Missing data**: Skips individual records but continues migration
- **Batch failures**: Logs errors but processes remaining batches
- **Verification**: Shows summary to confirm data integrity

### After Migration

Once migration is complete:

1. **Verify in Supabase**:
   - Go to Supabase dashboard → Table Editor
   - Check clients, pages, and client_following tables
   - Run queries to spot-check data

2. **Test the API**:
   ```bash
   curl http://localhost:8000/api/clients
   ```

3. **Test the Web UI**:
   - Open the web dashboard
   - Check clients tab shows your clients
   - Check pages tab shows discovered pages

4. **Archive old JSON**:
   ```bash
   mv clients_data.json clients_data.json.backup
   ```

5. **Switch to new system**:
   - Use the web UI for all new operations
   - Old CLI scripts (main.py) no longer needed

## Troubleshooting

### "Missing environment variables"
Set `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`:
```bash
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_SERVICE_KEY="your-key"
```

### "File not found"
Provide the correct path to your JSON file:
```bash
python scripts/migrate_clients_json.py /full/path/to/clients_data.json
```

### "Failed to migrate client/page"
- Check Supabase connection
- Verify tables exist (run SQL from DATA_MODEL_SUPABASE.md)
- Check service role key has permissions

### "Migration successful but counts don't match"
- Some records may have failed (check logs for errors)
- Re-run the script (it will update existing records)
- Manually check failed records in Supabase

### Large file takes too long
- Migration is batch-processed (100 records at a time)
- For very large datasets (10,000+ pages), expect 10-30 minutes
- Script can be safely interrupted and re-run (uses upsert)

## Reverse Migration (DB → JSON)

To export from Supabase back to JSON (for backup):

```python
# TODO: Create reverse migration script if needed
python scripts/export_to_json.py
```

## Data Integrity

The migration script:
- ✅ Preserves all client names and usernames
- ✅ Maintains follower counts and metadata
- ✅ Keeps following relationships intact
- ✅ Transfers profile pictures (base64)
- ✅ Migrates bio and post data
- ✅ Preserves promo status and contact emails
- ✅ Maintains timestamps (added_date, last_scraped)

No data is lost during migration.

## Best Practices

1. **Backup first**: Keep a copy of `clients_data.json` before migrating
2. **Test on staging**: Try migration on a test Supabase project first
3. **Verify data**: Spot-check a few clients/pages after migration
4. **Document**: Note any issues or manual fixes needed
5. **Archive old system**: Once verified, archive old CLI scripts

## Support

For migration issues:
1. Check script logs for specific errors
2. Verify Supabase project is set up correctly
3. Review `docs/DATA_MODEL_SUPABASE.md` for schema details
4. Test with a small subset of data first (edit JSON to 1-2 clients)

