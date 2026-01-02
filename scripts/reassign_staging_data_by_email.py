#!/usr/bin/env python3
"""
Reassign staging data to users based on email matching.

This script finds all data in staging with NULL user_id and reassigns it
to the correct staging user_id by matching production user_id via email.

Usage:
    python scripts/reassign_staging_data_by_email.py --email user@example.com
    python scripts/reassign_staging_data_by_email.py --all  # Reassign all unmapped data
"""

import os
import sys
import argparse
from typing import Dict, Any
from supabase import create_client, Client

# Tables that have user_id columns
TABLES_WITH_USER_ID = [
    'clients',
    'pages',
    'scrape_runs',
]

# Related tables that get user_id from parent tables
RELATED_TABLES = {
    'client_following': ('clients', 'client_id'),
    'page_profiles': ('pages', 'page_id'),
    'outreach_tracking': ('pages', 'page_id'),
}


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


def get_prod_user_id_by_email(prod_client: Client, email: str) -> str | None:
    """Get production user_id for a given email."""
    try:
        users_response = prod_client.auth.admin.list_users()
        users = users_response if isinstance(users_response, list) else users_response.users if hasattr(users_response, 'users') else []
        
        for user in users:
            user_email = None
            user_id = None
            
            if hasattr(user, 'email'):
                user_email = user.email
                user_id = user.id
            elif isinstance(user, dict):
                user_email = user.get('email')
                user_id = user.get('id')
            
            if user_email and user_email.lower() == email.lower():
                return user_id
    except Exception as e:
        print(f"   ⚠️  Error fetching production users: {e}")
    
    return None


def get_staging_user_id_by_email(staging_client: Client, email: str) -> str | None:
    """Get staging user_id for a given email."""
    try:
        users_response = staging_client.auth.admin.list_users()
        users = users_response if isinstance(users_response, list) else users_response.users if hasattr(users_response, 'users') else []
        
        for user in users:
            user_email = None
            user_id = None
            
            if hasattr(user, 'email'):
                user_email = user.email
                user_id = user.id
            elif isinstance(user, dict):
                user_email = user.get('email')
                user_id = user.get('id')
            
            if user_email and user_email.lower() == email.lower():
                return user_id
    except Exception as e:
        print(f"   ⚠️  Error fetching staging users: {e}")
    
    return None


def find_data_with_prod_user_id(
    staging_client: Client,
    table: str,
    prod_user_id: str,
    verbose: bool = True
) -> list[Dict[str, Any]]:
    """
    Find staging data that has the production user_id.
    
    During sync, unmapped user_ids keep their production user_id.
    This function finds all rows with that production user_id so we can reassign them.
    """
    try:
        # Find all rows with this production user_id
        response = staging_client.table(table).select('*').eq('user_id', prod_user_id).execute()
        return response.data or []
    except Exception as e:
        if verbose:
            print(f"   ⚠️  Error finding data with production user_id in {table}: {e}")
        return []


def reassign_table_data(
    staging_client: Client,
    table: str,
    prod_user_id: str,
    staging_user_id: str,
    verbose: bool = True
) -> int:
    """Reassign all data with production user_id to the staging user_id."""
    try:
        # Find all rows with this production user_id
        prod_data = find_data_with_prod_user_id(staging_client, table, prod_user_id, verbose=False)
        
        if not prod_data:
            return 0
        
        # Update all rows with production user_id to staging user_id
        # Use bulk update if possible
        updated_count = 0
        batch_size = 100
        
        for i in range(0, len(prod_data), batch_size):
            batch = prod_data[i:i + batch_size]
            ids_to_update = [row['id'] for row in batch]
            
            for row_id in ids_to_update:
                try:
                    staging_client.table(table).update({'user_id': staging_user_id}).eq('id', row_id).execute()
                    updated_count += 1
                except Exception as e:
                    if verbose:
                        print(f"   ⚠️  Error updating {table} row {row_id}: {e}")
        
        return updated_count
    except Exception as e:
        if verbose:
            print(f"   ❌ Error reassigning {table}: {e}")
        return 0


def reassign_related_tables(
    staging_client: Client,
    verbose: bool = True
) -> Dict[str, int]:
    """Reassign user_id in related tables based on parent table user_ids."""
    results = {}
    
    for table, (parent_table, foreign_key) in RELATED_TABLES.items():
        try:
            # Get all rows from related table
            response = staging_client.table(table).select('*').execute()
            rows = response.data or []
            
            updated_count = 0
            for row in rows:
                fk_value = row.get(foreign_key)
                if not fk_value:
                    continue
                
                # Get user_id from parent table
                parent_response = staging_client.table(parent_table).select('user_id').eq('id', fk_value).limit(1).execute()
                if parent_response.data:
                    parent_user_id = parent_response.data[0].get('user_id')
                    if parent_user_id and row.get('user_id') != parent_user_id:
                        # Update related table row
                        staging_client.table(table).update({'user_id': parent_user_id}).eq('id', row['id']).execute()
                        updated_count += 1
            
            results[table] = updated_count
            if verbose and updated_count > 0:
                print(f"   ✅ Updated {updated_count} rows in {table}")
        except Exception as e:
            if verbose:
                print(f"   ⚠️  Error updating {table}: {e}")
            results[table] = 0
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Reassign staging data to users based on email'
    )
    parser.add_argument(
        '--email',
        type=str,
        help='Email address of user to reassign data for'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Reassign all unmapped data (matches by email from production)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=True,
        help='Show detailed progress'
    )
    
    args = parser.parse_args()
    
    if not args.email and not args.all:
        parser.error("Must specify either --email or --all")
    
    print("=" * 60)
    print("🔄 Reassigning Staging Data by Email")
    print("=" * 60)
    
    # Get clients
    try:
        prod_client, staging_client = get_clients()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    if args.email:
        # Reassign data for specific email
        email = args.email
        print(f"\n📧 Reassigning data for: {email}")
        
        # Get production and staging user_ids
        prod_user_id = get_prod_user_id_by_email(prod_client, email)
        staging_user_id = get_staging_user_id_by_email(staging_client, email)
        
        if not prod_user_id:
            print(f"   ❌ User not found in production: {email}")
            sys.exit(1)
        
        if not staging_user_id:
            print(f"   ❌ User not found in staging: {email}")
            print(f"   ℹ️  User must log in to staging at least once first")
            sys.exit(1)
        
        print(f"   Production user_id: {prod_user_id[:8]}...")
        print(f"   Staging user_id: {staging_user_id[:8]}...")
        
        # Reassign all data with this production user_id to the staging user_id
        print(f"\n   🔄 Reassigning data from production user_id to staging user_id...")
        
        total_updated = 0
        for table in TABLES_WITH_USER_ID:
            updated = reassign_table_data(staging_client, table, prod_user_id, staging_user_id, verbose=args.verbose)
            total_updated += updated
            if args.verbose and updated > 0:
                print(f"   ✅ {table}: {updated} rows")
        
        # Fix related tables
        if args.verbose:
            print(f"\n   🔗 Fixing related tables...")
        reassign_related_tables(staging_client, verbose=args.verbose)
        
        print(f"\n   ✅ Total: {total_updated} rows reassigned")
    
    elif args.all:
        # Reassign all unmapped data by matching emails
        print(f"\n🔄 Reassigning all unmapped data...")
        
        # Get all production users
        try:
            prod_users_response = prod_client.auth.admin.list_users()
            prod_users = prod_users_response if isinstance(prod_users_response, list) else prod_users_response.users if hasattr(prod_users_response, 'users') else []
        except Exception as e:
            print(f"   ❌ Error fetching production users: {e}")
            sys.exit(1)
        
        # For each production user, find their staging user_id and reassign data
        total_reassigned = 0
        for prod_user in prod_users:
            email = None
            prod_user_id = None
            
            if hasattr(prod_user, 'email'):
                email = prod_user.email
                prod_user_id = prod_user.id
            elif isinstance(prod_user, dict):
                email = prod_user.get('email')
                prod_user_id = prod_user.get('id')
            
            if not email or not prod_user_id:
                continue
            
            staging_user_id = get_staging_user_id_by_email(staging_client, email)
            if not staging_user_id:
                if args.verbose:
                    print(f"   ⚠️  No staging user for {email}, skipping")
                continue
            
            # Reassign data for this user (from production user_id to staging user_id)
            user_updated = 0
            for table in TABLES_WITH_USER_ID:
                updated = reassign_table_data(staging_client, table, prod_user_id, staging_user_id, verbose=False)
                user_updated += updated
            
            if user_updated > 0 and args.verbose:
                print(f"   ✅ {email}: {user_updated} rows")
            total_reassigned += user_updated
        
        # Fix related tables
        if args.verbose:
            print(f"\n   🔗 Fixing related tables...")
        reassign_related_tables(staging_client, verbose=args.verbose)
        
        print(f"\n   ✅ Total: {total_reassigned} rows reassigned")
    
    print("\n" + "=" * 60)
    print("✅ Reassignment complete")
    print("=" * 60)


if __name__ == '__main__':
    main()

