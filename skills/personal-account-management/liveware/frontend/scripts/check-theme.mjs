import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const css = await readFile(path.join(frontendDir, "src/app.css"), "utf8");
const components = JSON.parse(
  await readFile(path.join(frontendDir, "components.json"), "utf8"),
);

function token(name) {
  const match = css.match(new RegExp(`--${name}:\\s*([^;]+);`));
  assert.ok(match, `missing --${name} theme token`);
  return match[1].trim();
}

function chroma(value) {
  const match = value.match(/^oklch\([^\s]+\s+([\d.]+)/);
  return match ? Number(match[1]) : null;
}

function hue(value) {
  const match = value.match(/^oklch\([^\s]+\s+[\d.]+\s+([\d.]+)/);
  return match ? Number(match[1]) : null;
}

const primary = token("primary");
const muted = token("muted");
const secondary = token("secondary");
const accent = token("accent");
const radius = token("radius");

assert.ok((chroma(primary) ?? 0) > 0.05, "primary should carry the teal brand color");
assert.ok(
  (hue(primary) ?? 0) >= 180 && (hue(primary) ?? 0) < 190,
  "primary should use the teal theme hue",
);
assert.equal(components.tailwind?.baseColor, "slate", "base color should remain slate");
assert.ok(
  secondary === "var(--muted)" || (chroma(secondary) ?? Infinity) <= 0.01,
  "secondary should remain neutral",
);
assert.ok(
  accent === "var(--muted)" || (chroma(accent) ?? Infinity) <= 0.01,
  "accent should remain neutral",
);
assert.notEqual(accent, primary, "accent must not reuse the primary brand color");
assert.ok(muted.length > 0);
assert.equal(radius, "0.45rem", "radius should use the official small preset");
assert.match(css, /@import "shadcn-svelte\/tailwind\.css";/);
assert.match(css, /\.dark\s*\{/);
assert.doesNotMatch(
  css,
  /^\.(?!dark(?:\s|\{))[a-zA-Z_-]/m,
  "global CSS should not contain application-specific class selectors",
);
assert.doesNotMatch(css, /--font-(?:display|body|mono)-stack:/);

console.log("theme token semantics are correct");
