from __future__ import annotations
from typing import Any, Dict, List, Optional
import httpx

class RapidProvider:
    """
    Licensed-provider stub using RapidAPI for Yahoo Finance.
    NOTE: This is a placeholder: search/quote/history/options_chain raise NotImplementedError
    until endpoints are configured. Keeps the server bootable with provider="rapidapi".
    """

    def __init__(self, api_key: str, host: str, timeout: float = 8.0) -> None:
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

    # Fill these with concrete endpoints when you’re ready.
    def search(self, query: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("RapidAPI search not yet implemented")

    def quote(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("RapidAPI quote not yet implemented")

    def history(
        self, symbol: str, start: Optional[str], end: Optional[str], interval: str, adjust: bool
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("RapidAPI history not yet implemented")

    def options_chain(self, symbol: str, expiry: Optional[str]) -> Dict[str, Any]:
        raise NotImplementedError("RapidAPI options_chain not yet implemented")

    def ping(self, timeout: float = 1.0) -> bool:
        # Basic connectivity check: we have a client and key
        try:
            self._client.get("https://httpbin.org/status/200", timeout=timeout)
            return True
        except Exception:
            return False

