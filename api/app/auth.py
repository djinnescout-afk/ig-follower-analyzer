"""Authentication middleware for FastAPI"""
from typing import Optional
import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import jwt
from jwt import PyJWKClient
import os
import httpx

from .config import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer()


def verify_jwt_token(token: str) -> Optional[str]:
    """
    Verify JWT token and return user_id.
    Returns None if token is invalid.
    
    Supports multiple Supabase JWT signing methods:
    - HS256 (legacy): Uses SUPABASE_JWT_SECRET (symmetric key)
    - ES256/RS256 (new): Uses JWKS endpoint from Supabase (automatic key fetching)
    
    The 'sub' claim contains the user UUID.
    """
    if not token:
        logger.warning("[AUTH] No token provided")
        return None
    
    try:
        # First, decode the header to see what algorithm is used
        unverified_header = jwt.get_unverified_header(token)
        algorithm = unverified_header.get("alg", "HS256")
        
        logger.debug(f"[AUTH] Token uses algorithm: {algorithm}")
        print(f"[AUTH] Token uses algorithm: {algorithm}")
        
        # Handle ES256/RS256 (new Supabase projects with JWKS)
        if algorithm in ["ES256", "RS256"]:
            supabase_url = os.getenv("SUPABASE_URL", "")
            
            if not supabase_url:
                error_msg = "[AUTH] ES256/RS256 token detected but SUPABASE_URL not set!"
                logger.error(error_msg)
                print(error_msg)
                return None
            
            # Construct JWKS endpoint URL
            # Supabase JWKS endpoint can be at different paths:
            # - https://[project-ref].supabase.co/.well-known/jwks.json (standard)
            # - https://[project-ref].supabase.co/auth/v1/.well-known/jwks.json (alternative)
            base_url = supabase_url.rstrip('/')
            jwks_urls = [
                f"{base_url}/.well-known/jwks.json",  # Standard Supabase path
                f"{base_url}/auth/v1/.well-known/jwks.json",  # Alternative path
            ]
            
            last_error = None
            
            # Try each JWKS URL until one works
            for jwks_url in jwks_urls:
                try:
                    logger.debug(f"[AUTH] Trying JWKS URL: {jwks_url}")
                    print(f"[AUTH] Trying JWKS URL: {jwks_url}")
                    # Use PyJWKClient to fetch and cache keys from JWKS endpoint
                    jwks_client = PyJWKClient(jwks_url, cache_ttl=3600)  # Cache for 1 hour
                    signing_key = jwks_client.get_signing_key_from_jwt(token)
                    
                    # Verify token with the key from JWKS
                    payload = jwt.decode(
                        token,
                        signing_key.key,
                        algorithms=["ES256", "RS256"],  # Support both
                        audience="authenticated"
                    )
                    user_id = payload.get("sub")
                    success_msg = f"[AUTH] {algorithm} token verified successfully via JWKS ({jwks_url}): user_id={user_id}"
                    logger.info(success_msg)
                    print(success_msg)
                    return user_id
                except jwt.InvalidTokenError as e:
                    # Token verification failed - don't try other URLs
                    error_msg = f"[AUTH] {algorithm} token verification failed: {e}"
                    logger.warning(error_msg)
                    print(error_msg)
                    import traceback
                    print(traceback.format_exc())
                    return None
                except Exception as e:
                    # JWKS fetch failed - try next URL
                    last_error = e
                    error_msg = f"[AUTH] Error with JWKS URL {jwks_url}: {type(e).__name__}: {e}"
                    logger.warning(error_msg)
                    print(error_msg)
                    import traceback
                    print(traceback.format_exc())
                    continue
            
            # All JWKS URLs failed
            if last_error:
                error_msg = f"[AUTH] All JWKS URLs failed. Last error: {type(last_error).__name__}: {last_error}"
                logger.error(error_msg)
                print(error_msg)
                import traceback
                print(traceback.format_exc())
            return None
        
        # Fall back to HS256 (legacy Supabase projects)
        elif algorithm == "HS256":
            jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
            
            if not jwt_secret:
                # Check if we're in production
                is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
                
                if is_production:
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
            
            # Verify and decode the token with HS256
            secret_length = len(jwt_secret)
            logger.debug(f"[AUTH] Attempting to verify HS256 token with secret (length: {secret_length})")
            print(f"[AUTH] Attempting to verify HS256 token with secret (length: {secret_length})")
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )
            user_id = payload.get("sub")
            success_msg = f"[AUTH] HS256 token verified successfully: user_id={user_id}"
            logger.info(success_msg)
            print(success_msg)
            return user_id
        
        else:
            error_msg = f"[AUTH] Unsupported algorithm: {algorithm}"
            logger.error(error_msg)
            print(error_msg)
            return None
        
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

