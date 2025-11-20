"""
Migrate clients_data.json to Supabase Database

This script reads the existing clients_data.json file and uploads all data
to the Supabase database, preserving relationships and metadata.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

# Add parent directory to path to import from api
sys.path.append(str(Path(__file__).parent.parent))

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not installed")
    print("Install with: pip install supabase")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataMigrator:
    """Handles migration from JSON file to Supabase"""
    
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        
        # Get Supabase credentials from environment
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Missing environment variables. Set SUPABASE_URL and SUPABASE_SERVICE_KEY"
            )
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("Connected to Supabase")
    
    def load_json_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        logger.info(f"Loading data from {self.json_file_path}")
        
        if not os.path.exists(self.json_file_path):
            raise FileNotFoundError(f"File not found: {self.json_file_path}")
        
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data.get('clients', {}))} clients and {len(data.get('pages', {}))} pages")
        return data
    
    def migrate_clients(self, clients_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Migrate clients to database
        Returns mapping of old username → new UUID
        """
        logger.info("Migrating clients...")
        username_to_id = {}
        
        for username, client in clients_data.items():
            try:
                # Prepare client record
                client_record = {
                    "name": client.get("name", username),
                    "ig_username": username,
                    "following_count": client.get("following_count", 0),
                    "last_scraped": client.get("last_scraped"),
                    "created_at": client.get("added_date", datetime.utcnow().isoformat())
                }
                
                # Check if client already exists
                existing = self.supabase.table("clients")\
                    .select("id")\
                    .eq("ig_username", username)\
                    .execute()
                
                if existing.data:
                    # Update existing
                    client_id = existing.data[0]["id"]
                    self.supabase.table("clients")\
                        .update(client_record)\
                        .eq("id", client_id)\
                        .execute()
                    logger.info(f"Updated client: {username}")
                else:
                    # Insert new
                    result = self.supabase.table("clients")\
                        .insert(client_record)\
                        .execute()
                    client_id = result.data[0]["id"]
                    logger.info(f"Created client: {username}")
                
                username_to_id[username] = client_id
                
            except Exception as e:
                logger.error(f"Failed to migrate client {username}: {e}")
        
        logger.info(f"✅ Migrated {len(username_to_id)} clients")
        return username_to_id
    
    def migrate_pages(self, pages_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Migrate pages to database
        Returns mapping of old username → new UUID
        """
        logger.info("Migrating pages...")
        username_to_id = {}
        
        # Process in batches
        batch_size = 100
        usernames = list(pages_data.keys())
        
        for i in range(0, len(usernames), batch_size):
            batch = usernames[i:i + batch_size]
            logger.info(f"Processing pages {i+1}-{min(i+batch_size, len(usernames))} of {len(usernames)}")
            
            for username in batch:
                page = pages_data[username]
                
                try:
                    # Prepare page record
                    page_record = {
                        "ig_username": username,
                        "full_name": page.get("full_name"),
                        "follower_count": page.get("follower_count", 0),
                        "is_verified": page.get("is_verified", False),
                        "is_private": page.get("is_private", False),
                        "last_scraped": page.get("last_scraped"),
                    }
                    
                    # Check if page already exists
                    existing = self.supabase.table("pages")\
                        .select("id")\
                        .eq("ig_username", username)\
                        .execute()
                    
                    if existing.data:
                        # Update existing
                        page_id = existing.data[0]["id"]
                        self.supabase.table("pages")\
                            .update(page_record)\
                            .eq("id", page_id)\
                            .execute()
                    else:
                        # Insert new
                        result = self.supabase.table("pages")\
                            .insert(page_record)\
                            .execute()
                        page_id = result.data[0]["id"]
                    
                    username_to_id[username] = page_id
                    
                    # Migrate page profile if available
                    if page.get("profile_pic_base64") or page.get("bio"):
                        self.migrate_page_profile(page_id, page)
                    
                except Exception as e:
                    logger.error(f"Failed to migrate page {username}: {e}")
        
        logger.info(f"✅ Migrated {len(username_to_id)} pages")
        return username_to_id
    
    def migrate_page_profile(self, page_id: str, page_data: Dict):
        """Migrate page profile data"""
        try:
            profile_record = {
                "page_id": page_id,
                "profile_pic_base64": page_data.get("profile_pic_base64"),
                "profile_pic_mime_type": page_data.get("profile_pic_mime_type"),
                "bio": page_data.get("bio"),
                "posts": page_data.get("posts", []),
                "promo_status": page_data.get("promo_status", "unknown"),
                "promo_indicators": page_data.get("promo_indicators", []),
                "contact_email": page_data.get("contact_email"),
                "scraped_at": page_data.get("last_scraped", datetime.utcnow().isoformat())
            }
            
            # Upsert profile
            self.supabase.table("page_profiles")\
                .upsert(profile_record, on_conflict="page_id")\
                .execute()
            
        except Exception as e:
            logger.warning(f"Failed to migrate profile for page {page_id}: {e}")
    
    def migrate_following_relationships(
        self,
        clients_data: Dict[str, Any],
        client_id_map: Dict[str, str],
        page_id_map: Dict[str, str]
    ):
        """Migrate client → page following relationships"""
        logger.info("Migrating following relationships...")
        
        total_relationships = 0
        
        for client_username, client in clients_data.items():
            if client_username not in client_id_map:
                continue
            
            client_id = client_id_map[client_username]
            following_list = client.get("following", [])
            
            logger.info(f"Migrating {len(following_list)} relationships for {client_username}")
            
            # Delete existing relationships for this client
            try:
                self.supabase.table("client_following")\
                    .delete()\
                    .eq("client_id", client_id)\
                    .execute()
            except:
                pass  # Table might be empty
            
            # Insert new relationships in batches
            batch_size = 100
            for i in range(0, len(following_list), batch_size):
                batch = following_list[i:i + batch_size]
                
                relationships = []
                for page_username in batch:
                    if isinstance(page_username, dict):
                        page_username = page_username.get("username")
                    
                    if page_username in page_id_map:
                        relationships.append({
                            "client_id": client_id,
                            "page_id": page_id_map[page_username]
                        })
                
                if relationships:
                    try:
                        self.supabase.table("client_following")\
                            .insert(relationships)\
                            .execute()
                        total_relationships += len(relationships)
                    except Exception as e:
                        logger.error(f"Failed to insert relationship batch: {e}")
        
        logger.info(f"✅ Migrated {total_relationships} following relationships")
    
    def verify_migration(self, original_data: Dict[str, Any]):
        """Verify migration was successful"""
        logger.info("Verifying migration...")
        
        # Count clients
        clients_result = self.supabase.table("clients")\
            .select("id", count="exact")\
            .execute()
        db_clients = clients_result.count
        json_clients = len(original_data.get("clients", {}))
        
        # Count pages
        pages_result = self.supabase.table("pages")\
            .select("id", count="exact")\
            .execute()
        db_pages = pages_result.count
        json_pages = len(original_data.get("pages", {}))
        
        # Count relationships
        relationships_result = self.supabase.table("client_following")\
            .select("client_id", count="exact")\
            .execute()
        db_relationships = relationships_result.count
        
        logger.info(f"\nMigration Summary:")
        logger.info(f"  Clients:       {db_clients}/{json_clients}")
        logger.info(f"  Pages:         {db_pages}/{json_pages}")
        logger.info(f"  Relationships: {db_relationships}")
        
        if db_clients >= json_clients * 0.95 and db_pages >= json_pages * 0.95:
            logger.info("✅ Migration successful!")
            return True
        else:
            logger.warning("⚠️  Some data may not have migrated correctly")
            return False
    
    def run(self):
        """Execute full migration"""
        try:
            logger.info("=" * 60)
            logger.info("Starting migration from JSON to Supabase")
            logger.info("=" * 60)
            
            # Load JSON data
            data = self.load_json_data()
            
            # Migrate clients
            client_id_map = self.migrate_clients(data.get("clients", {}))
            
            # Migrate pages
            page_id_map = self.migrate_pages(data.get("pages", {}))
            
            # Migrate relationships
            self.migrate_following_relationships(
                data.get("clients", {}),
                client_id_map,
                page_id_map
            )
            
            # Verify
            self.verify_migration(data)
            
            logger.info("=" * 60)
            logger.info("Migration complete!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            sys.exit(1)


def main():
    """Main entry point"""
    # Default path to clients_data.json
    default_path = Path(__file__).parent.parent / "clients_data.json"
    
    # Allow custom path as command line argument
    json_path = sys.argv[1] if len(sys.argv) > 1 else str(default_path)
    
    print(f"\n📦 IG Follower Analyzer - Data Migration")
    print(f"{'=' * 60}")
    print(f"Source: {json_path}")
    print(f"Target: Supabase Database")
    print(f"{'=' * 60}\n")
    
    # Confirm before proceeding
    response = input("This will upload data to Supabase. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        sys.exit(0)
    
    # Run migration
    migrator = DataMigrator(json_path)
    migrator.run()


if __name__ == "__main__":
    main()

