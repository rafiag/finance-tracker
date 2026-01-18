from datetime import datetime, timedelta
from typing import Any

class SimpleCache:
    """Simple in-memory cache with TTL for static data."""
    
    def __init__(self, ttl_minutes: int = 5):
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
    
    def get(self, key: str) -> Any | None:
        """Get cached value if not expired."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                return data
        return None
    
    def set(self, key: str, value: Any):
        """Set cache value with current timestamp."""
        self._cache[key] = (value, datetime.now())

# Initialize cache with 5-minute TTL for static data
# and 2-minute TTL for summary calculations (Issue 4.3 and 4.2)
cache = SimpleCache(ttl_minutes=5)
summary_cache = SimpleCache(ttl_minutes=2)
