import os
import pytest
from mcp_yahoo.providers.yf import YFProvider

RUN = os.getenv("RUN_NETWORK_TESTS") == "1"

@pytest.mark.skipif(not RUN, reason="set RUN_NETWORK_TESTS=1 to run")
def test_options_chain_has_expiries_and_some_rows():
    p = YFProvider()
    data = p.options_chain("AAPL")
    assert isinstance(data.get("expiries"), list) and len(data["expiries"]) > 0
    assert data["selectedExpiry"] in data["expiries"]
    # calls/puts may be empty on illiquid dates, but usually have rows
    assert "calls" in data and "puts" in data
    if data["calls"]:
        row = data["calls"][0]
        assert "contractSymbol" in row and "strike" in row
