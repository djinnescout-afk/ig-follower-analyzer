"""Admin routes for user management and debugging"""
from fastapi import APIRouter, HTTPException, status, Depends, Body
from typing import List, Optional
from pydantic import BaseModel
import os
import logging
from supabase import create_client, Client

from ..auth import get_current_user_id
from ..config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_emails() -> List[str]:
    """Get list of admin emails from environment variable"""
    admin_emails_str = os.getenv("ADMIN_EMAILS", "")
    logger.info(f"[ADMIN] ADMIN_EMAILS env var value: '{admin_emails_str}'")
    if not admin_emails_str:
        logger.warning("[ADMIN] ADMIN_EMAILS environment variable is not set!")
        return []
    emails = [email.strip().lower() for email in admin_emails_str.split(",") if email.strip()]
    logger.info(f"[ADMIN] Parsed admin emails: {emails}")
    return emails


def check_is_admin(user_id: str) -> bool:
    """Check if the current user is an admin"""
    try:
        settings = get_settings()
        # Use service role key to access auth.users table
        admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Get user email from auth.users
        response = admin_client.auth.admin.get_user_by_id(user_id)
        if not response or not response.user:
            logger.warning(f"[ADMIN] User not found: {user_id}")
            return False
        
        user_email = response.user.email
        if not user_email:
            logger.warning(f"[ADMIN] User has no email: {user_id}")
            return False
        
        admin_emails = get_admin_emails()
        user_email_lower = user_email.lower().strip()
        
        logger.info(f"[ADMIN] Checking admin access for: {user_email_lower}")
        logger.info(f"[ADMIN] Admin emails list: {admin_emails}")
        
        is_admin = user_email_lower in admin_emails
        logger.info(f"[ADMIN] Is admin: {is_admin}")
        
        return is_admin
    except Exception as e:
        logger.error(f"[ADMIN] Error checking admin status: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        return False


def get_supabase_admin_client() -> Client:
    """Get Supabase client with service role key for admin operations"""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)


@router.get("/test-admin")
def test_admin_access(user_id: str = Depends(get_current_user_id)):
    """Test endpoint to debug admin access (returns debug info)"""
    try:
        settings = get_settings()
        admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Get user email
        response = admin_client.auth.admin.get_user_by_id(user_id)
        user_email = response.user.email if response and response.user else None
        
        admin_emails = get_admin_emails()
        is_admin = check_is_admin(user_id)
        
        return {
            "user_id": user_id,
            "user_email": user_email,
            "admin_emails_from_env": admin_emails,
            "is_admin": is_admin,
            "env_var_raw": os.getenv("ADMIN_EMAILS", "NOT_SET")
        }
    except Exception as e:
        logger.error(f"[ADMIN] Error in test endpoint: {e}", exc_info=True)
        return {
            "error": str(e),
            "user_id": user_id
        }


@router.get("/users")
def list_users(user_id: str = Depends(get_current_user_id)):
    """List all users (admin only)"""
    if not check_is_admin(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        admin_client = get_supabase_admin_client()
        # List all users using admin API
        response = admin_client.auth.admin.list_users()
        
        users = []
        for user in response.users:
            users.append({
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at,
                "last_sign_in_at": user.last_sign_in_at,
                "email_confirmed_at": user.email_confirmed_at,
            })
        
        return {"users": users}
    except Exception as e:
        logger.error(f"[ADMIN] Error listing users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing users: {str(e)}"
        )


class GenerateMagicLinkRequest(BaseModel):
    target_user_id: str
    redirect_to: Optional[str] = None


@router.post("/generate-magic-link")
def generate_magic_link(
    request: GenerateMagicLinkRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Generate a magic link for a user (admin only)"""
    target_user_id = request.target_user_id
    redirect_to = request.redirect_to
    if not check_is_admin(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        admin_client = get_supabase_admin_client()
        
        # Get user email first
        user_response = admin_client.auth.admin.get_user_by_id(target_user_id)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_email = user_response.user.email
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no email"
            )
        
        # Default redirect to the app URL
        if not redirect_to:
            redirect_to = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # Generate magic link using admin API
        # The generate_link method signature: generate_link(type, email, options={})
        link_response = admin_client.auth.admin.generate_link(
            type="magiclink",
            email=user_email,
            options={
                "redirect_to": redirect_to
            }
        )
        
        # Extract the magic link from the response
        # The response structure may vary, so we'll handle it safely
        magic_link = None
        if hasattr(link_response, 'properties') and hasattr(link_response.properties, 'action_link'):
            magic_link = link_response.properties.action_link
        elif hasattr(link_response, 'action_link'):
            magic_link = link_response.action_link
        elif isinstance(link_response, dict):
            magic_link = link_response.get('action_link') or link_response.get('properties', {}).get('action_link')
        
        if not magic_link:
            # Fallback: construct the link manually if needed
            logger.warning(f"[ADMIN] Could not extract magic link from response: {link_response}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate magic link - invalid response format"
            )
        
        return {
            "magic_link": magic_link,
            "user_email": user_email,
            "user_id": target_user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] Error generating magic link: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating magic link: {str(e)}"
        )

