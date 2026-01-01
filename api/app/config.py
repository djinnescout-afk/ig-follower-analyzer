"""Application configuration"""
import os
from functools import lru_cache


class Settings:
    """Application settings"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        self.apify_token = os.getenv("APIFY_TOKEN", "")
        self.api_prefix = "/api"  # API route prefix
        
        # CORS configuration
        cors_origins = os.getenv("CORS_ORIGINS", "")
        if cors_origins:
            # Allow multiple origins separated by comma
            self.cors_origins = [origin.strip() for origin in cors_origins.split(",")]
        else:
            # Default to allowing all (for development)
            # In production, set CORS_ORIGINS environment variable
            self.cors_origins = ["*"]
        
        # JWT secret (required in production)
        self.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
        self.is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        
        # Validate required settings
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not self.supabase_service_key:
            raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")
        if not self.apify_token:
            raise ValueError("APIFY_TOKEN environment variable is required")
        
        # In production, JWT secret is required
        if self.is_production and not self.supabase_jwt_secret:
            raise ValueError(
                "SUPABASE_JWT_SECRET environment variable is REQUIRED in production. "
                "Set ENVIRONMENT=production and SUPABASE_JWT_SECRET in your environment."
            )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
