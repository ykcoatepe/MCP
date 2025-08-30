import os, pytest
from mcp_yahoo.providers.yf import YFProvider

RUN = os.getenv("RUN_NETWORK_TESTS") == "1"

@pytest.mark.skipif(not RUN, reason="set RUN_NETWORK_TESTS=1 to run")
def test_search_and_quote():
    p = YFProvider()
    items = p.search("AAPL")
    assert items and any(it["symbol"] == "AAPL" for it in items)
    q = p.quote("AAPL")
    assert q["symbol"] == "AAPL"
    assert q["price"] is None or q["price"] > 0

