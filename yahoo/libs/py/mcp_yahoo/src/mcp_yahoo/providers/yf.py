from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
import httpx
import yfinance as yf

_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"


class YFProvider:
    """
    Yahoo-style data via yfinance + Yahoo search JSON.
    For research/educational use. Swap to a licensed provider for production.
    """

    def __init__(self, http_timeout: float = 8.0) -> None:
        self._client = httpx.Client(
            timeout=http_timeout,
            headers={"User-Agent": "mcp-yahoo/0.1 (+LLM)"},
        )

    # ---- search ----
    def search(self, query: str) -> List[Dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []
        r = self._client.get(_SEARCH_URL, params={"q": q, "quotesCount": 10, "newsCount": 0})
        r.raise_for_status()
        payload = r.json()
        items: List[Dict[str, Any]] = []
        for row in payload.get("quotes", []):
            sym = row.get("symbol")
            if not sym:
                continue
            items.append({
                "id": sym,
                "symbol": sym,
                "name": row.get("shortname") or row.get("longname") or sym,
                "exchange": row.get("exchDisp") or row.get("exchange"),
                "type": row.get("quoteType"),
            })
        return items

    # ---- quote ----
    def quote(self, symbol: str) -> Dict[str, Any]:
        sym = (symbol or "").strip().upper()
        if not sym:
            raise ValueError("symbol is required")
        t = yf.Ticker(sym)

        price = currency = open_ = day_high = day_low = prev_close = None
        try:
            fi = dict(getattr(t, "fast_info", {}))
            price = fi.get("last_price")
            currency = fi.get("currency")
            open_ = fi.get("open")
            day_high = fi.get("day_high")
            day_low = fi.get("day_low")
            prev_close = fi.get("previous_close")
        except Exception:
            pass

        # Fallback: last minute bar close if fast_info missing
        if price is None:
            df = t.history(period="1d", interval="1m", auto_adjust=False)
            if not df.empty:
                price = float(df["Close"].iloc[-1])
                if len(df) >= 2:
                    prev_close = float(df["Close"].iloc[-2])

        return {
            "symbol": sym,
            "price": price,
            "currency": currency,
            "open": open_,
            "dayHigh": day_high,
            "dayLow": day_low,
            "previousClose": prev_close,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": "Yahoo Finance via yfinance",
        }

