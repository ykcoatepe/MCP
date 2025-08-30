from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp_yahoo.providers.stub import StubProvider

mcp = FastMCP("yahoo-finance-mcp")
provider = StubProvider()


@mcp.tool()
def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """Return symbol matches for a free-text query."""
    return {"items": provider.search(query)}


@mcp.tool()
def fetch(id: str) -> Dict[str, Any]:
    """Hydrate a search result by id (symbol) into a quote-like payload."""
    return provider.quote(id)


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "http")  # http|stdio|sse
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    path = os.getenv("MCP_PATH", "/mcp")
    if transport == "http":
        mcp.run(transport="streamable-http")
    elif transport == "sse":
        mcp.run(transport="sse", mount_path=path)
    else:
        mcp.run(transport="stdio")
