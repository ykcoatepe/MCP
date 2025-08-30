#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import json
from typing import Any, Dict, List, Optional

import anyio
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
import mcp.types as types

URL = "http://127.0.0.1:8000/mcp"


def get_structured(result: types.CallToolResult) -> Any:
    if result.structuredContent is not None:
        return result.structuredContent
    # fallback: parse first text block if present
    for block in result.content:
        if isinstance(block, dict) and block.get("type") == "text":
            try:
                return json.loads(block.get("text", ""))
            except Exception:
                return block.get("text")
    return None


async def run_tests() -> int:
    failures: List[str] = []

    async with sse_client(URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            async def call(name: str, args: Dict[str, Any] | None = None) -> Any:
                res = await session.send_request(
                    types.ClientRequest(
                        types.CallToolRequest(
                            method="tools/call",
                            params=types.CallToolRequestParams(name=name, arguments=args or {}),
                        )
                    ),
                    types.CallToolResult,
                )
                return get_structured(res)

            # 1. healthz(deep=true)
            try:
                h = await call("healthz", {"deep": True})
                ok = (
                    isinstance(h, dict)
                    and h.get("status") == "ok"
                    and isinstance(h.get("provider_ok"), bool)
                    and h.get("provider_ok") is True
                    and (h.get("latency_ms") is None or isinstance(h.get("latency_ms"), int))
                    and isinstance(h.get("provider"), str)
                )
                print(f"1 healthz: {'PASS' if ok else 'FAIL'}")
                if not ok:
                    failures.append("healthz")
            except Exception as e:
                print(f"1 healthz: FAIL ({e})")
                failures.append("healthz")

            # 2. configz()
            try:
                c = await call("configz")
                ok = isinstance(c, dict) and c.get("provider") in {"yfinance", "rapidapi"}
                key_redacted = True
                cfg = c.get("config") if isinstance(c, dict) else None
                if isinstance(cfg, dict) and "rapidapi_key" in cfg:
                    key_redacted = cfg.get("rapidapi_key") == "****"
                ok = ok and key_redacted
                print(f"2 configz: {'PASS' if ok else 'FAIL'}")
                if not ok:
                    failures.append("configz")
            except Exception as e:
                print(f"2 configz: FAIL ({e})")
                failures.append("configz")

            # 3. search(query="AAPL")
            try:
                s = await call("search", {"query": "AAPL"})
                items = (s or {}).get("items") if isinstance(s, dict) else None
                ok = isinstance(items, list) and any((isinstance(it, dict) and it.get("symbol") == "AAPL") for it in items)
                print(f"3 search: {'PASS' if ok else 'FAIL'}")
                if not ok:
                    failures.append("search")
            except Exception as e:
                print(f"3 search: FAIL ({e})")
                failures.append("search")

            # 4. fetch(id="AAPL")
            try:
                f = await call("fetch", {"id": "AAPL"})
                ok = (
                    isinstance(f, dict)
                    and f.get("symbol") == "AAPL"
                    and "currency" in f
                    and (isinstance(f.get("price"), (int, float)) or f.get("price") is None)
                )
                print(f"4 fetch: {'PASS' if ok else 'FAIL'}")
                if not ok:
                    failures.append("fetch")
            except Exception as e:
                print(f"4 fetch: FAIL ({e})")
                failures.append("fetch")

            # 5. get_quote(symbol="MSFT")
            try:
                q = await call("get_quote", {"symbol": "MSFT"})
                ok = (
                    isinstance(q, dict)
                    and q.get("symbol") == "MSFT"
                    and all(k in q for k in ["price", "open", "dayHigh", "dayLow", "previousClose"])
                )
                print(f"5 get_quote: {'PASS' if ok else 'FAIL'}")
                if not ok:
                    failures.append("get_quote")
            except Exception as e:
                print(f"5 get_quote: FAIL ({e})")
                failures.append("get_quote")

            # 6. get_history(symbol="AAPL", interval="1d")
            try:
                h = await call("get_history", {"symbol": "AAPL", "interval": "1d"})
                bars = (h or {}).get("bars") if isinstance(h, dict) else None
                ok = isinstance(bars, list) and len(bars) >= 5
                if ok:
                    first = bars[0]
                    ok = all(k in first for k in ["time", "open", "high", "low", "close", "volume"])
                print(f"6 get_history: {'PASS' if ok else 'FAIL'}")
                if not ok:
                    failures.append("get_history")
            except Exception as e:
                print(f"6 get_history: FAIL ({e})")
                failures.append("get_history")

            # 7. get_options_chain(symbol="AAPL")
            try:
                oc = await call("get_options_chain", {"symbol": "AAPL"})
                expiries = (oc or {}).get("expiries") if isinstance(oc, dict) else None
                selected = (oc or {}).get("selectedExpiry") if isinstance(oc, dict) else None
                calls = (oc or {}).get("calls") if isinstance(oc, dict) else None
                puts = (oc or {}).get("puts") if isinstance(oc, dict) else None
                ok = (
                    isinstance(expiries, list)
                    and len(expiries) > 0
                    and selected in expiries
                    and ((isinstance(calls, list) and len(calls) > 0) or (isinstance(puts, list) and len(puts) > 0))
                )
                if ok:
                    rows = calls if (isinstance(calls, list) and len(calls) > 0) else puts
                    row0 = rows[0] if rows else {}
                    ok = isinstance(row0, dict) and "contractSymbol" in row0 and "strike" in row0
                print(f"7 get_options_chain: {'PASS' if ok else 'FAIL'}")
                if not ok:
                    failures.append("get_options_chain")
            except Exception as e:
                print(f"7 get_options_chain: FAIL ({e})")
                failures.append("get_options_chain")

    if failures:
        print("Summary: FAILED: " + ", ".join(failures))
        return 1
    else:
        print("Summary: ALL PASS")
        return 0


if __name__ == "__main__":
    anyio.run(run_tests)
