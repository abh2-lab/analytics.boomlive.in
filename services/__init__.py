# Export essential services related to Spotify user insights and Facebook authentication
from .token_service import (
    create_google_oauth,
    get_token_from_session, 
    save_token_to_session,
    # get_refreshed_token,
    # is_token_expired,
    is_authenticated
)
from .spotify_service import (
    get_spotify_auth_url,
    get_user_artists,
    exchange_spotify_token,
)
from .facebook_service import (
    fetch_graph,
    get_instagram_metadata,
    get_facebook_metadata,
    get_combined_insights,
    
)

# Export essential services related to Beehiiv newsletter analytics
from .beehiiv_service import (
    BeehiivService,

)
# Explicit module exports
__all__ = [
    # Token Service
    "create_google_oauth",
    "get_token_from_session",
    "save_token_to_session",
    # "get_refreshed_token",
    # "is_token_expired",
    "is_authenticated",
    
    # Spotify Service (User Insights Only)
    "get_spotify_auth_url",
    "get_user_artists",
    "exchange_spotify_token",

    # Facebook Service
    "get_facebook_auth_url",
    "exchange_facebook_token",
    "get_page_insights",
    "BeehiivService",
    "SubscriptionStatus", 
    "SubscriptionTier",
    "SubscriptionStats",
    "GeneralizedStats",
]
