"""
Exchange Rate Utility for Finance Tracker
Fetches USD/IDR exchange rates for currency conversion
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# Cache exchange rate for 1 hour to avoid excessive API calls
_cached_rate: Optional[float] = None
_cache_timestamp: Optional[datetime] = None
CACHE_DURATION = timedelta(hours=1)

# Fallback rate if API fails (approximate USD/IDR rate)
FALLBACK_RATE = 16000.0


async def get_usd_to_idr_rate() -> float:
    """
    Fetch current USD to IDR exchange rate.
    Uses caching to minimize API calls.

    Returns:
        Exchange rate (1 USD = X IDR)
    """
    global _cached_rate, _cache_timestamp

    # Check cache
    if _cached_rate is not None and _cache_timestamp is not None:
        if datetime.now() - _cache_timestamp < CACHE_DURATION:
            return _cached_rate

    # Try to fetch fresh rate
    try:
        rate = await _fetch_exchange_rate()
        if rate:
            _cached_rate = rate
            _cache_timestamp = datetime.now()
            return rate
    except Exception as e:
        logger.warning(f"Failed to fetch exchange rate: {e}")

    # Return cached rate if available, otherwise fallback
    if _cached_rate is not None:
        logger.info(f"Using cached exchange rate: {_cached_rate}")
        return _cached_rate

    logger.warning(f"Using fallback exchange rate: {FALLBACK_RATE}")
    return FALLBACK_RATE


async def _fetch_exchange_rate() -> Optional[float]:
    """
    Fetch exchange rate from free API.
    Uses exchangerate-api.com (free tier: 1500 requests/month)
    """
    # Try free exchangerate.host API first (no key required)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.exchangerate.host/latest",
                params={"base": "USD", "symbols": "IDR"}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "rates" in data:
                    rate = data["rates"].get("IDR")
                    if rate:
                        logger.info(f"Fetched exchange rate from exchangerate.host: {rate}")
                        return float(rate)
    except Exception as e:
        logger.debug(f"exchangerate.host failed: {e}")

    # Fallback to frankfurter.app (free, no key required)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.frankfurter.app/latest",
                params={"from": "USD", "to": "IDR"}
            )
            if response.status_code == 200:
                data = response.json()
                rate = data.get("rates", {}).get("IDR")
                if rate:
                    logger.info(f"Fetched exchange rate from frankfurter.app: {rate}")
                    return float(rate)
    except Exception as e:
        logger.debug(f"frankfurter.app failed: {e}")

    return None


def convert_usd_to_idr(usd_amount: float, rate: float) -> float:
    """
    Convert USD amount to IDR.

    Args:
        usd_amount: Amount in USD
        rate: Exchange rate (1 USD = X IDR)

    Returns:
        Amount in IDR
    """
    return usd_amount * rate


def get_cached_rate() -> Optional[float]:
    """Get the currently cached rate without fetching."""
    return _cached_rate


def set_fallback_rate(rate: float) -> None:
    """
    Override the fallback rate.
    Useful for testing or manual rate setting.
    """
    global FALLBACK_RATE
    FALLBACK_RATE = rate
