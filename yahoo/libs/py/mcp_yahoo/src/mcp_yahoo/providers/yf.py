from __future__ import annotations
import time
import random, time as _time
from typing import Any, Dict, List, Optional
import httpx
import yfinance as yf
from mcp_yahoo.cache import cache_quote, cache_search, cache_hist, cache_opts

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
        self._search_cache = cache_search()
        self._quote_cache  = cache_quote()
        self._hist_cache   = cache_hist()
        self._opt_cache    = cache_opts()

    def _retry(self, fn, *, attempts: int = 3, base_ms: int = 150, cap_ms: int = 1200):
        last = None
        for i in range(attempts):
            try:
                return fn()
            except Exception as e:
                last = e
                if i == attempts - 1:
                    break
                sleep_ms = min(cap_ms, base_ms * (2 ** i)) + random.randint(0, 100)
                _time.sleep(sleep_ms / 1000.0)
        raise last

    # ---- search ----
    def search(self, query: str) -> List[Dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []
        key = q.lower()
        hit = self._search_cache.get(key)
        if hit is not None:
            return hit

        def _call():
            r = self._client.get(_SEARCH_URL, params={"q": q, "quotesCount": 10, "newsCount": 0})
            r.raise_for_status()
            return r.json()

        payload = self._retry(_call)
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
        self._search_cache[key] = items
        return items

    # ---- quote ----
    def quote(self, symbol: str) -> Dict[str, Any]:
        sym = (symbol or "").strip().upper()
        if not sym:
            raise ValueError("symbol is required")

        cached = self._quote_cache.get(sym)
        if cached is not None:
            return cached

        def _fast():
            t = yf.Ticker(sym)
            fi = dict(getattr(t, "fast_info", {}))
            return fi

        price = currency = open_ = day_high = day_low = prev_close = None
        try:
            fi = self._retry(_fast)
            price = fi.get("last_price")
            currency = fi.get("currency")
            open_ = fi.get("open")
            day_high = fi.get("day_high")
            day_low = fi.get("day_low")
            prev_close = fi.get("previous_close")
        except Exception:
            pass

        if price is None:
            def _hist_minute():
                t = yf.Ticker(sym)
                return t.history(period="1d", interval="1m", auto_adjust=False)
            df = self._retry(_hist_minute)
            if not df.empty:
                price = float(df["Close"].iloc[-1])
                if len(df) >= 2:
                    prev_close = float(df["Close"].iloc[-2])

        out = {
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
        self._quote_cache[sym] = out
        return out

    # ---- history ----
    def history(
        self,
        symbol: str,
        start: Optional[str] = None,   # "YYYY-MM-DD"
        end: Optional[str] = None,     # "YYYY-MM-DD"
        interval: str = "1d",          # e.g. "1m","5m","15m","1h","1d","1wk","1mo"
        adjust: bool = True,
    ) -> List[Dict[str, Any]]:
        sym = (symbol or "").strip().upper()
        if not sym:
            raise ValueError("symbol is required")

        allowed = {"1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"}
        if interval not in allowed:
            raise ValueError(f"unsupported interval: {interval}")

        key = "|".join([sym, str(start or ""), str(end or ""), interval, "A" if adjust else "U"])
        hit = self._hist_cache.get(key)
        if hit is not None:
            return hit

        def _dl():
            if start or end:
                return yf.download(sym, start=start, end=end, interval=interval, auto_adjust=adjust, progress=False)
            else:
                return yf.download(sym, period="1mo", interval=interval, auto_adjust=adjust, progress=False)

        try:
            df = self._retry(_dl)
        except Exception as e:
            raise RuntimeError(f"yfinance download failed: {e}") from e

        if df.empty:
            self._hist_cache[key] = []
            return []

        # If columns are MultiIndex (e.g., ('Open','MSFT')), select the symbol level
        try:
            import pandas as pd  # type: ignore
            if isinstance(df.columns, pd.MultiIndex):
                try:
                    df = df.xs(sym, axis=1, level=1)
                except Exception:
                    try:
                        df.columns = [c[-1] if isinstance(c, tuple) else c for c in df.columns]
                    except Exception:
                        pass
        except Exception:
            pass

        df = df.reset_index()
        out: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            ts = row.iloc[0]
            rec: Dict[str, Any] = {
                "time": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row.get("Volume", 0) or 0),
            }
            if "Adj Close" in df.columns:
                try:
                    rec["adjClose"] = float(row["Adj Close"])
                except Exception:
                    pass
            out.append(rec)
        self._hist_cache[key] = out
        return out

    # ---- options ----
    def options_chain(self, symbol: str, expiry: Optional[str] = None) -> Dict[str, Any]:
        sym = (symbol or "").strip().upper()
        if not sym:
            raise ValueError("symbol is required")

        t = yf.Ticker(sym)
        expiries = list(t.options or [])
        if not expiries:
            return {"expiries": [], "selectedExpiry": None, "calls": [], "puts": []}

        if expiry and expiry not in expiries:
            raise ValueError(f"requested expiry {expiry!r} not in available expiries")

        selected = expiry or expiries[0]
        cache_key = f"{sym}|{expiry or 'FIRST'}"
        hit = self._opt_cache.get(cache_key)
        if hit is not None:
            return hit
        try:
            chain = t.option_chain(selected)  # returns namedtuple(calls=DataFrame, puts=DataFrame)
        except Exception as e:
            raise RuntimeError(f"yfinance option_chain failed: {e}") from e

        def df_to_list(df) -> List[Dict[str, Any]]:
            # Keep a stable subset; some columns (greeks) can be NaN or missing depending on symbol/date.
            cols = [
                "contractSymbol", "strike", "lastPrice", "bid", "ask",
                "volume", "openInterest", "impliedVolatility", "inTheMoney"
            ]
            out: List[Dict[str, Any]] = []
            if df is None or getattr(df, "empty", True):
                return out
            for _, r in df.iterrows():
                item: Dict[str, Any] = {}
                for k in cols:
                    if k not in df.columns:
                        continue
                    v = r[k]
                    if k == "contractSymbol":
                        item[k] = str(v)
                    elif k == "inTheMoney":
                        item[k] = bool(v)
                    else:
                        # coerce numeric if possible; skip NaNs
                        try:
                            if v == v:
                                item[k] = float(v)
                        except Exception:
                            pass
                out.append(item)
            return out

        data = {
            "expiries": expiries,
            "selectedExpiry": selected,
            "calls": df_to_list(chain.calls),
            "puts": df_to_list(chain.puts),
        }
        self._opt_cache[cache_key] = data
        return data

    def ping(self, timeout: float = 1.0) -> bool:
        try:
            r = self._client.get(_SEARCH_URL, params={"q":"AAPL","quotesCount":1,"newsCount":0}, timeout=timeout)
            return r.status_code == 200
        except Exception:
            return False
