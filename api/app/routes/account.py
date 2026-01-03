"""Account routes for user account state management"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Literal
import logging
from supabase import create_client, Client

from ..auth import get_current_user_id
from ..config import get_settings
from ..db import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/account", tags=["account"])


class AccountStatusResponse(BaseModel):
    account_state: Literal["active", "paused"]


@router.get("/status", response_model=AccountStatusResponse)
async def get_account_status(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Get current user's account state"""
    try:
        settings = get_settings()
        # Use service role key to access auth.users
        admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Get user from auth.users
        response = admin_client.auth.admin.get_user_by_id(user_id)
        if not response or not response.user:
            logger.warning(f"[ACCOUNT] User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = response.user
        # Get account_state from user_metadata, default to 'active'
        user_metadata = user.user_metadata or {}
        account_state = user_metadata.get("account_state", "active")
        
        # Ensure it's a valid value
        if account_state not in ["active", "paused"]:
            account_state = "active"
        
        return AccountStatusResponse(account_state=account_state)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ACCOUNT] Error fetching account status for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch account status"
        )

