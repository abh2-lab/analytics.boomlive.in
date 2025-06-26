# import requests
# import os
# from fastapi import Request, HTTPException
# from services.token_service import save_token_to_session, get_token_from_session
# from dotenv import load_dotenv
# load_dotenv()
# FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_APP_ID")
# FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_APP_SECRET")
# REDIRECT_URI = "https://ba9a-58-146-101-17.ngrok-free.app/auth/callback/facebook"

# print(REDIRECT_URI, FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET)
# def get_facebook_auth_url():
#     """Generate the Facebook OAuth authorization URL"""
#     print(FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET)
#     return f"https://www.facebook.com/v18.0/dialog/oauth?client_id={FACEBOOK_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=pages_read_engagement"

# def exchange_facebook_token(request: Request, code: str):
#     """Exchange the authorization code for an access token"""
#     token_url = f"https://graph.facebook.com/v18.0/oauth/access_token"
#     params = {
#         "client_id": FACEBOOK_CLIENT_ID,
#         "client_secret": FACEBOOK_CLIENT_SECRET,
#         "redirect_uri": REDIRECT_URI,
#         "code": code
#     }
    
#     response = requests.get(token_url, params=params)
#     if response.status_code != 200:
#         raise HTTPException(status_code=400, detail="Failed to retrieve access token")
    
#     token_info = response.json()
#     save_token_to_session(request, token_info)
#     return token_info

# def get_page_insights(request: Request, page_id: str):
#     """Retrieve insights for a managed Facebook Page"""
#     token_info = get_token_from_session(request)
#     access_token = token_info.get("access_token")

#     url = f"https://graph.facebook.com/v18.0/{page_id}/insights?metric=page_impressions,page_engaged_users,page_fan_adds&period=day&access_token={access_token}"
#     response = requests.get(url)

#     if response.status_code != 200:
#         raise HTTPException(status_code=400, detail="Failed to retrieve page insights")

#     return response.json()


# services/facebook_service.py

import os
import requests
from datetime import datetime
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("FACEBOOK_APP_ID")
APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("FACEBOOK_USER_ACCESS_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

def fetch_graph(endpoint: str, params: dict):
    res = requests.get(f"https://graph.facebook.com/v23.0/{endpoint}", params=params)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    return res.json()

def get_facebook_metadata():
    return fetch_graph(
        f"{PAGE_ID}",
        {
            "fields": "name,fan_count,followers_count,category,about,website,phone,location",
            "access_token": ACCESS_TOKEN
        }
    )

def get_instagram_metadata():
    return fetch_graph(
        f"{INSTAGRAM_ACCOUNT_ID}",
        {
            "fields": "username,name,biography,followers_count,follows_count,media_count,profile_picture_url,website",
            "access_token": ACCESS_TOKEN
        }
    )

def get_combined_insights(since: str, until: str):
    fmt = "%Y-%m-%d"
    since_ts = int(datetime.strptime(since, fmt).timestamp())
    until_ts = int(datetime.strptime(until, fmt).timestamp())

    results = {"instagram": {}, "facebook": {}}

    # Instagram basic insights
    ig_metrics = ["reach", "profile_views", "impressions"]
    for metric in ig_metrics:
        try:
            data = fetch_graph(
                f"{INSTAGRAM_ACCOUNT_ID}/insights",
                {
                    "metric": metric,
                    "period": "day",
                    "since": since_ts,
                    "until": until_ts,
                    "access_token": ACCESS_TOKEN
                }
            )
            results["instagram"][metric] = data
        except HTTPException as e:
            results["instagram"][metric] = {"error": str(e.detail)}

    # Facebook insights
    fb_metrics = ["page_impressions", "page_post_engagements", "page_fans",
                  "page_views_total", "page_video_views", "page_actions_post_reactions_total"]
    for metric in fb_metrics:
        try:
            data = fetch_graph(
                f"{PAGE_ID}/insights/{metric}",
                {
                    "period": "day",
                    "since": since_ts,
                    "until": until_ts,
                    "access_token": PAGE_ACCESS_TOKEN
                }
            )
            results["facebook"][metric] = data
        except HTTPException as e:
            results["facebook"][metric] = {"error": str(e.detail)}

    # Summary
    def safe_value(metric_data):
        try:
            return metric_data.get("data", [{}])[0].get("values", [{}])[0].get("value", 0)
        except:
            return 0

    ig_engagement = sum([safe_value(results["instagram"].get(m, {})) for m in ig_metrics])

    return {
        "date_range": {"since": since, "until": until},
        "insights": results,
        "summary": {
            "instagram_engagement": ig_engagement,
            "instagram_successful": len([k for k, v in results["instagram"].items() if "error" not in v]),
            "facebook_successful": len([k for k, v in results["facebook"].items() if "error" not in v])
        }
    }

def test_app_info():
    if not APP_ID or not ACCESS_TOKEN:
        raise HTTPException(status_code=400, detail="APP_ID or ACCESS_TOKEN not set")

    response = requests.get(
        f"https://graph.facebook.com/v23.0/{APP_ID}",
        params={"access_token": ACCESS_TOKEN}
    )
    return {
        "status_code": response.status_code,
        "response": response.json(),
        "app_id_used": APP_ID
    }
