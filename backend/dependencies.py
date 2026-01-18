import os
import logging
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)

# API Authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Verify API key for dashboard endpoints.
    Raises HTTPException if invalid or missing.
    """
    expected_key = os.getenv("DASHBOARD_API_KEY")
    
    # If no API key is configured, allow access (for backward compatibility)
    if not expected_key:
        logger.warning("DASHBOARD_API_KEY not set - API endpoints are unprotected!")
        return None
    
    # Check if API key was provided
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Please provide X-API-Key header."
        )
    
    # Verify API key matches
    if api_key != expected_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return api_key
