import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import yf from "yahoo-finance2";

const server = new McpServer(
  { name: "yahoo", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// Zod schemas
// Use raw shapes for tool registration so clients see JSON schemas.
const quoteInput = {
  symbol: z.string().min(1).describe("Ticker symbol, e.g., AAPL"),
};
const quoteSchema = z.object(quoteInput).passthrough();

const optionsInput = {
  symbol: z.string().min(1).describe("Ticker symbol, e.g., AAPL"),
  date: z
    .union([z.number(), z.string()])
    .optional()
    .describe("Options expiration (YYYY-MM-DD or epoch seconds)"),
};
const optionsSchema = z.object(optionsInput).passthrough();

const chartInput = {
  symbol: z.string().min(1).describe("Ticker symbol, e.g., AAPL"),
  range: z
    .string()
    .optional()
    .describe("Chart range like '1d', '5d', '1y'"),
  interval: z
    .string()
    .optional()
    .describe("Bar interval like '1m', '5m', '1d'"),
  period1: z.union([z.number(), z.string(), z.date()]).optional(),
  period2: z.union([z.number(), z.string(), z.date()]).optional(),
  events: z.union([z.string(), z.array(z.string())]).optional(),
  includePrePost: z.boolean().optional(),
};
const chartSchema = z.object(chartInput).passthrough();

// Helpers: normalize results to a consistent quote shape
function normalizeEpochSeconds(val) {
  if (val == null) return null;
  if (val instanceof Date) return Math.floor(val.getTime() / 1000);
  if (typeof val === "number") {
    // If it's clearly milliseconds, convert to seconds
    return Math.floor(val > 1e12 ? val / 1000 : val);
  }
  if (typeof val === "string") {
    const n = Number(val);
    if (!Number.isFinite(n)) return null;
    return Math.floor(n > 1e12 ? n / 1000 : n);
  }
  return null;
}

function toISO(epochSeconds) {
  const s = normalizeEpochSeconds(epochSeconds);
  if (s == null) return null;
  try {
    return new Date(s * 1000).toISOString();
  } catch (_) {
    return null;
  }
}

function normalizeFromQuoteApi(q) {
  if (!q || typeof q !== "object") return null;
  const price =
    q.regularMarketPrice ?? q.postMarketPrice ?? q.preMarketPrice ?? null;
  const asOfEpoch = normalizeEpochSeconds(
    q.regularMarketTime ?? q.postMarketTime ?? q.preMarketTime ?? null
  );
  return {
    symbol: q.symbol ?? null,
    name: q.longName ?? q.shortName ?? null,
    exchange: q.fullExchangeName ?? q.exchange ?? null,
    currency: q.currency ?? null,
    price,
    high: q.regularMarketDayHigh ?? null,
    low: q.regularMarketDayLow ?? null,
    previousClose: q.regularMarketPreviousClose ?? null,
    volume: q.regularMarketVolume ?? null,
    asOfEpoch,
    asOfISO: toISO(asOfEpoch),
    marketState: q.marketState ?? null,
    source: "quote",
  };
}

function normalizeFromChartApi(chart) {
  if (!chart || typeof chart !== "object") return null;
  const res = chart.chart ?? chart; // support raw or wrapped
  const result = Array.isArray(res?.result) ? res.result[0] : res?.result ?? res;
  if (!result) return null;
  const meta = result.meta ?? {};
  const ts = Array.isArray(result.timestamp) ? result.timestamp : [];
  const q = Array.isArray(result.indicators?.quote)
    ? result.indicators.quote[0]
    : {};
  const closes = Array.isArray(q?.close) ? q.close : [];
  const highs = Array.isArray(q?.high) ? q.high : [];
  const lows = Array.isArray(q?.low) ? q.low : [];
  const vols = Array.isArray(q?.volume) ? q.volume : [];

  // last non-null close
  let lastIdx = -1;
  for (let i = closes.length - 1; i >= 0; i--) {
    if (closes[i] != null) {
      lastIdx = i;
      break;
    }
  }
  const price = lastIdx >= 0 ? closes[lastIdx] : null;
  const asOfEpoch = lastIdx >= 0 && ts[lastIdx] != null ? ts[lastIdx] : null;

  // intraday range and volume (filter nulls)
  const validHighs = highs.filter((v) => v != null);
  const validLows = lows.filter((v) => v != null);
  const validVols = vols.filter((v) => v != null);
  const high = validHighs.length ? Math.max(...validHighs) : null;
  const low = validLows.length ? Math.min(...validLows) : null;
  const volume = validVols.length
    ? validVols.reduce((a, b) => a + b, 0)
    : null;

  return {
    symbol: meta.symbol ?? null,
    name: null, // not provided by chart meta
    exchange: meta.exchangeName ?? null,
    currency: meta.currency ?? null,
    price,
    high,
    low,
    previousClose: meta.chartPreviousClose ?? null,
    volume,
    asOfEpoch,
    asOfISO: toISO(asOfEpoch),
    marketState: meta.marketState ?? null,
    source: `chart:${meta.range ?? "1d"}@${meta.dataGranularity ?? "1m"}`,
  };
}

const NETWORK_CODES = new Set([
  "ENOTFOUND",
  "ECONNREFUSED",
  "EAI_AGAIN",
  "ECONNRESET",
  "ETIMEDOUT",
  "EHOSTUNREACH",
  "ENETUNREACH",
]);

function isLikelyNetworkError(err) {
  if (!err || typeof err !== "object") return false;
  const any = err;
  return (
    ("code" in any && typeof any.code === "string" && NETWORK_CODES.has(any.code)) ||
    ("name" in any && any.name === "FetchError")
  );
}

// Tool: getQuote
server.tool(
  "getQuote",
  "Fetch a normalized quote. Falls back to chart when quote is blocked.",
  quoteInput,
  async ({ symbol }) => {
    // First try the official quote endpoint
    try {
      const raw = await yf.quote(symbol);
      const normalized = normalizeFromQuoteApi(raw);
      if (!normalized) {
        throw new McpError(
          ErrorCode.InternalError,
          `quote returned empty for ${symbol}`
        );
      }
      return { content: [{ type: "text", text: JSON.stringify(normalized) }] };
    } catch (err) {
      // Fallback to chart-based synthesis if quote fails
      let quoteErr = err;
      try {
        const chart = await yf.chart(symbol, { range: "1d", interval: "1m" });
        const normalized = normalizeFromChartApi(chart);
        if (!normalized) {
          throw new Error("chart returned no data to synthesize quote");
        }
        return { content: [{ type: "text", text: JSON.stringify(normalized) }] };
      } catch (chartErr) {
        const qMsg =
          quoteErr && typeof quoteErr === "object" && "message" in quoteErr
            ? quoteErr.message
            : String(quoteErr);
        const cMsg =
          chartErr && typeof chartErr === "object" && "message" in chartErr
            ? chartErr.message
            : String(chartErr);

        const networkish = isLikelyNetworkError(quoteErr) || isLikelyNetworkError(chartErr);
        const message = networkish
          ? `Network restricted or unreachable while fetching ${symbol}. quote: ${qMsg}; chart: ${cMsg}`
          : `Failed fetching ${symbol}. quote: ${qMsg}; chart: ${cMsg}`;

        throw new McpError(ErrorCode.InternalError, message);
      }
    }
  }
);

// Tool: getOptions
server.tool(
  "getOptions",
  "Fetch option chain for a ticker symbol. Optionally filter by expiration date.",
  optionsInput,
  async ({ symbol, date }) => {
    try {
      const query = {};
      if (date !== undefined) query.date = date;
      const data = await yf.options(
        symbol,
        Object.keys(query).length ? query : undefined
      );
      return { content: [{ type: "text", text: JSON.stringify(data) }] };
    } catch (err) {
      const msg = err && typeof err === "object" && "message" in err ? err.message : String(err);
      throw new McpError(
        ErrorCode.InternalError,
        `getOptions failed for ${symbol}${date ? ` @ ${date}` : ""}: ${msg}. Check network access or API rate limits.`
      );
    }
  }
);

// Tool: getChart
server.tool(
  "getChart",
  "Fetch historical price chart data for a ticker symbol from Yahoo Finance.",
  chartInput,
  async ({ symbol, ...query }) => {
    try {
      const data = await yf.chart(
        symbol,
        Object.keys(query).length ? query : undefined
      );
      return { content: [{ type: "text", text: JSON.stringify(data) }] };
    } catch (err) {
      const msg = err && typeof err === "object" && "message" in err ? err.message : String(err);
      throw new McpError(
        ErrorCode.InternalError,
        `getChart failed for ${symbol}: ${msg}. Check network access or API rate limits.`
      );
    }
  }
);

// Start the server over stdio (no logs; silent)
const transport = new StdioServerTransport();
await server.connect(transport);
