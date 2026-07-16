---
name: xhs-operator
display_name: XHS Operator
description: "Use a real local browser to simulate normal human interactions when uploading and publishing Xiaohongshu image-and-text notes: QR or SMS login, login-state reuse, 1-18 images, title/body/ordinary topics, originality/remix/copy/visibility/scheduling/collections/locations, preview confirmation, publishing, draft fallback, and local records. Use for Xiaohongshu image-and-text note uploads and creator-account session maintenance."
version: 0.1.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [Social Media, Xiaohongshu, Publishing, Browser Automation]
    blueprint:
      schedule: "0 3 * * 1"
      deliver: origin
      prompt: "Use xhs-operator to clean expired Xiaohongshu run records, then report only the number removed. Do not log in or publish."
      no_agent: false
---

# XHS Operator

Use a real local browser to simulate normal human interactions when uploading and publishing image-and-text notes for a Xiaohongshu creator account. Guide the user through content confirmation, uploading 1-18 images, filling the title and body, appending ordinary topics, configuring note settings, previewing the complete note, and approving the final publish action.

## Requirements

- Node.js 20 or later
- CloakBrowser, installed separately by the user: <https://cloakbrowser.dev>

Run the requirement check before login or publishing:

```bash
node /opt/data/skills/xhs-operator/scripts/xhs-operator.mjs check
```

If the check fails, stop and report the missing requirement. Do not install or update dependencies from this skill.

### CloakBrowser specifics (don't skip)

- **It is paid software.** Solo $19/mo floor, Team $49/mo, up to Scale $499/mo. Pro features require `CLOAKBROWSER_LICENSE_KEY` in the environment; without it the wrapper falls back to a free build.
- **Install on a GUI machine, not a headless sandbox.** QR login needs a human to scan the screenshot; that requires display + clipboard on the host running the worker. Confirm with the owner before installing.
- **ToS caveat.** CloakBrowser is purpose-built to bypass bot detection. Xiaohongshu prohibits automated publishing. Detection-side risk stays with the operator account regardless of how invisible the browser is.
- Full install options (pip / npm / docker), platform matrix, and pitfalls: see [references/cloakbrowser-install.md](references/cloakbrowser-install.md).

## Authorization gate (read before any install or login)

This skill drives a real browser against a real creator account. Several actions look mechanical but each carries non-reversible side effects. Get explicit owner confirmation before:

1. **`npm install` / `pip install` of cloakbrowser** — costs money on Pro plans, pulls a long-running stateful binary. Confirm source, version, and pricing tier.
2. **`npm install playwright-core` (or any peer dep)** — same rationale. The wrapper does not declare it automatically.
3. **`login --mode qr` / `login --mode sms`** — produces a real QR / SMS challenge bound to a real Xiaohongshu account. Confirm whose account and that the user will scan personally.
4. **`prepare --request <json>`** — fills the real publish form with images, title, body, topics. Confirm content has been approved; this is the final review surface.
5. **`confirm --token <token>`** — **the only command that actually publishes.** Never run without the owner explicitly approving the previewed note.
6. **`logout --confirm`, `cleanup --all --confirm`** — destructive; state cannot be recovered.

Default when ambiguous: stop and ask. The agent_behavior line "do not perform external actions on behalf of owner" applies throughout this skill.

## Workflows

- For QR login, SMS login, login-state recovery, or logout behavior, read [references/login.md](references/login.md).
- For image upload, title/body/topics, note settings, preview, confirmation, publishing, and failure handling, read [references/image-text-upload.md](references/image-text-upload.md).
- For CloakBrowser installation, pricing, license setup, and the `playwright-core` peer-dep pitfall, read [references/cloakbrowser-install.md](references/cloakbrowser-install.md).
- For delivering the QR screenshot back to a human in a **headless / no-display** agent environment (sandbox, server, CI), read [references/headless-qr-login.md](references/headless-qr-login.md).
- For ingesting image content the user shares via chat links (clawchat, external CDNs) before publishing, read [references/cloud-media-fetch.md](references/cloud-media-fetch.md).

Do not improvise browser operations. Use the bundled scripts and follow the applicable reference workflow.

## Records and logout

Every invocation removes successful runs older than 30 days and other runs older than 7 days. The optional Blueprint only suggests a weekly cleanup job; installation must never silently schedule it.

```bash
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs records
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs cleanup
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs cleanup --all --confirm
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs logout --confirm
```

Require explicit user confirmation before `cleanup --all --confirm` or `logout --confirm`.
