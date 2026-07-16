# Login workflow

Use this workflow for first login, expired login state, QR login, SMS login, and logout.

## Login method

Prefer QR login. Use SMS only when the user requests it.

### QR login

```bash
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs login --mode qr
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs status --run <run-id>
```

**`login` is asynchronous.** The wrapper `spawn()`s `worker.mjs` detached with stdio piped to `/dev/null`, then returns a `runId` immediately. A fast exit is normal, not a failure. `worker.log` inside the run directory is created but stays empty — that is by design, not a hang. Real progress only appears via `status`.

Polling cadence:
- **First poll 10–30 s after launch.** The wrapper may be downloading the ~200 MB stealth Chromium binary on first use (free build); a cold cache can take a minute.
- **Subsequent polls every 5–10 s** once `status` flips to `starting` and Chromium is being launched.
- **Stop polling once `status` becomes `waiting_for_scan`** and deliver the QR screenshot.

Terminal states to expect:

| status | meaning | action |
| --- | --- | --- |
| `waiting_for_scan` | QR captured; awaiting mobile app scan | deliver `qrScreenshot` path, continue polling |
| `logged_in` | mobile scan succeeded, session persisted | done for this login; do not publish anything unsolicited |
| `failed` | wrapper error (commonly missing `playwright-core` peer dep) | read `error`, do not retry blindly |
| `risk_verification_required` | Xiaohongshu served a captcha / slider | stop. Never retry, bypass, or use a CAPTCHA service. Surface to user. |

QR screenshot location: `<RUNS_DIR>/<run-id>/qr.png` (same path written into `state.json` as `qrScreenshot`).

### SMS login

Ask for the phone number, start login, and ask for the received code only after status becomes `waiting_for_code`:

```bash
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs login --mode sms --phone <phone>
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs sms-code --run <run-id> --code <code>
```

Never echo or retain the SMS code.

## Login state

Login state is stored at `$HOME/xiaohongshu/auth/state.json`. Publishing restores this state automatically. If the creator page redirects to login, report that authentication expired and start a new login workflow.

If status is `risk_verification_required`, stop. Do not retry, bypass verification, or use a CAPTCHA service.

## Logout

Require explicit user confirmation before deleting login state:

```bash
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs logout --confirm
```
