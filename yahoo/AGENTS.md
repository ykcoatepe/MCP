# Repository Guidelines

## Project Structure & Module Organization
- `yahoo/`: Yahoo Finance MCP server (Node.js, ESM).
  - `index.js`: MCP server entry; exposes tools over stdio.
  - `package.json`: Scripts and deps (`@modelcontextprotocol/sdk`, `yahoo-finance2`, `zod`).
  - `test_mcp_client.js`: Local stdio sanity client for handshake.
- Workspace root: No monorepo tooling. Add new MCP servers as sibling folders.

## Build, Test, and Development Commands
- Install deps (inside `yahoo/`): `npm ci` or `npm install`.
- Run server (stdio): `node yahoo/index.js`.
- Package script: `npm -C yahoo start` (runs `node index.js`).
- Handshake test (no network calls): `node yahoo/test_mcp_client.js`.
- Codex CLI wiring (read-only note): `~/.codex/config.toml` has `[mcp_servers.yahoo]` → `node /Users/yordamkocatepe/mcp/yahoo/index.js`.

## Coding Style & Naming Conventions
- Language: modern Node (≥18), ES Modules, 2‑space indentation.
- Tool names: `camelCase` (e.g., `getQuote`, `getOptions`, `getChart`).
- Validation: prefer `zod` with raw shape objects for input schemas.
- Avoid inline logging; server uses stdio transport and should remain silent on stdout/stderr.

## Testing Guidelines
- Framework: not configured. Use the provided `test_mcp_client.js` for quick checks.
- Add tests under `yahoo/__tests__/` if expanding; name files `*.test.js`.
- Keep tests offline by default; mock `yahoo-finance2` for deterministic runs.

## Commit & Pull Request Guidelines
- Commits: use Conventional Commits.
  - Examples: `feat(yahoo): add getNews tool`, `fix(yahoo): handle invalid symbols`.
- PRs: include a brief summary, screenshots or logs when relevant, and list of manual test steps (e.g., handshake, a sample tool call).

## Security & Configuration Tips
- Do not print secrets; this server runs via stdio under Codex.
- Network access is only required during tool calls; startup must succeed offline.
- Configuration for Codex lives at `~/.codex/config.toml`. Avoid hard‑coding user paths in code.

## Architecture Overview
- Transport: `StdioServerTransport` (MCP).
- Server: `McpServer` with `tool(...)` APIs; prefer zod raw shapes so input schemas surface to clients.

## Yahoo Tools
- `getQuote`: Normalized quote for a symbol. Attempts Yahoo `quote` first; on failure, falls back to synthesizing from `chart?range=1d&interval=1m`.
  - Input: `{ symbol: string }`
  - Output JSON fields (consistent across paths):
    - `symbol`, `name`, `exchange`, `currency`
    - `price`, `high`, `low`, `previousClose`, `volume`
    - `asOfEpoch` (seconds), `asOfISO` (ISO string)
    - `marketState`, `source` (`quote` or `chart:<range>@<interval>`)
- `getOptions`: Option chain for a symbol; optional `date` filter.
- `getChart`: Historical bars; accepts `range`, `interval`, `period1`, `period2`, `events`, `includePrePost`.

### Error Handling
- Differentiates likely network failures in error messages when both quote and chart fail.
- Uses `McpError(ErrorCode.InternalError, message)` to ensure clients get structured failures.
# Repository Guidelines

## Project Structure & Module Organization
- `yahoo/`: Yahoo Finance MCP server (Node.js ESM).
  - `index.js`: MCP stdio server; tools `getQuote`, `getOptions`, `getChart`.
  - `package.json`: Scripts and dependencies (`@modelcontextprotocol/sdk`, `yahoo-finance2`, `zod`).
  - `test_mcp_client.js`: Offline handshake/schema sanity check.
  - `test_fetch_quote.js`: Live `getQuote` call (needs network).
- Add additional MCP servers as sibling folders (e.g., `alpaca/`).

## Build, Test, and Development Commands
- Install: `npm ci -C yahoo` (or `npm install -C yahoo`).
- Run server: `node yahoo/index.js` (or `npm -C yahoo start`).
- List tools (offline): `node yahoo/test_mcp_client.js`.
- Live quote (network): `node yahoo/test_fetch_quote.js` (defaults to `TSLA`).

## Coding Style & Naming Conventions
- Runtime: Node.js 18+; ES Modules; 2‑space indentation.
- Tools: camelCase names; descriptive `description` strings.
- Validation: `zod` with raw shapes so JSON schemas surface to clients.
- I/O: Keep stdout/stderr silent (stdio transport); no ad‑hoc logging.

## Testing Guidelines
- No framework enforced. Prefer offline tests by mocking `yahoo-finance2`.
- If adding a framework, place tests under `yahoo/__tests__/` and name `*.test.js`.
- Keep tests deterministic; avoid network in CI.

## Commit & Pull Request Guidelines
- Commits: Conventional Commits (e.g., `feat(yahoo): add quote fallback`, `fix(yahoo): normalize timestamps`).
- PRs: short description, linked issues, manual steps (handshake + sample tool call), and relevant logs/screenshots.

## Security & Configuration Tips
- Do not commit secrets. Network errors are surfaced via `McpError` with clear messages.
- Codex CLI wiring (example): in `~/.codex/config.toml`
  ```toml
  [mcp_servers.yahoo]
  command = "node"
  args = ["/absolute/path/to/repo/yahoo/index.js"]
  ```

## Architecture Overview
- Transport: `StdioServerTransport`; Server: `McpServer`.
- Responses: tools return `text` content containing a JSON string (broad client compatibility). Update to `json` content if your client supports it.
- `getQuote`: Tries Yahoo `quote`; on failure, synthesizes from `chart?range=1d&interval=1m`. Normalized fields: `symbol`, `name`, `exchange`, `currency`, `price`, `high`, `low`, `previousClose`, `volume`, `asOfEpoch`, `asOfISO`, `marketState`, `source`.
