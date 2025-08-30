from __future__ import annotations
import os
from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP
from mcp_yahoo.providers.yf import YFProvider

mcp = FastMCP("yahoo-finance-mcp")
provider = YFProvider()

@mcp.tool()
def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
    return {"items": provider.search(query)}

@mcp.tool()
def fetch(id: str) -> Dict[str, Any]:
    return provider.quote(id)

@mcp.tool()
def get_quote(symbol: str) -> Dict[str, Any]:
    return provider.quote(symbol)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "http")  # http|stdio|sse
    try:
        mcp.run(transport=transport, host="127.0.0.1", port=8000, path="/mcp")
    except TypeError:
        if transport == "sse":
            mcp.run(transport="sse", mount_path="/mcp")
        elif transport == "http":
            mcp.run(transport="streamable-http")
        else:
            mcp.run(transport="stdio")
