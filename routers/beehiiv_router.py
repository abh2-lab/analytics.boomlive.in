from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

# Pydantic models
class StatsResponse(BaseModel):
    total_subscribers: int
    active_subscribers: int
    avg_open_rate: float
    avg_click_rate: float
    last_updated: str

class SubscriberResponse(BaseModel):
    id: str
    email: str
    status: str
    created: int
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None

class EngagementSegment(BaseModel):
    count: int
    percentage: float
    top_subscribers: Optional[List[Dict]] = None
    sample_subscribers: Optional[List[Dict]] = None

class ActivityInsights(BaseModel):
    engagement_segments: Dict[str, EngagementSegment]
    growth_metrics: Dict[str, Any]
    acquisition_sources: Dict[str, int]
    status_breakdown: Dict[str, int]
    churn_indicators: Dict[str, Any]

# Import the service
from services.beehiiv_service import BeehiivService

router = APIRouter()

def get_service() -> BeehiivService:
    """Get BeehiivService instance from environment variables"""
    api_token = os.getenv("BEEHIIV_API_TOKEN")
    publication_id = os.getenv("BEEHIIV_PUBLICATION_ID")
    
    if not api_token:
        raise HTTPException(status_code=500, detail="BEEHIIV_API_TOKEN environment variable not set")
    if not publication_id:
        raise HTTPException(status_code=500, detail="BEEHIIV_PUBLICATION_ID environment variable not set")
    
    return BeehiivService(api_token, publication_id)

@router.get("/stats", response_model=StatsResponse)
async def get_stats(service: BeehiivService = Depends(get_service)):
    try:
        stats = service.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity-insights")
async def get_activity_insights(service: BeehiivService = Depends(get_service)):
    """Get detailed subscriber activity insights and engagement analysis"""
    try:
        insights = service.get_activity_insights()
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscribers", response_model=List[SubscriberResponse])
async def get_subscribers(
    engagement: Optional[str] = Query(None, description="Filter by engagement level: high, medium, low"),
    service: BeehiivService = Depends(get_service)
):
    try:
        subs = service.get_subscriptions()
        
        # Filter by engagement if specified
        if engagement:
            filtered_subs = []
            for sub in subs:
                stats = sub.get("stats", {})
                open_rate = stats.get("open_rate", 0)
                click_rate = stats.get("click_rate", 0)
                
                if engagement == "high" and (open_rate >= 50 or click_rate >= 10):
                    filtered_subs.append(sub)
                elif engagement == "medium" and (20 <= open_rate < 50 or 3 <= click_rate < 10):
                    filtered_subs.append(sub)
                elif engagement == "low" and (open_rate < 20 and click_rate < 3):
                    filtered_subs.append(sub)
            
            subs = filtered_subs
        
        return [
            SubscriberResponse(
                id=sub.get("id", ""),
                email=sub.get("email", ""),
                status=sub.get("status", ""),
                created=sub.get("created", 0),
                open_rate=sub.get("stats", {}).get("open_rate"),
                click_rate=sub.get("stats", {}).get("click_rate")
            ) for sub in subs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscriber/{email}")
async def get_subscriber_details(email: str, service: BeehiivService = Depends(get_service)):
    """Get detailed information about a specific subscriber"""
    try:
        subscriber = service.get_subscriber_by_email(email)
        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        stats = subscriber.get("stats", {})
        return {
            "subscriber_info": {
                "id": subscriber.get("id"),
                "email": subscriber.get("email"),
                "status": subscriber.get("status"),
                "created": subscriber.get("created"),
                "utm_source": subscriber.get("utm_source"),
                "utm_medium": subscriber.get("utm_medium")
            },
            "engagement_metrics": {
                "open_rate": stats.get("open_rate", 0),
                "click_rate": stats.get("click_rate", 0),
                "total_sent": stats.get("total_sent", 0),
                "total_received": stats.get("total_received", 0),
                "total_unique_opened": stats.get("total_unique_opened", 0),
                "total_clicked": stats.get("total_clicked", 0)
            },
            "engagement_level": (
                "high" if stats.get("open_rate", 0) >= 50 or stats.get("click_rate", 0) >= 10
                else "medium" if stats.get("open_rate", 0) >= 20 or stats.get("click_rate", 0) >= 3
                else "low"
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/engagement-report")
async def get_engagement_report(service: BeehiivService = Depends(get_service)):
    """Get a comprehensive engagement report for newsletter optimization"""
    try:
        insights = service.get_activity_insights()
        basic_stats = service.get_stats()
        
        # Calculate additional metrics
        total_subs = basic_stats["total_subscribers"]
        high_engagement_count = insights["engagement_segments"]["high_engagement"]["count"]
        low_engagement_count = insights["engagement_segments"]["low_engagement"]["count"]
        
        return {
            "summary": {
                "total_subscribers": total_subs,
                "avg_open_rate": basic_stats["avg_open_rate"],
                "avg_click_rate": basic_stats["avg_click_rate"],
                "engagement_health_score": round((high_engagement_count / total_subs * 100), 1) if total_subs else 0
            },
            "growth_analysis": insights["growth_metrics"],
            "engagement_breakdown": insights["engagement_segments"],
            "acquisition_performance": insights["acquisition_sources"],
            "recommendations": {
                "re_engagement_needed": low_engagement_count,
                "top_performing_source": max(insights["acquisition_sources"].items(), key=lambda x: x[1])[0] if insights["acquisition_sources"] else "N/A",
                "churn_risk": insights["churn_indicators"]["churn_rate"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "beehiiv_api"}