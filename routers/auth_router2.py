from fastapi import APIRouter, Request, HTTPException, Query, Depends
import httpx
import json
from datetime import datetime, timedelta
from services.google_service import (
    get_google_auth_url,
    create_google_oauth_flow,
    get_ga4_property,
    get_combined_ga4_analytics_auto,
    get_combined_youtube_analytics_auto,
    get_partner_channels,
    get_owner_channel,
    get_combined_youtube_analytics,
    get_combined_ga4_analytics
)

router = APIRouter()

# API Configuration
TOKEN_API_BASE_URL = "https://your-api-domain.com/api"  # Replace with your API URL
API_TIMEOUT = 30

async def store_token_in_db(user_id: str, token_data: dict, service: str = "google"):
    """Store token in database via API"""
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        payload = {
            "user_id": user_id,
            "service": service,
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "token_type": token_data.get("token_type", "Bearer"),
            "expires_at": token_data.get("expires_at"),
            "scope": token_data.get("scope"),
            "created_at": datetime.utcnow().isoformat()
        }
        print("payload", payload)
        response = await client.post(f"{TOKEN_API_BASE_URL}/tokens", json=payload)
        response.raise_for_status()
        return response.json()

async def get_token_from_db(user_id: str, service: str = "google"):
    """Retrieve token from database via API"""
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        response = await client.get(f"{TOKEN_API_BASE_URL}/tokens/{user_id}/{service}")
        response.raise_for_status()
        return response.json()

async def delete_token_from_db(user_id: str, service: str = "google"):
    """Delete token from database via API"""
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        response = await client.delete(f"{TOKEN_API_BASE_URL}/tokens/{user_id}/{service}")
        response.raise_for_status()
        return response.json()

def get_user_id(request: Request) -> str:
    """Extract user ID from request - implement based on your auth system"""
    # Replace with your actual user identification logic
    return request.headers.get("user-id") or "default_user"

async def is_authenticated_db(request: Request):
    """Check if user is authenticated via database"""
    user_id = get_user_id(request)
    try:
        token_data = await get_token_from_db(user_id)
        return token_data.get("access_token") is not None
    except:
        return False

@router.get("/auth/login/google")
async def login_google():
    """Initiates Google OAuth flow"""
    auth_url = get_google_auth_url()
    return {"auth_url": auth_url}

@router.get("/auth/callback/google")
async def google_callback(request: Request, code: str = None, error: str = None):
    """Handles Google OAuth callback and stores token in database"""
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")

    try:
        flow = create_google_oauth_flow()
        flow.fetch_token(code=code)
        
        token_info = json.loads(flow.credentials.to_json())
        user_id = get_user_id(request)
        
        # Store token in database
        await store_token_in_db(user_id, token_info)
        
        return {
            "message": "Google Authentication successful", 
            "authenticated": True,
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to authenticate: {str(e)}")

@router.get("/auth/status")
async def auth_status(request: Request):
    """Check authentication status"""
    user_id = get_user_id(request)
    try:
        token_data = await get_token_from_db(user_id)
        return {
            "authenticated": True,
            "user_id": user_id,
            "expires_at": token_data.get("expires_at")
        }
    except:
        return {"authenticated": False}

@router.get("/google/youtube/partner-channels")
async def fetch_partner_channels(request: Request):
    """Retrieve YouTube partner channels"""
    if not await is_authenticated_db(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        return get_partner_channels(request)
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/google/youtube/owner-channel")
async def fetch_owner_channel(request: Request):
    """Retrieve owned YouTube channel"""
    if not await is_authenticated_db(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        return get_owner_channel(request)
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/google/youtube/analytics/auto")
async def fetch_youtube_analytics_auto(
    request: Request,
    start_date: str = Query("2024-01-01"),
    end_date: str = Query("2024-04-01")
):
    """Retrieve YouTube analytics automatically"""
    if not await is_authenticated_db(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        return get_combined_youtube_analytics_auto(request, start_date, end_date)
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/google/ga4/analytics/auto")
async def fetch_ga4_analytics_auto(
    request: Request,
    start_date: str = Query("2024-01-01"),
    end_date: str = Query("2024-04-01"),
    has_admin_access: bool = Query(False)
):
    """Retrieve GA4 analytics automatically"""
    if not await is_authenticated_db(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        return get_combined_ga4_analytics_auto(request, start_date, end_date, has_admin_access)
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/auth/logout")
async def logout(request: Request):
    """Logout by deleting token from database"""
    user_id = get_user_id(request)
    try:
        await delete_token_from_db(user_id)
        return {"message": "Logged out successfully"}
    except Exception as e:
        return {"message": "Logout completed", "note": str(e)}