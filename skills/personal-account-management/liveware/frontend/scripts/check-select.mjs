import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const header = await readFile(
  path.join(frontendDir, "src/lib/components/DashboardHeader.svelte"),
  "utf8",
);
const layout = await readFile(
  path.join(frontendDir, "src/routes/+layout.svelte"),
  "utf8",
);
const navigation = await readFile(
  path.join(frontendDir, "src/lib/components/BottomNav.svelte"),
  "utf8",
);
const css = await readFile(path.join(frontendDir, "src/app.css"), "utf8");

assert.match(header, /<Select\.Root\b/);
assert.match(header, /<Select\.Trigger class="[^"]*w-\[180px\][^"]*"/);
assert.doesNotMatch(header, /<select\b/);
assert.doesNotMatch(header, /class="month-select"/);
assert.doesNotMatch(css, /\.month-select\b/);
assert.match(header, /import BottomNav from/);
assert.match(header, /<BottomNav\b/);
assert.doesNotMatch(layout, /<BottomNav\b/);
assert.doesNotMatch(navigation, /\bfixed\b/);
assert.match(navigation, /href:\s*"#\//);
assert.doesNotMatch(navigation, /<button\b/);
assert.match(header, /md:sticky/);
assert.match(header, /flex-col[^\"]*md:flex-row/);
assert.match(navigation, /md:min-h-8/);

console.log("toolbar flows normally on mobile and stays compact on desktop");
