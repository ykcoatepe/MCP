from __future__ import annotations
import os
import json, sys, time as _t
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp_yahoo.config import load_config
from mcp_yahoo.providers.yf import YFProvider
try:
    from mcp_yahoo.providers.rapid import RapidProvider  # optional
except Exception:
    RapidProvider = None  # type: ignore

mcp = FastMCP("yahoo-finance-mcp")
cfg = load_config()
_provider_name: str
if (cfg.get("provider") or "yfinance").lower() == "rapidapi" and RapidProvider and cfg.get("rapidapi_key"):
    provider = RapidProvider(api_key=cfg["rapidapi_key"], host=cfg.get("rapidapi_host", ""))  # type: ignore
    _provider_name = "rapidapi"
else:
    provider = YFProvider()
    _provider_name = "yfinance"

def jlog(event: str, **kw):
    try:
        kw["event"] = event
        kw["ts"] = _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime())
        print(json.dumps(kw, ensure_ascii=False), file=sys.stdout, flush=True)
    except Exception:
        pass

@mcp.tool()
def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
    t0 = _t.perf_counter()
    try:
        items = provider.search(query)
        jlog("tool_ok", tool="search", query=query, ms=int(1000*(_t.perf_counter()-t0)))
        return {"items": items}
    except Exception as e:
        jlog("tool_err", tool="search", query=query, error=str(e))
        return {"error": {"code": "SEARCH_FAILED", "message": str(e)}}

@mcp.tool()
def fetch(id: str) -> Dict[str, Any]:
    t0 = _t.perf_counter()
    try:
        out = provider.quote(id)
        jlog("tool_ok", tool="fetch", id=id, ms=int(1000*(_t.perf_counter()-t0)))
        return out
    except Exception as e:
        jlog("tool_err", tool="fetch", id=id, error=str(e))
        return {"error": {"code": "FETCH_FAILED", "message": str(e)}}

@mcp.tool()
def get_quote(symbol: str) -> Dict[str, Any]:
    t0 = _t.perf_counter()
    try:
        out = provider.quote(symbol)
        jlog("tool_ok", tool="get_quote", symbol=symbol, ms=int(1000*(_t.perf_counter()-t0)))
        return out
    except Exception as e:
        jlog("tool_err", tool="get_quote", symbol=symbol, error=str(e))
        return {"error": {"code": "QUOTE_FAILED", "message": str(e)}}

@mcp.tool()
def get_history(
    symbol: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    interval: str = "1d",
    adjust: bool = True,
) -> Dict[str, Any]:
    """Return OHLCV bars for a symbol."""
    t0 = _t.perf_counter()
    try:
        bars = provider.history(symbol, start=start, end=end, interval=interval, adjust=adjust)
        jlog("tool_ok", tool="get_history", symbol=symbol, interval=interval, ms=int(1000*(_t.perf_counter()-t0)))
        return {"symbol": symbol.upper(), "interval": interval, "bars": bars}
    except Exception as e:
        jlog("tool_err", tool="get_history", symbol=symbol, interval=interval, error=str(e))
        return {"error": {"code": "HISTORY_FAILED", "message": str(e)}}

@mcp.tool()
def get_options_chain(symbol: str, expiry: Optional[str] = None) -> Dict[str, Any]:
    """Return option expiries and the calls/puts lists for the selected expiry."""
    t0 = _t.perf_counter()
    try:
        data = provider.options_chain(symbol, expiry)
        jlog("tool_ok", tool="get_options_chain", symbol=symbol, expiry=expiry, ms=int(1000*(_t.perf_counter()-t0)))
        return data
    except Exception as e:
        jlog("tool_err", tool="get_options_chain", symbol=symbol, expiry=expiry, error=str(e))
        return {"error": {"code": "OPTIONS_FAILED", "message": str(e)}}

@mcp.tool()
def healthz(deep: bool = False) -> Dict[str, Any]:
    """Lightweight health/status for the MCP server and provider."""
    status = "ok"
    provider_ok = True
    latency_ms = None
    if deep:
        t0 = _t.perf_counter()
        provider_ok = bool(provider.ping(timeout=1.0))
        latency_ms = int(1000*(_t.perf_counter()-t0))
        if not provider_ok:
            status = "degraded"
    return {
        "status": status,
        "provider": _provider_name,
        "deep": deep,
        "provider_ok": provider_ok,
        "latency_ms": latency_ms,
    }

@mcp.tool()
def configz() -> Dict[str, Any]:
    """Return effective provider/config (secrets redacted)."""
    effective = dict(cfg)
    if "rapidapi_key" in effective:
        effective["rapidapi_key"] = "****"
    return {"provider": _provider_name, "config": effective}

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "http")  # http|stdio|sse
    try:
        mcp.run(transport=transport, host="127.0.0.1", port=8000, path="/mcp")
    except TypeError:
        if transport == "sse":
            mcp.run(transport="sse", mount_path="/mcp")
        elif transport == "http":
            mcp.run(transport="streamable-http")
        else:
            mcp.run(transport="stdio")
