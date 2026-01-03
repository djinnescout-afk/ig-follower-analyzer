"""Settings routes for user preferences"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from supabase import create_client, Client

from ..auth import get_current_user_id
from ..config import get_settings
from ..db import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["settings"])


class PreferencesResponse(BaseModel):
    category_set: str


class UpdatePreferencesRequest(BaseModel):
    category_set: str


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Get user's preferences"""
    try:
        response = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            return PreferencesResponse(category_set=response.data[0].get("category_set", "option1"))
        else:
            # Return default if no preferences exist
            return PreferencesResponse(category_set="option1")
    except Exception as e:
        logger.error(f"[SETTINGS] Error fetching preferences for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch preferences"
        )


@router.put("/preferences", response_model=PreferencesResponse)
async def update_preferences(
    request: UpdatePreferencesRequest,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Update user's preferences"""
    if request.category_set not in ["option1", "option2"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category_set must be 'option1' or 'option2'"
        )
    
    try:
        # Try to update existing preferences
        update_response = supabase.table("user_preferences").update({
            "category_set": request.category_set,
            "updated_at": "now()"
        }).eq("user_id", user_id).execute()
        
        # If no rows were updated, insert new preferences
        if not update_response.data or len(update_response.data) == 0:
            insert_response = supabase.table("user_preferences").insert({
                "user_id": user_id,
                "category_set": request.category_set
            }).execute()
            
            if not insert_response.data or len(insert_response.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create preferences"
                )
            
            return PreferencesResponse(category_set=insert_response.data[0].get("category_set"))
        
        return PreferencesResponse(category_set=update_response.data[0].get("category_set"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SETTINGS] Error updating preferences for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )

