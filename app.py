from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv

from routers import auth_router, facebook_router, google_router, spotify_router, beehiiv_router, auth_router2

# Load environment variables
load_dotenv()

app = FastAPI(title="Multi-Platform Analytics API", debug=True)

# Add session middleware for token storage
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("JWT_SECRET", "your_random_secure_string"),
    max_age=3600  # Session expires after 1 hour
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for authentication and Facebook services
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(auth_router2.router, prefix="/auth2", tags=["Authentication2"])

app.include_router(facebook_router, prefix="/facebook", tags=["Facebook Insights"])

# Commented out for now
# app.include_router(spotify_router, prefix="/spotify", tags=["Spotify Analysis"])
app.include_router(google_router, prefix="/google", tags=["Google Analytics & YouTube"])
app.include_router(beehiiv_router.router, prefix="/newsletter", tags=["Newsletter Analytics"])
@app.get("/")
async def root():
    """
    Root endpoint that confirms API is running
    """
    return {"message": "Multi-Platform Analytics API is running. Use /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
