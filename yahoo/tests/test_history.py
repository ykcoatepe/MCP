import os
import pytest
import datetime as dt
from mcp_yahoo.providers.yf import YFProvider

RUN = os.getenv("RUN_NETWORK_TESTS") == "1"

@pytest.mark.skipif(not RUN, reason="set RUN_NETWORK_TESTS=1 to run")
def test_history_basic():
    p = YFProvider()
    end = dt.date.today()
    start = end - dt.timedelta(days=20)
    bars = p.history("MSFT", start=str(start), end=str(end), interval="1d", adjust=True)
    assert isinstance(bars, list) and len(bars) >= 5
    # monotonic timestamps
    times = [b["time"] for b in bars]
    assert times == sorted(times)
    # sample fields present
    sample = bars[-1]
    for k in ("open","high","low","close","volume"):
        assert k in sample
