from __future__ import annotations
import os
from mcp_yahoo import server  # importing runs the same module


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    path = os.getenv("MCP_PATH", "/mcp")
    server.mcp.run(transport=transport, host=host, port=port, path=path)


if __name__ == "__main__":
    main()

