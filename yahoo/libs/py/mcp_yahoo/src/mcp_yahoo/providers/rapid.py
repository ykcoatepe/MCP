from __future__ import annotations
from typing import Any, Dict, List, Optional
import time
import random
import datetime as dt
import httpx
from cachetools import TTLCache
from mcp_yahoo.cache import cache_search, cache_quote, cache_hist, cache_opts


def _to_iso(unix_ts: int) -> str:
    try:
        return dt.datetime.utcfromtimestamp(int(unix_ts)).isoformat() + "Z"
    except Exception:
        return str(unix_ts)


class RapidProvider:
    """
    Licensed Yahoo Finance via RapidAPI (Apidojo).
    Implements:
      - search:  /auto-complete
      - quote:   /market/v2/get-quotes  (fallback: /stock/v2/get-summary)
      - history: /stock/v3/get-historical-data
      - options: /options/v2/get-options
    """

    def __init__(self, api_key: str, host: str, timeout: float = 8.0, region: str = "US") -> None:
        if not api_key:
            raise ValueError("RAPIDAPI_KEY is required for provider='rapidapi'")
        if not host:
            raise ValueError("RAPIDAPI_HOST is required for provider='rapidapi'")
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": host,
                "User-Agent": "mcp-yahoo/0.1 (+LLM)",
            },
        )
        self._region = region
        self._search_cache: TTLCache = cache_search()
        self._quote_cache: TTLCache = cache_quote()
        self._hist_cache: TTLCache = cache_hist()
        self._opt_cache: TTLCache = cache_opts()

    # --- retry helper ---
    def _retry(self, fn, attempts: int = 3, base_ms: int = 150, cap_ms: int = 1200):
        last = None
        for i in range(attempts):
            try:
                return fn()
            except Exception as e:
                last = e
                if i == attempts - 1:
                    break
                sleep_ms = min(cap_ms, base_ms * (2 ** i)) + random.randint(0, 100)
                time.sleep(sleep_ms / 1000.0)
        raise last

    # --- SEARCH ---
    def search(self, query: str) -> List[Dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []
        key = q.lower()
        hit = self._search_cache.get(key)
        if hit is not None:
            return hit

        def _call():
            r = self._client.get(
                "https://apidojo-yahoo-finance-v1.p.rapidapi.com/auto-complete",
                params={"q": q, "region": self._region},
            )
            r.raise_for_status()
            return r.json()

        data = self._retry(_call)
        items: List[Dict[str, Any]] = []
        for row in data.get("quotes", []):
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
        self._search_cache[key] = items
        return items

    # --- QUOTE ---
    def quote(self, symbol: str) -> Dict[str, Any]:
        sym = (symbol or "").strip().upper()
        if not sym:
            raise ValueError("symbol is required")
        hit = self._quote_cache.get(sym)
        if hit is not None:
            return hit

        def _getq():
            r = self._client.get(
                "https://apidojo-yahoo-finance-v1.p.rapidapi.com/market/v2/get-quotes",
                params={"symbols": sym, "region": self._region},
            )
            r.raise_for_status()
            return r.json()

        data = self._retry(_getq)
        result = (data or {}).get("quoteResponse", {}).get("result", []) or []

        if result:
            q = result[0]
            price = q.get("regularMarketPrice")
            currency = q.get("currency")
            open_ = q.get("regularMarketOpen")
            day_high = q.get("regularMarketDayHigh")
            day_low = q.get("regularMarketDayLow")
            prev_close = q.get("regularMarketPreviousClose")
        else:
            def _sum():
                r = self._client.get(
                    "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-summary",
                    params={"symbol": sym, "region": self._region},
                )
                r.raise_for_status()
                return r.json()

            sdata = self._retry(_sum)
            price = (sdata.get("price") or {}).get("regularMarketPrice", {}).get("raw")
            currency = (sdata.get("price") or {}).get("currency")
            open_ = (sdata.get("price") or {}).get("regularMarketOpen", {}).get("raw")
            day_high = (sdata.get("price") or {}).get("regularMarketDayHigh", {}).get("raw")
            day_low = (sdata.get("price") or {}).get("regularMarketDayLow", {}).get("raw")
            prev_close = (sdata.get("price") or {}).get("regularMarketPreviousClose", {}).get("raw")

        out = {
            "symbol": sym,
            "price": float(price) if isinstance(price, (int, float)) else price,
            "currency": currency,
            "open": float(open_) if isinstance(open_, (int, float)) else open_,
            "dayHigh": float(day_high) if isinstance(day_high, (int, float)) else day_high,
            "dayLow": float(day_low) if isinstance(day_low, (int, float)) else day_low,
            "previousClose": float(prev_close) if isinstance(prev_close, (int, float)) else prev_close,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": "Yahoo Finance via RapidAPI",
        }
        self._quote_cache[sym] = out
        return out

    # --- HISTORY ---
    def history(
        self,
        symbol: str,
        start: Optional[str],
        end: Optional[str],
        interval: str,
        adjust: bool,
    ) -> List[Dict[str, Any]]:
        sym = (symbol or "").strip().upper()
        if not sym:
            raise ValueError("symbol is required")
        key = "|".join([sym, str(start or ""), str(end or ""), interval, "A" if adjust else "U"])
        hit = self._hist_cache.get(key)
        if hit is not None:
            return hit

        # RapidAPI endpoint typically returns {"prices":[{"date":unix,"open":...,"adjclose":...},...]}
        def _call():
            r = self._client.get(
                "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v3/get-historical-data",
                params={"symbol": sym, "region": self._region},
            )
            r.raise_for_status()
            return r.json()

        data = self._retry(_call)
        prices = data.get("prices") or []
        out: List[Dict[str, Any]] = []
        for row in prices:
            if "type" in row:  # skip events like DIVIDEND/SPLIT
                continue
            ts = _to_iso(row.get("date"))
            rec = {
                "time": ts,
                "open": float(row.get("open")) if row.get("open") is not None else None,
                "high": float(row.get("high")) if row.get("high") is not None else None,
                "low": float(row.get("low")) if row.get("low") is not None else None,
                "close": float(row.get("close")) if row.get("close") is not None else None,
                "volume": int(row.get("volume") or 0),
            }
            adj = row.get("adjclose")
            if adj is not None:
                try:
                    rec["adjClose"] = float(adj)
                except Exception:
                    pass
            # filter None-valued OHLC rows
            if rec["open"] is not None and rec["close"] is not None:
                out.append(rec)
        out.sort(key=lambda r: r["time"])
        self._hist_cache[key] = out
        return out

    # --- OPTIONS ---
    def options_chain(self, symbol: str, expiry: Optional[str]) -> Dict[str, Any]:
        sym = (symbol or "").strip().upper()
        if not sym:
            raise ValueError("symbol is required")

        # first call to get expiries (unix list)
        def _get0():
            r = self._client.get(
                "https://apidojo-yahoo-finance-v1.p.rapidapi.com/options/v2/get-options",
                params={"symbol": sym, "region": self._region},
            )
            r.raise_for_status()
            return r.json()

        root = self._retry(_get0)
        result = (root.get("optionChain") or {}).get("result") or []
        if not result:
            return {"expiries": [], "selectedExpiry": None, "calls": [], "puts": []}
        exp_unix = result[0].get("expirationDates") or []
        expiries = [dt.datetime.utcfromtimestamp(int(x)).strftime("%Y-%m-%d") for x in exp_unix]

        # if a specific expiry requested, map YYYY-MM-DD -> unix
        selected = None
        date_param = None
        if expiry:
            selected = expiry
            try:
                idx = expiries.index(expiry)
                date_param = int(exp_unix[idx])
            except Exception:
                raise ValueError(f"requested expiry {expiry!r} not in available expiries")
        else:
            selected = expiries[0]
            date_param = int(exp_unix[0]) if exp_unix else None

        cache_key = f"{sym}|{selected}"
        hit = self._opt_cache.get(cache_key)
        if hit is not None:
            return hit

        def _get_for_date():
            params = {"symbol": sym, "region": self._region}
            if date_param is not None:
                params["date"] = date_param
            r = self._client.get(
                "https://apidojo-yahoo-finance-v1.p.rapidapi.com/options/v2/get-options",
                params=params,
            )
            r.raise_for_status()
            return r.json()

        data = self._retry(_get_for_date)

        def df_to_list(arr) -> List[Dict[str, Any]]:
            cols = [
                "contractSymbol",
                "strike",
                "lastPrice",
                "bid",
                "ask",
                "volume",
                "openInterest",
                "impliedVolatility",
                "inTheMoney",
            ]
            out: List[Dict[str, Any]] = []
            for row in arr or []:
                item: Dict[str, Any] = {}
                for k in cols:
                    v = (row or {}).get(k)
                    if k == "contractSymbol" and v:
                        item[k] = str(v)
                        continue
                    if k == "inTheMoney":
                        item[k] = bool(v)
                        continue
                    if v is None:
                        continue
                    try:
                        item[k] = float(v)
                    except Exception:
                        pass
                if "contractSymbol" in item and "strike" in item:
                    out.append(item)
            return out

        opts = ((data.get("optionChain") or {}).get("result") or [{}])[0].get("options") or []
        calls: List[Dict[str, Any]] = []
        puts: List[Dict[str, Any]] = []
        if opts:
            block = opts[0]
            calls = df_to_list(block.get("calls"))
            puts = df_to_list(block.get("puts"))

        out = {"expiries": expiries, "selectedExpiry": selected, "calls": calls, "puts": puts}
        self._opt_cache[cache_key] = out
        return out

    # --- ping ---
    def ping(self, timeout: float = 1.0) -> bool:
        try:
            r = self._client.get(
                "https://apidojo-yahoo-finance-v1.p.rapidapi.com/auto-complete",
                params={"q": "AAPL", "region": self._region},
                timeout=timeout,
            )
            return r.status_code == 200
        except Exception:
            return False
