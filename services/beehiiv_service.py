import requests
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

class BeehiivService:
    def __init__(self, api_token: str, publication_id: str):
        self.api_token = api_token
        self.publication_id = publication_id
        self.base_url = "https://api.beehiiv.com/v2"
        self.headers = {"Authorization": f"Bearer {api_token}"}

    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_subscriptions(self, limit: int = 1000) -> List[Dict]:
        endpoint = f"/publications/{self.publication_id}/subscriptions"
        params = {"limit": limit, "expand[]": ["stats"], "order_by": "created", "direction": "desc"}
        return self._request(endpoint, params).get("data", [])

    def get_stats(self) -> Dict[str, Any]:
        subs = self.get_subscriptions()
        total = len(subs)
        active = sum(1 for s in subs if s.get("status") == "active")
        
        # Calculate engagement metrics
        open_rates = [s.get("stats", {}).get("open_rate", 0) for s in subs if s.get("stats")]
        click_rates = [s.get("stats", {}).get("click_rate", 0) for s in subs if s.get("stats")]
        avg_open_rate = sum(open_rates) / len(open_rates) if open_rates else 0
        avg_click_rate = sum(click_rates) / len(click_rates) if click_rates else 0
        
        return {
            "total_subscribers": total,
            "active_subscribers": active,
            "avg_open_rate": round(avg_open_rate, 2),
            "avg_click_rate": round(avg_click_rate, 2),
            "last_updated": datetime.now().isoformat()
        }

    def get_activity_insights(self) -> Dict[str, Any]:
        """Get detailed subscriber activity insights"""
        subs = self.get_subscriptions()
        now = datetime.now()
        
        # Engagement segmentation
        high_engagement = []
        medium_engagement = []
        low_engagement = []
        
        # Growth tracking
        growth_30d = 0
        growth_7d = 0
        
        # UTM source tracking
        utm_sources = defaultdict(int)
        
        # Status breakdown
        status_counts = defaultdict(int)
        
        for sub in subs:
            # Status counting
            status_counts[sub.get("status", "unknown")] += 1
            
            # Growth analysis
            created_date = datetime.fromtimestamp(sub.get("created", 0))
            days_ago = (now - created_date).days
            
            if days_ago <= 7:
                growth_7d += 1
            if days_ago <= 30:
                growth_30d += 1
            
            # UTM source tracking
            utm_source = sub.get("utm_source", "direct")
            utm_sources[utm_source] += 1
            
            # Engagement segmentation
            stats = sub.get("stats", {})
            open_rate = stats.get("open_rate", 0)
            click_rate = stats.get("click_rate", 0)
            
            if open_rate >= 50 or click_rate >= 10:
                high_engagement.append({
                    "email": sub.get("email"),
                    "open_rate": open_rate,
                    "click_rate": click_rate
                })
            elif open_rate >= 20 or click_rate >= 3:
                medium_engagement.append({
                    "email": sub.get("email"),
                    "open_rate": open_rate,
                    "click_rate": click_rate
                })
            else:
                low_engagement.append({
                    "email": sub.get("email"),
                    "open_rate": open_rate,
                    "click_rate": click_rate
                })
        
        return {
            "engagement_segments": {
                "high_engagement": {
                    "count": len(high_engagement),
                    "percentage": round(len(high_engagement) / len(subs) * 100, 1) if subs else 0,
                    "top_subscribers": high_engagement[:5]  # Top 5 most engaged
                },
                "medium_engagement": {
                    "count": len(medium_engagement),
                    "percentage": round(len(medium_engagement) / len(subs) * 100, 1) if subs else 0
                },
                "low_engagement": {
                    "count": len(low_engagement),
                    "percentage": round(len(low_engagement) / len(subs) * 100, 1) if subs else 0,
                    "sample_subscribers": low_engagement[:5]  # Sample for re-engagement
                }
            },
            "growth_metrics": {
                "new_subscribers_7d": growth_7d,
                "new_subscribers_30d": growth_30d,
                "growth_rate_weekly": round(growth_7d / len(subs) * 100, 2) if subs else 0,
                "growth_rate_monthly": round(growth_30d / len(subs) * 100, 2) if subs else 0
            },
            "acquisition_sources": dict(utm_sources),
            "status_breakdown": dict(status_counts),
            "churn_indicators": {
                "inactive_subscribers": status_counts.get("inactive", 0),
                "churn_rate": round(status_counts.get("inactive", 0) / len(subs) * 100, 2) if subs else 0
            }
        }

    def get_subscriber_by_email(self, email: str) -> Optional[Dict]:
        """Get detailed subscriber info by email"""
        endpoint = f"/publications/{self.publication_id}/subscriptions"
        params = {"email": email, "expand[]": ["stats"]}
        
        try:
            result = self._request(endpoint, params)
            subs = result.get("data", [])
            return subs[0] if subs else None
        except:
            return None