from __future__ import annotations
import os
from cachetools import TTLCache

def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

QUOTE_TTL_S  = _int("QUOTE_TTL_S", 8)
SEARCH_TTL_S = _int("SEARCH_TTL_S", 3600)
HIST_TTL_S   = _int("HIST_TTL_S", 300)
OPT_TTL_S    = _int("OPT_TTL_S", 60)

def cache_quote() -> TTLCache:  return TTLCache(maxsize=2048, ttl=QUOTE_TTL_S)
def cache_search() -> TTLCache: return TTLCache(maxsize=512, ttl=SEARCH_TTL_S)
def cache_hist() -> TTLCache:   return TTLCache(maxsize=256, ttl=HIST_TTL_S)
def cache_opts() -> TTLCache:   return TTLCache(maxsize=512, ttl=OPT_TTL_S)

