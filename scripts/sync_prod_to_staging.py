#!/usr/bin/env python3
"""
One-way data sync script: Production Supabase → Staging Supabase

This script copies all data from production to staging, maintaining user_id relationships.
It's designed to be run manually or on a schedule (daily/weekly).

Usage:
    python scripts/sync_prod_to_staging.py --full
    python scripts/sync_prod_to_staging.py --incremental
    python scripts/sync_prod_to_staging.py --tables clients pages

Environment Variables Required:
    PROD_SUPABASE_URL - Production Supabase URL
    PROD_SUPABASE_SERVICE_KEY - Production Supabase service role key
    STAGING_SUPABASE_URL - Staging Supabase URL
    STAGING_SUPABASE_SERVICE_KEY - Staging Supabase service role key
"""

import os
import sys
import argparse
from typing import List, Dict, Any
from datetime import datetime
from supabase import create_client, Client

# Tables to sync (in dependency order to handle foreign keys)
TABLES = [
    'clients',           # No dependencies
    'pages',            # No dependencies
    'client_following',  # Depends on clients and pages
    'scrape_runs',      # Depends on clients (optional)
    'page_profiles',    # Depends on pages
    'outreach_tracking', # Depends on pages
]

# Tables that should be synced in full (truncate first)
FULL_SYNC_TABLES = ['clients', 'pages', 'client_following', 'scrape_runs', 'page_profiles', 'outreach_tracking']


def get_clients() -> tuple[Client, Client]:
    """Get production and staging Supabase clients."""
    prod_url = os.getenv('PROD_SUPABASE_URL')
    prod_key = os.getenv('PROD_SUPABASE_SERVICE_KEY')
    staging_url = os.getenv('STAGING_SUPABASE_URL')
    staging_key = os.getenv('STAGING_SUPABASE_SERVICE_KEY')
    
    if not all([prod_url, prod_key, staging_url, staging_key]):
        raise ValueError(
            "Missing required environment variables:\n"
            "  PROD_SUPABASE_URL\n"
            "  PROD_SUPABASE_SERVICE_KEY\n"
            "  STAGING_SUPABASE_URL\n"
            "  STAGING_SUPABASE_SERVICE_KEY"
        )
    
    prod_client = create_client(prod_url, prod_key)
    staging_client = create_client(staging_url, staging_key)
    
    return prod_client, staging_client


def fetch_all_rows(client: Client, table: str, batch_size: int = 1000) -> List[Dict[str, Any]]:
    """Fetch all rows from a table, handling pagination."""
    all_rows = []
    offset = 0
    
    while True:
        response = client.table(table).select('*').range(offset, offset + batch_size - 1).execute()
        batch = response.data or []
        
        if not batch:
            break
        
        all_rows.extend(batch)
        offset += batch_size
        
        # If we got fewer rows than requested, we're done
        if len(batch) < batch_size:
            break
    
    return all_rows


def get_user_id_mapping(prod_client: Client, staging_client: Client, verbose: bool = True) -> dict:
    """
    Create a mapping from production user_id to staging user_id based on email.
    Returns dict mapping prod_user_id -> staging_user_id
    """
    if verbose:
        print("\n🔗 Building user ID mapping...")
    
    mapping = {}
    
    try:
        # Get all users from production
        prod_users_response = prod_client.auth.admin.list_users()
        prod_users = prod_users_response if isinstance(prod_users_response, list) else prod_users_response.users if hasattr(prod_users_response, 'users') else []
        
        # Get all users from staging
        staging_users_response = staging_client.auth.admin.list_users()
        staging_users = staging_users_response if isinstance(staging_users_response, list) else staging_users_response.users if hasattr(staging_users_response, 'users') else []
        
        # Create email -> staging_user_id map
        staging_email_to_id = {}
        for user in staging_users:
            if hasattr(user, 'email') and user.email:
                staging_email_to_id[user.email.lower()] = user.id
            elif isinstance(user, dict) and user.get('email'):
                staging_email_to_id[user['email'].lower()] = user['id']
        
        # Map production user_id to staging user_id by email
        for user in prod_users:
            email = None
            prod_id = None
            
            if hasattr(user, 'email'):
                email = user.email
                prod_id = user.id
            elif isinstance(user, dict):
                email = user.get('email')
                prod_id = user.get('id')
            
            if email and prod_id:
                email_lower = email.lower()
                if email_lower in staging_email_to_id:
                    mapping[prod_id] = staging_email_to_id[email_lower]
                    if verbose:
                        print(f"   ✅ Mapped {email}: {prod_id[:8]}... → {staging_email_to_id[email_lower][:8]}...")
                else:
                    if verbose:
                        print(f"   ⚠️  No staging user found for {email}")
        
        if verbose:
            print(f"   📊 Mapped {len(mapping)} users")
        
    except Exception as e:
        print(f"   ⚠️  Warning: Could not build user mapping: {e}")
        print(f"   ℹ️  Will attempt sync without user mapping (may fail on foreign keys)")
    
    return mapping


def sync_table(
    prod_client: Client,
    staging_client: Client,
    table: str,
    full_sync: bool = False,
    user_id_mapping: dict = None,
    verbose: bool = True
) -> tuple[int, int]:
    """
    Sync a single table from production to staging.
    
    Args:
        user_id_mapping: Dict mapping prod_user_id -> staging_user_id
    
    Returns:
        (rows_fetched, rows_synced)
    """
    if verbose:
        print(f"\n📊 Syncing table: {table}")
    
    # Fetch all rows from production
    try:
        prod_rows = fetch_all_rows(prod_client, table)
        if verbose:
            print(f"   Fetched {len(prod_rows)} rows from production")
    except Exception as e:
        print(f"   ❌ Error fetching from production: {e}")
        return 0, 0
    
    if not prod_rows:
        if verbose:
            print(f"   ℹ️  No rows to sync")
        return 0, 0
    
    # Map user_ids if mapping provided and table has user_id column
    if user_id_mapping and 'user_id' in (prod_rows[0] if prod_rows else {}):
        mapped_count = 0
        for row in prod_rows:
            if row.get('user_id') and row['user_id'] in user_id_mapping:
                row['user_id'] = user_id_mapping[row['user_id']]
                mapped_count += 1
        if verbose and mapped_count > 0:
            print(f"   🔄 Mapped {mapped_count} user_ids")
    
    # Full sync: truncate staging table first
    if full_sync:
        try:
            # Delete all rows (using service key bypasses RLS)
            staging_client.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            if verbose:
                print(f"   🗑️  Cleared staging table")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not clear staging table: {e}")
    
    # Insert rows into staging
    # Batch inserts for better performance
    batch_size = 100
    synced_count = 0
    
    for i in range(0, len(prod_rows), batch_size):
        batch = prod_rows[i:i + batch_size]
        
        try:
            # Use upsert to handle conflicts (based on primary key)
            # For tables with composite keys, we'll need special handling
            if table == 'client_following':
                # Composite primary key (client_id, page_id)
                staging_client.table(table).upsert(batch).execute()
            else:
                # Single primary key (id)
                staging_client.table(table).upsert(batch).execute()
            
            synced_count += len(batch)
            if verbose:
                print(f"   ✅ Synced batch {i//batch_size + 1} ({synced_count}/{len(prod_rows)} rows)")
        except Exception as e:
            print(f"   ❌ Error syncing batch: {e}")
            # Try individual inserts for this batch
            for row in batch:
                try:
                    if table == 'client_following':
                        staging_client.table(table).upsert(row).execute()
                    else:
                        staging_client.table(table).upsert(row).execute()
                    synced_count += 1
                except Exception as e2:
                    print(f"   ⚠️  Failed to sync row {row.get('id', 'unknown')}: {e2}")
    
    if verbose:
        print(f"   ✅ Completed: {synced_count}/{len(prod_rows)} rows synced")
    
    return len(prod_rows), synced_count


def main():
    parser = argparse.ArgumentParser(
        description='Sync data from production Supabase to staging Supabase'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Full sync: truncate staging tables before syncing'
    )
    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Incremental sync: only add/update rows (default)'
    )
    parser.add_argument(
        '--tables',
        nargs='+',
        choices=TABLES,
        help='Specific tables to sync (default: all tables)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=True,
        help='Show detailed progress (default: True)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output (overrides --verbose)'
    )
    
    args = parser.parse_args()
    
    if args.quiet:
        args.verbose = False
    
    # Determine sync mode
    full_sync = args.full
    if not args.full and not args.incremental:
        # Default to incremental
        full_sync = False
    
    # Determine tables to sync
    tables_to_sync = args.tables if args.tables else TABLES
    
    if args.verbose:
        print("=" * 60)
        print("🔄 Production → Staging Data Sync")
        print("=" * 60)
        print(f"Mode: {'Full sync (truncate first)' if full_sync else 'Incremental sync'}")
        print(f"Tables: {', '.join(tables_to_sync)}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    # Get clients
    try:
        prod_client, staging_client = get_clients()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Test connections
    if args.verbose:
        print("\n🔌 Testing connections...")
    try:
        # Try to fetch a single row from each
        prod_client.table('clients').select('id').limit(1).execute()
        staging_client.table('clients').select('id').limit(1).execute()
        if args.verbose:
            print("   ✅ Connections successful")
    except Exception as e:
        print(f"   ❌ Connection test failed: {e}")
        sys.exit(1)
    
    # Build user ID mapping (prod user_id -> staging user_id)
    user_id_mapping = get_user_id_mapping(prod_client, staging_client, verbose=args.verbose)
    
    # Sync each table
    total_fetched = 0
    total_synced = 0
    results = {}
    
    for table in tables_to_sync:
        if table not in TABLES:
            print(f"⚠️  Warning: Unknown table '{table}', skipping")
            continue
        
        try:
            fetched, synced = sync_table(
                prod_client,
                staging_client,
                table,
                full_sync=full_sync and table in FULL_SYNC_TABLES,
                user_id_mapping=user_id_mapping,
                verbose=args.verbose
            )
            total_fetched += fetched
            total_synced += synced
            results[table] = {'fetched': fetched, 'synced': synced}
        except Exception as e:
            print(f"❌ Fatal error syncing {table}: {e}")
            results[table] = {'fetched': 0, 'synced': 0, 'error': str(e)}
    
    # Summary
    if args.verbose:
        print("\n" + "=" * 60)
        print("📊 Sync Summary")
        print("=" * 60)
        for table, result in results.items():
            if 'error' in result:
                print(f"  {table}: ❌ Error - {result['error']}")
            else:
                print(f"  {table}: {result['synced']}/{result['fetched']} rows")
        print("=" * 60)
        print(f"Total: {total_synced}/{total_fetched} rows synced")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    # Exit code based on success
    if total_synced == total_fetched and total_fetched > 0:
        sys.exit(0)
    elif total_synced > 0:
        sys.exit(1)  # Partial success
    else:
        sys.exit(2)  # Complete failure


if __name__ == '__main__':
    main()

