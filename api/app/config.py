"""Application configuration"""
import os
from functools import lru_cache


class Settings:
    """Application settings"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        self.apify_token = os.getenv("APIFY_TOKEN", "")
        
        # Validate required settings
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not self.supabase_service_key:
            raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")
        if not self.apify_token:
            raise ValueError("APIFY_TOKEN environment variable is required")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
