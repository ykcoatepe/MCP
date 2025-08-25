import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function main() {
  const transport = new StdioClientTransport({
    command: "node",
    args: [new URL("./index.js", import.meta.url).pathname],
  });

  const client = new Client({ name: "yahoo-live-test", version: "1.0.0" });
  await client.connect(transport);

  const res = await client.callTool({
    name: "getQuote",
    arguments: { symbol: "TSLA" },
  });

  console.log(JSON.stringify(res, null, 2));
  await client.close();
}

main().catch((err) => {
  console.error("LIVE FETCH ERROR:", err);
  process.exit(1);
});

