# CloakBrowser install reference

External dependency for `xhs-operator`. Captured from <https://cloakbrowser.dev> on 2026-07-16.

## What it is

A stealth Chromium binary with source-level patches (59 C++ patches compiled into the binary, not JS injection). Drop-in replacement for Playwright / Puppeteer. Designed for anti-bot-detection automation — passes reCAPTCHA v3, Cloudflare Turnstile, FingerprintJS, BrowserScan, bot.incolumitas.com, etc.

## Install methods

Three options, all from official sources:

```bash
# Python
pip install cloakbrowser

# Node
npm install cloakbrowser

# Docker (works without a Pro license)
docker run --rm cloakhq/cloakbrowser cloaktest
```

On first launch the wrapper auto-downloads the platform-appropriate Chromium binary (~200MB) and caches it locally.

## Platforms supported

Linux x64, Linux ARM64, Windows x64, macOS — current build v148 at time of capture.

## Pricing and license

CloakBrowser is **paid software**, not free. Plans (from the site):

| Plan     | Price (promo / regular) | Sessions       |
| -------- | ----------------------- | -------------- |
| Solo     | $19 / $29 per month     | 3 active       |
| Team     | $49 / $79 per month     | 20 active      |
| Business | $199 / $249 per month   | 200 active     |
| Scale    | $499 / $699 per month   | 2,000 concurrent |

For xhs-operator usage (one operator account, occasional publishing) the Solo plan is the natural floor.

Set the Pro license key via env var; no code changes needed:

```bash
export CLOAKBROWSER_LICENSE_KEY=<key>
```

When a subscription lapses, the wrapper falls back to a free build on the next license check.

## Pitfalls

### Server-side / headless sandboxes cannot run the login flow

`xhs-operator` logs in via QR code (`login --mode qr`) — the worker captures a QR screenshot and the owner scans it from the Xiaohongshu mobile app. This requires:

- A machine with a GUI session (or at least display + clipboard / screenshot delivery back to a human)
- Network reachability to the Xiaohongshu login endpoints from that machine

If the agent runs in a remote / headless / SSH-only sandbox, `check` may pass after install but the QR login flow has no human to scan. Plan to install CloakBrowser **on the owner's local desktop machine**, not in the agent sandbox.

### ToS / compliance tension

CloakBrowser's entire pitch is bypassing bot detection. Xiaohongshu explicitly prohibits automated publishing, mass posting, and fake-traffic behavior in its creator terms. Using a stealth browser to publish does not change the operator-side risk: a flagged publish, mass-publish pattern, or detected automation can still trigger account restrictions regardless of how invisible the browser is. This is an owner decision, not an agent decision.

### Don't auto-install on the agent's own authority

The skill (`xhs-operator/SKILL.md`) explicitly says "Do not install or update dependencies from this skill." This is by design: installing CloakBrowser costs money (license) and creates a long-running stateful binary the owner has not necessarily approved. Confirm with the owner before running `npm install cloakbrowser` or `pip install cloakbrowser`. A sandbox-only dry-run install (to make `check` pass) is reasonable as a minimal first step but does not unlock the actual publishing flow.

### Node wrapper requires `playwright-core` as a peer dep

`npm install cloakbrowser` ships the JavaScript wrapper but does **not** pull in `playwright-core`. The wrapper dynamically imports Playwright from `cloakbrowser/dist/playwright.js`. On the first `launch()` (or the first `check` that exercises the import path), Node will fail with:

```
Cannot find package 'playwright-core' imported from .../cloakbrowser/dist/playwright.js
```

Fix:

```bash
npm install playwright-core
# Python wrapper (pip install cloakbrowser) does not need this — pip pulls its own Playwright.
```

If a future CloakBrowser release starts bundling `playwright-core`, retire this caveat — verify by deleting the package and running `node .../scripts/xhs-operator.mjs check`.

### Where state lives

`xhs-operator` stores auth at `$HOME/xiaohongshu/auth/state.json` (Playwright `storageState`). After QR login this file holds cookies / localStorage — treat it as a credential. Do not commit, share, or sync it. `logout --confirm` deletes it.