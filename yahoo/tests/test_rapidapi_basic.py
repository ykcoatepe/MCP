import os
import pytest
from mcp_yahoo.providers.rapid import RapidProvider

RUN = os.getenv("RUN_RAPIDAPI_TESTS") == "1"
KEY = os.getenv("RAPIDAPI_KEY", "")
HOST = os.getenv("RAPIDAPI_HOST", "apidojo-yahoo-finance-v1.p.rapidapi.com")
REGION = os.getenv("RAPIDAPI_REGION", "US")

@pytest.mark.skipif(not RUN, reason="set RUN_RAPIDAPI_TESTS=1 to run")
def test_rapidapi_search_and_quote():
    assert KEY, "RAPIDAPI_KEY required"
    p = RapidProvider(api_key=KEY, host=HOST, region=REGION)
    items = p.search("AAPL")
    assert items and any(it["symbol"] == "AAPL" for it in items)
    q = p.quote("AAPL")
    assert q["symbol"] == "AAPL"
    # price may be None off-hours, but usually numeric
    assert q["price"] is None or isinstance(q["price"], (int,float))
