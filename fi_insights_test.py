import os
import requests
from datetime import datetime
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

APP_ID = os.getenv("FACEBOOK_APP_ID")
APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("FACEBOOK_USER_ACCESS_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
print("App ID:", APP_ID)

app = FastAPI(title="Social Media Analytics API", version="1.0.0")

def fetch_graph(endpoint: str, params: dict):
    """Helper function to call Facebook Graph API"""
    res = requests.get(f"https://graph.facebook.com/v23.0/{endpoint}", params=params)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    return res.json()

@app.get("/facebook-page")
def get_facebook_page_metadata():
    """Get Facebook Page metadata including followers and basic info"""
    return fetch_graph(
        f"{PAGE_ID}",
        {
            "fields": "name,fan_count,followers_count,category,about,website,phone,location",
            "access_token": ACCESS_TOKEN
        }
    )

@app.get("/instagram-account")
def get_instagram_account_metadata():
    """Get Instagram Business Account metadata"""
    return fetch_graph(
        f"{INSTAGRAM_ACCOUNT_ID}",
        {
            "fields": "username,name,biography,followers_count,follows_count,media_count,profile_picture_url,website",
            "access_token": ACCESS_TOKEN
        }
    )

@app.get("/social-insights")
def get_combined_social_insights(since: str, until: str):
    """Get combined insights from both Instagram and Facebook for date range (YYYY-MM-DD format)"""
    # Convert dates to timestamps
    fmt = "%Y-%m-%d"
    since_ts = int(datetime.strptime(since, fmt).timestamp())
    until_ts = int(datetime.strptime(until, fmt).timestamp())
    
    results = {"instagram": {}, "facebook": {}}
    
    # Instagram Insights
    ig_standard_metrics = ["reach", "follower_count"]
    for metric in ig_standard_metrics:
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
    
    ig_total_value_metrics = [
        "profile_views", "website_clicks", "accounts_engaged", 
        "total_interactions", "likes", "comments", "shares", "saves"
    ]
    for metric in ig_total_value_metrics:
        try:
            data = fetch_graph(
                f"{INSTAGRAM_ACCOUNT_ID}/insights",
                {
                    "metric": metric,
                    "period": "day",
                    "metric_type": "total_value",
                    "since": since_ts,
                    "until": until_ts,
                    "access_token": ACCESS_TOKEN
                }
            )
            results["instagram"][metric] = data
        except HTTPException as e:
            results["instagram"][metric] = {"error": str(e.detail)}
    
    # Facebook Page Insights
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
    
    # Calculate summaries
    ig_engagement = sum([
        results["instagram"].get(m, {}).get("data", [{}])[0].get("total_value", {}).get("value", 0)
        for m in ["likes", "comments", "shares", "saves"] 
        if "error" not in results["instagram"].get(m, {})
    ])
    
    return {
        "date_range": {"since": since, "until": until},
        "insights": results,
        "summary": {
            "instagram_engagement": ig_engagement,
            "instagram_successful": len([k for k, v in results["instagram"].items() if "error" not in v]),
            "facebook_successful": len([k for k, v in results["facebook"].items() if "error" not in v])
        }
    }


@app.get("/test/app-info")
def test_app_info():
    """Test basic app information using App ID"""
    if not APP_ID or not ACCESS_TOKEN:
        raise HTTPException(status_code=400, detail="APP_ID or ACCESS_TOKEN not set")
    
    try:
        print("Testing App ID:", APP_ID)
        print("Using Access Token:", ACCESS_TOKEN)
        response = requests.get(
            f"https://graph.facebook.com/v23.0/{APP_ID}",
            params={"access_token": ACCESS_TOKEN}
        )
        
        return {
            "status_code": response.status_code,
            "response": response.json(),
            "app_id_used": APP_ID
        }
    except Exception as e:
        return {
            "error": str(e),
            "app_id_used": APP_ID
        }

# @app.get("/test/facebook-metrics")
# def test_facebook_available_metrics():
#     """Test what Facebook metrics are available for your page"""
#     if not PAGE_ID or not ACCESS_TOKEN:
#         raise HTTPException(status_code=400, detail="PAGE_ID or ACCESS_TOKEN not set")
    
#     # Test individual metrics to see which ones work
#     test_metrics = [
#         "page_impressions", "page_reach", "page_post_engagements", 
#         "page_fans", "page_views_total", "page_video_views",
#         "page_actions_post_reactions_total", "page_engaged_users",
#         "page_consumptions", "page_negative_feedback"
#     ]
    
#     results = {}
    
#     # Use a recent 7-day period for testing
#     from datetime import timedelta
#     end_date = datetime.now().date()
#     start_date = end_date - timedelta(days=7)
    
#     since_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
#     until_ts = int(datetime.combine(end_date, datetime.min.time()).timestamp())
    
#     for metric in test_metrics:
#         try:
#             data = fetch_graph(
#                 f"{PAGE_ID}/insights/{metric}",
#                 {
#                     "period": "day",
#                     "since": since_ts,
#                     "until": until_ts,
#                     "access_token": PAGE_ACCESS_TOKEN
#                 }
#             )
#             results[metric] = {
#                 "status": "success",
#                 "data_points": len(data.get("data", [])),
#                 "sample": data.get("data", [])[:2]  # First 2 data points
#             }
#         except Exception as e:
#             results[metric] = {
#                 "status": "error",
#                 "error": str(e)
#             }
    
#     return {
#         "page_id": PAGE_ID,
#         "test_period": f"{start_date} to {end_date}",
#         "metrics_test": results,
#         "working_metrics": [k for k, v in results.items() if v["status"] == "success"]
#     }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)