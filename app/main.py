from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.claims import router as claims_router
from app.database import create_db_and_tables

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Claim Processing Service",
    description="A service for processing dental claims",
    version="1.0.0",
)

# Add rate limiter exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(claims_router)


@app.on_event("startup")
def on_startup():
    """Create database tables on startup"""
    create_db_and_tables()


@app.get("/")
@limiter.limit("10/minute")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "Welcome to the Claim Processing Service",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
