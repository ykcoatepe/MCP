import os, pytest
from mcp_yahoo.providers.yf import YFProvider

RUN = os.getenv("RUN_NETWORK_TESTS") == "1"

@pytest.mark.skipif(not RUN, reason="set RUN_NETWORK_TESTS=1 to run")
def test_quote_cached_briefly():
    p = YFProvider()
    q1 = p.quote("AAPL")
    q2 = p.quote("AAPL")
    # Within TTL, should be identical dicts (ts captured at first call)
    assert q1 == q2

