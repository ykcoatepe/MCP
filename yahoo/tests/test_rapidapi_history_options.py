import os
import pytest
from mcp_yahoo.providers.rapid import RapidProvider

RUN = os.getenv("RUN_RAPIDAPI_TESTS") == "1"
KEY = os.getenv("RAPIDAPI_KEY", "")
HOST = os.getenv("RAPIDAPI_HOST", "apidojo-yahoo-finance-v1.p.rapidapi.com")
REGION = os.getenv("RAPIDAPI_REGION", "US")


@pytest.mark.skipif(not RUN, reason="set RUN_RAPIDAPI_TESTS=1 to run")
def test_rapidapi_history_and_options():
    assert KEY, "RAPIDAPI_KEY required"
    p = RapidProvider(api_key=KEY, host=HOST, region=REGION)
    bars = p.history("AAPL", start=None, end=None, interval="1d", adjust=True)
    assert isinstance(bars, list) and len(bars) > 0 and {"time", "open", "high", "low", "close", "volume"}.issubset(bars[-1].keys())
    chain = p.options_chain("AAPL", expiry=None)
    assert isinstance(chain.get("expiries"), list) and chain["expiries"], "no expiries"
    assert chain["selectedExpiry"] in chain["expiries"]
    # allow empty calls/puts (edge dates), but shape must be present
    assert "calls" in chain and "puts" in chain

