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
            # Check if we're in production
            is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
            
            if is_production:
                # In production, fail hard - don't allow unverified tokens
                error_msg = "[AUTH] CRITICAL: SUPABASE_JWT_SECRET not set in production!"
                logger.error(error_msg)
                print(error_msg)
                return None
            
            # Development fallback: decode without verification (INSECURE)
            logger.warning("[AUTH] SUPABASE_JWT_SECRET not set, decoding without verification (INSECURE - dev only)")
            print("[AUTH] WARNING: SUPABASE_JWT_SECRET not set, decoding without verification")
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")
            logger.info(f"[AUTH] Token decoded (no verification): user_id={user_id}")
            print(f"[AUTH] Token decoded (no verification): user_id={user_id}")
            return user_id
        
        # Verify and decode the token
        # Supabase JWTs require audience="authenticated" for authenticated users
        secret_length = len(jwt_secret)
        logger.debug(f"[AUTH] Attempting to verify token with secret (length: {secret_length})")
        print(f"[AUTH] Attempting to verify token with secret (length: {secret_length})")  # Print for Render logs
        payload = jwt.decode(
            token, 
            jwt_secret, 
            algorithms=["HS256"],
            audience="authenticated"  # Supabase JWTs require this audience
        )
        user_id = payload.get("sub")
        success_msg = f"[AUTH] Token verified successfully: user_id={user_id}"
        logger.info(success_msg)
        print(success_msg)  # Print for Render logs
        return user_id  # 'sub' is the user ID in Supabase JWTs
        
    except jwt.ExpiredSignatureError as e:
        error_msg = f"[AUTH] Token expired: {e}"
        logger.warning(error_msg)
        print(error_msg)  # Print to stdout for Render logs
        return None
    except jwt.InvalidTokenError as e:
        error_msg = f"[AUTH] Invalid token: {e}"
        logger.warning(error_msg)
        print(error_msg)  # Print to stdout for Render logs
        return None
    except Exception as e:
        error_msg = f"[AUTH] Unexpected error verifying token: {type(e).__name__}: {e}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)  # Print to stdout for Render logs
        import traceback
        print(traceback.format_exc())  # Print full traceback
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
    token_length = len(token) if token else 0
    logger.debug(f"[AUTH] Received token (length: {token_length})")
    print(f"[AUTH] Received token (length: {token_length})")  # Print for Render logs
    
    user_id = verify_jwt_token(token)
    
    if not user_id:
        error_msg = "[AUTH] Token verification failed, returning 401"
        logger.error(error_msg)
        print(error_msg)  # Print for Render logs
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

