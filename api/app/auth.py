"""Authentication middleware for FastAPI"""
from typing import Optional
import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import jwt
import os

from .config import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer()


def verify_jwt_token(token: str) -> Optional[str]:
    """
    Verify JWT token and return user_id.
    Returns None if token is invalid.
    
    Supabase JWTs are signed with the JWT_SECRET (found in Supabase dashboard).
    The 'sub' claim contains the user UUID.
    """
    if not token:
        logger.warning("[AUTH] No token provided")
        return None
    
    try:
        # Get JWT secret from environment (set this in your .env)
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
        
        if not jwt_secret:
            logger.warning("[AUTH] SUPABASE_JWT_SECRET not set, decoding without verification (INSECURE - dev only)")
            # Fallback: Try to decode without verification (NOT SECURE - for development only)
            # In production, you MUST set SUPABASE_JWT_SECRET
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")
            logger.info(f"[AUTH] Token decoded (no verification): user_id={user_id}")
            return user_id
        
        # Verify and decode the token
        logger.debug(f"[AUTH] Attempting to verify token with secret (length: {len(jwt_secret)})")
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        logger.info(f"[AUTH] Token verified successfully: user_id={user_id}")
        return user_id  # 'sub' is the user ID in Supabase JWTs
        
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"[AUTH] Token expired: {e}")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"[AUTH] Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"[AUTH] Unexpected error verifying token: {type(e).__name__}: {e}", exc_info=True)
        return None


def get_user_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extract and verify JWT token from Authorization header.
    Returns user_id if valid, raises 401 if invalid.
    """
    if not credentials:
        logger.warning("[AUTH] No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    logger.debug(f"[AUTH] Received token (length: {len(token) if token else 0})")
    
    user_id = verify_jwt_token(token)
    
    if not user_id:
        logger.error("[AUTH] Token verification failed, returning 401")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"[AUTH] Token verified, user_id: {user_id}")
    return user_id


# Dependency for protected routes
def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current user ID from JWT token"""
    return get_user_id_from_token(credentials)

