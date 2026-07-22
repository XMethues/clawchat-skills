import adapter from "@sveltejs/adapter-static";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const outputDirectory = process.env.PAM_DASHBOARD_OUT_DIR || "../dist";
const projectDirectory = dirname(fileURLToPath(import.meta.url));

function sourceFiles(path) {
  if (!statSync(path).isDirectory()) return [path];
  return readdirSync(path)
    .sort()
    .flatMap((entry) => sourceFiles(join(path, entry)));
}

function sourceVersion() {
  const hash = createHash("sha256");
  for (const path of [
    join(projectDirectory, "src"),
    join(projectDirectory, "components.json"),
    join(projectDirectory, "package.json"),
    join(projectDirectory, "package-lock.json"),
    join(projectDirectory, "svelte.config.js"),
    join(projectDirectory, "vite.config.ts"),
  ].flatMap(sourceFiles)) {
    hash.update(relative(projectDirectory, path));
    hash.update(readFileSync(path));
  }
  return hash.digest("hex").slice(0, 16);
}

/** @type {import("svelte/compiler").CompileOptions} */
const config = {
  preprocess: vitePreprocess(),
  compilerOptions: {
    // Svelte's default scoped-CSS hash includes the absolute filename. Hash
    // CSS bytes instead so committed output is reproducible across checkouts.
    cssHash: ({ css, hash }) => `svelte-${hash(css)}`,
  },
  kit: {
    adapter: adapter({
      pages: outputDirectory,
      assets: outputDirectory,
      fallback: "index.html",
      precompress: false,
      strict: true,
    }),
    router: {
      type: "hash",
    },
    version: {
      name: sourceVersion(),
    },
  },
};

export default config;
