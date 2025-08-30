import importlib

def test_default_provider_is_yfinance(monkeypatch):
    # Ensure no env overrides
    for k in ("PROVIDER","RAPIDAPI_KEY","RAPIDAPI_HOST","MCP_YAHOO_CONFIG"):
        monkeypatch.delenv(k, raising=False)
    # Reload server to re-evaluate provider selection
    m = importlib.import_module("mcp_yahoo.server")
    assert m._provider_name == "yfinance"

def test_switch_to_rapidapi_requires_key(monkeypatch):
    monkeypatch.setenv("PROVIDER", "rapidapi")
    # no key → will fall back to yfinance
    m = importlib.reload(importlib.import_module("mcp_yahoo.server"))
    assert m._provider_name in ("rapidapi","yfinance")
    if m._provider_name == "rapidapi":
        # If RapidProvider import succeeded without key, it should have raised; so we expect yfinance
        assert False, "rapidapi selected without RAPIDAPI_KEY"
