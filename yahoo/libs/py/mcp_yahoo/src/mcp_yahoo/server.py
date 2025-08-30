from __future__ import annotations
import os
import json
import sys
import time as _t
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp_yahoo.config import load_config
from mcp_yahoo.providers.yf import YFProvider
from mcp_yahoo.schemas import (
    Quote,
    HistoryResponse,
    OptionsChainResponse,
    HealthzResponse,
    ConfigzResponse,
    ErrorPayload,
)
from mcp_yahoo.metrics import inc, obs_latency, snapshot as metrics_snapshot
try:
    from mcp_yahoo.providers.rapid import RapidProvider  # optional
except Exception:
    RapidProvider = None  # type: ignore

mcp = FastMCP("yahoo-finance-mcp")
cfg = load_config()
_provider_name: str
if (cfg.get("provider") or "yfinance").lower() == "rapidapi" and RapidProvider and cfg.get("rapidapi_key"):
    provider = RapidProvider(
        api_key=cfg["rapidapi_key"],
        host=cfg.get("rapidapi_host", ""),
        region=cfg.get("rapidapi_region", "US"),
    )  # type: ignore
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
        ms = int(1000 * (_t.perf_counter() - t0))
        obs_latency("search", ms)
        inc("search.ok")
        jlog("tool_ok", tool="search", query=query, ms=ms)
        return {"items": items}
    except Exception as e:
        inc("search.err")
        jlog("tool_err", tool="search", query=query, error=str(e))
        return {"error": ErrorPayload(code="SEARCH_FAILED", message=str(e)).model_dump()}

@mcp.tool()
def fetch(id: str) -> Dict[str, Any]:
    t0 = _t.perf_counter()
    try:
        raw = provider.quote(id)
        out = Quote.model_validate(raw).model_dump()
        ms = int(1000 * (_t.perf_counter() - t0))
        obs_latency("fetch", ms)
        inc("fetch.ok")
        jlog("tool_ok", tool="fetch", id=id, ms=ms)
        return out
    except Exception as e:
        inc("fetch.err")
        jlog("tool_err", tool="fetch", id=id, error=str(e))
        return {"error": ErrorPayload(code="FETCH_FAILED", message=str(e)).model_dump()}

@mcp.tool()
def get_quote(symbol: str) -> Dict[str, Any]:
    t0 = _t.perf_counter()
    try:
        raw = provider.quote(symbol)
        out = Quote.model_validate(raw).model_dump()
        ms = int(1000 * (_t.perf_counter() - t0))
        obs_latency("get_quote", ms)
        inc("get_quote.ok")
        jlog("tool_ok", tool="get_quote", ms=ms, symbol=symbol)
        return out
    except Exception as e:
        inc("get_quote.err")
        jlog("tool_err", tool="get_quote", symbol=symbol, error=str(e))
        return {"error": ErrorPayload(code="QUOTE_FAILED", message=str(e)).model_dump()}

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
        raw = {
            "symbol": symbol.upper(),
            "interval": interval,
            "bars": provider.history(symbol, start, end, interval, adjust),
        }
        out = HistoryResponse.model_validate(raw).model_dump()
        ms = int(1000 * (_t.perf_counter() - t0))
        obs_latency("get_history", ms)
        inc("get_history.ok")
        jlog("tool_ok", tool="get_history", symbol=symbol, interval=interval, ms=ms)
        return out
    except Exception as e:
        inc("get_history.err")
        jlog("tool_err", tool="get_history", symbol=symbol, interval=interval, error=str(e))
        return {"error": ErrorPayload(code="HISTORY_FAILED", message=str(e)).model_dump()}

@mcp.tool()
def get_options_chain(symbol: str, expiry: Optional[str] = None) -> Dict[str, Any]:
    """Return option expiries and the calls/puts lists for the selected expiry."""
    t0 = _t.perf_counter()
    try:
        out = OptionsChainResponse.model_validate(provider.options_chain(symbol, expiry)).model_dump()
        ms = int(1000 * (_t.perf_counter() - t0))
        obs_latency("get_options_chain", ms)
        inc("get_options_chain.ok")
        jlog("tool_ok", tool="get_options_chain", symbol=symbol, expiry=expiry, ms=ms)
        return out
    except Exception as e:
        inc("get_options_chain.err")
        jlog("tool_err", tool="get_options_chain", symbol=symbol, expiry=expiry, error=str(e))
        return {"error": ErrorPayload(code="OPTIONS_FAILED", message=str(e)).model_dump()}

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
    out = HealthzResponse.model_validate({
        "status": status,
        "provider": (_provider_name if isinstance(_provider_name, str) else "unknown"),
        "deep": bool(deep),
        "provider_ok": provider_ok,
        "latency_ms": latency_ms,
    }).model_dump()
    inc("healthz.ok")
    return out

@mcp.tool()
def configz() -> Dict[str, Any]:
    """Return effective provider/config (secrets redacted)."""
    effective = dict(cfg)
    if "rapidapi_key" in effective:
        effective["rapidapi_key"] = "****"
    out = ConfigzResponse.model_validate({"provider": _provider_name, "config": effective}).model_dump()
    inc("configz.ok")
    return out

@mcp.tool()
def metricsz() -> Dict[str, Any]:
    """Return internal counters and latency snapshots."""
    inc("metricsz.ok")
    return metrics_snapshot()

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
