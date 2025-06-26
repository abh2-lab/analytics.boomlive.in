# from fastapi import APIRouter, Request, Depends, HTTPException, status
# from services.facebook_service import get_facebook_auth_url, exchange_facebook_token, get_page_insights
# from services.token_service import is_authenticated

# router = APIRouter()

# @router.get("/login/facebook")
# async def login_facebook():
#     """Initiates Facebook OAuth flow and returns the authorization URL"""
#     auth_url = get_facebook_auth_url()
#     return {"auth_url": auth_url}

# @router.get("/callback/facebook")
# async def facebook_callback(request: Request, code: str = None, error: str = None):
#     """Handles the Facebook OAuth callback"""
#     if error:
#         raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
#     if not code:
#         raise HTTPException(status_code=400, detail="No authorization code provided")

#     token_info = exchange_facebook_token(request, code)
#     return {"message": "Facebook Authentication successful", "authenticated": True}

# @router.get("/page-insights/{page_id}")
# async def fetch_page_insights(request: Request, page_id: str, _: bool = Depends(is_authenticated)):
#     """Retrieve insights for a Facebook Page"""
#     return get_page_insights(request, page_id)
# routers/facebook_routers.py

from fastapi import APIRouter, Query, HTTPException
from services.facebook_service import (
    get_facebook_metadata,
    get_instagram_metadata,
    get_combined_insights,
    test_app_info
)

router = APIRouter()

@router.get("/facebook-page")
def facebook_page():
    return get_facebook_metadata()

@router.get("/instagram-account")
def instagram_account():
    return get_instagram_metadata()

@router.get("/social-insights")
def social_insights(
    since: str = Query(..., description="Start date in YYYY-MM-DD"),
    until: str = Query(..., description="End date in YYYY-MM-DD")
):
    return get_combined_insights(since, until)

@router.get("/test/app-info")
def test_facebook_app():
    return test_app_info()
