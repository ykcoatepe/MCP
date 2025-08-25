import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function main() {
  const transport = new StdioClientTransport({
    command: "node",
    args: [new URL("./index.js", import.meta.url).pathname],
  });

  const client = new Client({ name: "yahoo-test-client", version: "1.0.0" });
  await client.connect(transport);

  const tools = await client.listTools();
  console.log("TOOLS:", JSON.stringify(tools, null, 2));

  await client.close();
}

main().catch((err) => {
  console.error("TEST ERROR:", err);
  process.exit(1);
});

