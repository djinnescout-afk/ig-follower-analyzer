"""Authentication middleware for FastAPI"""
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import jwt
import os

from .config import get_settings

security = HTTPBearer()


def verify_jwt_token(token: str) -> Optional[str]:
    """
    Verify JWT token and return user_id.
    Returns None if token is invalid.
    
    Supabase JWTs are signed with the JWT_SECRET (found in Supabase dashboard).
    The 'sub' claim contains the user UUID.
    """
    try:
        # Get JWT secret from environment (set this in your .env)
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
        
        if not jwt_secret:
            # Fallback: Try to decode without verification (NOT SECURE - for development only)
            # In production, you MUST set SUPABASE_JWT_SECRET
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub")
        
        # Verify and decode the token
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        return payload.get("sub")  # 'sub' is the user ID in Supabase JWTs
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def get_user_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extract and verify JWT token from Authorization header.
    Returns user_id if valid, raises 401 if invalid.
    """
    token = credentials.credentials
    
    user_id = verify_jwt_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


# Dependency for protected routes
def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current user ID from JWT token"""
    return get_user_id_from_token(credentials)

