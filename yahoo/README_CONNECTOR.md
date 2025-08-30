# ChatGPT Desktop – Custom Connector (MCP)

This server can be exposed over HTTP (MCP) on **http://127.0.0.1:8000/mcp**.

## Run (HTTP)
```bash
make -C yahoo run-http
# or:
yahoo/scripts/mcp-yahoo-http.sh

If port 8000 is busy:

yahoo/scripts/diag-8000.sh   # see which process holds it
# then stop/kill that process and run again

Add to ChatGPT Desktop
	1.	Open ChatGPT → Settings → Connectors.
	2.	Create a Custom Connector, set the URL to your server.
	•	If Desktop cannot reach localhost, expose it via a tunnel (Cloudflare/Tailscale/ngrok) mapped to http://127.0.0.1:8000.
	3.	The server implements the required MCP tools:
	•	search(query) and fetch(id) (plus get_quote, get_history, get_options_chain, healthz, configz).

Quick health check

make -C yahoo health
# or call the MCP tool: healthz(deep=true)

Notes
	•	Provider defaults to yfinance. Switch via env/TOML (see mcp_yahoo.toml and configz()).
	•	For production/legal use, prefer a licensed provider and wire the RapidAPI adapter.
```

⸻

	5.	(Optional) Extend sanity script with HTTP runner existence check
Append this near the end of scripts/sanity_task12.sh before the final echo:

⸻

[ -x “yahoo/scripts/mcp-yahoo-http.sh” ] && echo “PASS  http runner present” || echo “FAIL  http runner missing”
	6.	Run smoke checks
Commands:

	•	make -C yahoo run-http   # should start (if :8000 free); Ctrl+C to stop
	•	yahoo/scripts/diag-8000.sh
	•	make -C yahoo health

**Acceptance**
- `yahoo/scripts/mcp-yahoo-http.sh` starts HTTP mode on 8000 (when free).
- `yahoo/scripts/diag-8000.sh` lists the blocker if 8000 is busy.
- `make -C yahoo health` prints a small dict from `healthz`.
- `yahoo/README_CONNECTOR.md` is present with clear steps.

## API Contracts
Responses conform to Pydantic models (see `mcp_yahoo/schemas.py`). Errors follow:
```json
{"error":{"code":"STRING","message":"HUMAN_READABLE"}}
```

Available tools: search, fetch, get_quote, get_history, get_options_chain, healthz, configz, metricsz.
