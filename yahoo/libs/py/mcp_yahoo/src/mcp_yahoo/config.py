from __future__ import annotations
from typing import TypedDict
import os
import pathlib
import tomllib

class Settings(TypedDict, total=False):
    provider: str
    rapidapi_key: str
    rapidapi_host: str
    rapidapi_region: str

def load_config() -> Settings:
    """
    Load settings from TOML (MCP_YAHOO_CONFIG or ./mcp_yahoo.toml), then apply env overrides.
    Defaults to provider="yfinance".
    """
    s: Settings = {}
    # 1) TOML file
    cfg_path = os.getenv("MCP_YAHOO_CONFIG")
    if not cfg_path:
        # default to repo root ./mcp_yahoo.toml (works when server is launched from yahoo/)
        default = pathlib.Path(__file__).resolve().parents[4] / "mcp_yahoo.toml"
        if default.is_file():
            cfg_path = str(default)
    if cfg_path:
        p = pathlib.Path(cfg_path)
        if p.is_file():
            with p.open("rb") as f:
                data = tomllib.load(f)
            block = data.get("mcp_yahoo", data) if isinstance(data, dict) else {}
            if isinstance(block, dict):
                # normalize keys to underscores
                for k, v in block.items():
                    s[k.replace("-", "_")] = v

    # 2) defaults
    s["provider"] = (s.get("provider") or "yfinance").lower()

    # 3) env overrides
    prov = os.getenv("PROVIDER")
    if prov:
        s["provider"] = prov.lower()
    key = os.getenv("RAPIDAPI_KEY") or s.get("rapidapi_key", "")
    if key:
        s["rapidapi_key"] = key
    host = os.getenv("RAPIDAPI_HOST") or s.get("rapidapi_host") or "apidojo-yahoo-finance-v1.p.rapidapi.com"
    s["rapidapi_host"] = host

    # 4) region (default US)
    region = os.getenv("RAPIDAPI_REGION") or s.get("rapidapi_region") or "US"
    s["rapidapi_region"] = region

    return s
