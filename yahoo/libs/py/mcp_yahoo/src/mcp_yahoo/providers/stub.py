from __future__ import annotations
from typing import Any, Dict, List


class StubProvider:
    """In-memory fake data so MCP shape can be validated by ChatGPT connectors."""
    _universe = {
        "AAPL": {"symbol": "AAPL", "price": 123.45, "currency": "USD"},
        "MSFT": {"symbol": "MSFT", "price": 345.67, "currency": "USD"},
        "SPY":  {"symbol": "SPY",  "price": 500.01, "currency": "USD"},
    }

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = (query or "").strip().upper()
        if not q:
            return []
        items: List[Dict[str, Any]] = []
        for sym, row in self._universe.items():
            if q in sym:
                items.append({"id": sym, "symbol": sym, "name": sym, "exchange": "STUB", "type": "EQUITY"})
        return items

    def quote(self, symbol: str) -> Dict[str, Any]:
        sym = (symbol or "").strip().upper()
        row = self._universe.get(sym)
        if not row:
            raise ValueError(f"Unknown symbol: {symbol}")
        return {
            "symbol": row["symbol"],
            "price": row["price"],
            "currency": row["currency"],
            "open": None, "dayHigh": None, "dayLow": None, "previousClose": None,
            "ts": "1970-01-01T00:00:00Z",
            "source": "stub",
        }

