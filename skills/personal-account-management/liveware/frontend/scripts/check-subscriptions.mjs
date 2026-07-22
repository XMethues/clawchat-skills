import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const source = await readFile(
  path.join(frontendDir, "src/lib/components/SubscriptionsSection.svelte"),
  "utf8",
);

assert.doesNotMatch(
  source,
  /<div class="grid gap-3 lg:grid-cols-2">/,
  "subscription detail cards must not be split into half-width desktop columns",
);
assert.match(
  source,
  /<Card\.Root class="[^"]*\bw-full\b[^"]*" data-status=/,
  "every subscription detail card must explicitly fill the content width",
);

console.log("subscription detail cards use the full content width");
