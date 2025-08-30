import os, pytest
from mcp_yahoo.providers.stub import StubProvider


def test_search_basic():
    p = StubProvider()
    items = p.search("AAP")
    assert any(it["symbol"] == "AAPL" for it in items)


def test_fetch_known():
    p = StubProvider()
    q = p.quote("MSFT")
    assert q["symbol"] == "MSFT" and isinstance(q["price"], (int, float))

