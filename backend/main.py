"""
Finance Tracker - Main FastAPI Application
Handles Telegram webhooks and orchestrates the transaction processing pipeline
Refactored into Routers
"""

import os
import logging
import json
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from dotenv import load_dotenv

from logic.gsheets_handler import get_sheets_handler
from logic.ai_processor import get_ai_processor
from logic.telegram_utils import get_telegram_handler
from dependencies import limiter

from routers import dashboard, transactions, telegram

# Load environment variables
load_dotenv()

# =============================================================================
# Structured JSON Logging
# =============================================================================

class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for production logging."""
    
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        # Add extra fields if available
        if hasattr(record, 'extra'):
            log_record.update(record.extra)
        return json.dumps(log_record)

# Configure logging handler with JSON formatter
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)
logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================

def get_cors_origins() -> list[str]:
    """Get CORS origins, filtering out empty values (Issue 3.1)."""
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    if frontend_url := os.getenv("FRONTEND_URL"):
        origins.append(frontend_url)
    return origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup: Initialize connections
    logger.info("Starting Finance Tracker...")
    
    try:
        # Verify Google Sheets connection
        sheets = get_sheets_handler()
        sheets.connect()
        logger.info("✅ Google Sheets connected")
        
        # Verify AI processor
        _ = get_ai_processor()
        logger.info("✅ Gemini AI configured")
        
        # Verify Telegram handler
        _ = get_telegram_handler()
        logger.info("✅ Telegram handler ready")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Finance Tracker...")


app = FastAPI(
    title="Finance Tracker",
    description="Personal finance tracker with Telegram integration",
    version="1.0.0",
    lifespan=lifespan
)

# =============================================================================
# Rate Limiting Configuration
# =============================================================================

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration for dashboard frontend (Issue 3.1: fixed empty origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(telegram.router)
app.include_router(dashboard.router)
app.include_router(transactions.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Finance Tracker",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Check Google Sheets
    try:
        sheets = get_sheets_handler()
        sheets.connect()
        categories = sheets.get_categories()
        health["checks"]["google_sheets"] = {
            "status": "ok",
            "categories_count": len(categories)
        }
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["google_sheets"] = {
            "status": "error",
            "message": str(e)
        }
    
    return health
    
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
