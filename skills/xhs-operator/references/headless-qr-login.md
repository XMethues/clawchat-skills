# Headless / no-display QR login

The login reference ([references/login.md](references/login.md)) assumes the agent is running on a machine with a GUI session. In a sandboxed agent (no X server, no Wayland, no clipboard, no display), the QR challenge still works — but the agent cannot show it. This reference covers the headless delivery idiom.

## The constraint

`xhs-operator login --mode qr` launches a Chromium via CloakBrowser. Chromium will render the QR page inside the browser, but in a headless agent there is no human-visible window. The wrapper's compensation: `worker.mjs` calls `page.screenshot()` after the QR loads and writes the PNG to:

```
$HOME/xiaohongshu/runs/<run-id>/qr.png
```

The same path is recorded in `state.json` as `qrScreenshot`. That PNG is the only delivery surface in headless mode.

## Delivery idiom

In Hermes, image content can be attached to the user-facing reply with the `MEDIA:` prefix:

```
MEDIA:/opt/data/home/xiaohongshu/runs/login-.../qr.png
```

The chat platform renders this as an inline image the user can long-press / scan / open in a new tab. For platforms where the QR is hard to scan from an inline preview (compressed, downscaled), offer to copy the file out to a path the user can reach.

## Polling loop in headless mode

```bash
# Launch
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs login --mode qr
# → returns {"runId":"login-...","statusFile":"..."} immediately
#
# Wait for the QR to be captured (cold first run can take 60+ s for the
# Chromium binary download; warm runs ~5-15 s)
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs status --run <run-id>
```

State transitions to expect:

| Status | What to do |
| --- | --- |
| `starting` | Wait. Do not deliver anything yet — no PNG exists. |
| `waiting_for_scan` | Deliver `MEDIA:<state.json: qrScreenshot>`. Continue polling at ~10 s intervals; do not assume success or failure. |
| `logged_in` | Stop polling. Tell the user. **Do not publish anything unsolicited.** |
| `failed` | Read `error`. Common cause on first run: `Cannot find package 'playwright-core'` — see [cloakbrowser-install.md](cloakbrowser-install.md). Do not retry blindly; the failure may be transient and a fresh run creates a new QR session. |
| `risk_verification_required` | Xiaohongshu served a captcha / slider / "异常操作" page. **Stop.** Do not retry, do not bypass, do not call a CAPTCHA service. Surface to the user and wait for direction. |

## Pitfalls

### Don't pre-deliver the screenshot

`status` flips to `waiting_for_scan` only after the PNG is fully written. If you deliver before that, the user gets a broken or empty image. Always confirm `qrScreenshot` exists on disk:

```bash
ls -la $HOME/xiaohongshu/runs/<run-id>/qr.png
```

### Don't recycle a stale QR

If the user does not scan within the worker's `waitForLogin` window (default 10 minutes), the QR expires server-side and the page eventually reloads. If the worker exits without `logged_in`, do not point the user at an old PNG — the next `login` call will issue a fresh session.

### Headless Chromium without `--no-sandbox` flags

In many sandboxes Chromium refuses to start without explicit `--no-sandbox`. The CloakBrowser wrapper handles this internally for typical cases, but if `check` passes yet `login` hangs at `starting`, suspect sandbox restrictions. Report the symptom; do not improvise flag workarounds.

### Don't dump the full `state.json` to a public channel

`state.json` after login contains `account`, `currentUrl`, `authState` path, and screenshot paths. The `account` field in particular has the user's nickname and may include the XHS ID. If echoing `state.json` to the user via a public channel (e.g., a shared chat), redact `account` and `authState` before sharing. The login reference does this implicitly; do not bypass it for "completeness".