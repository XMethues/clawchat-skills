#!/usr/bin/env bash
set -euo pipefail
# LIVEWARE ANALYSIS V1: eyJhZGFwdGVyIjp7ImNvbW1hbmQiOlsiYmFzaCIsImxpdmV3YXJlL3NjcmlwdHMvc2VydmVyLnNoIl0sImRlZmF1bHRfcG9ydCI6MjYzMTYsImtpbmQiOiJleGlzdGluZy1sYXVuY2hlciIsImxvZyI6eyJvd25lciI6InRhcmdldCIsInBhdGgiOm51bGx9LCJyZWFkaW5lc3MiOnsia2luZCI6Imh0dHAiLCJ1cmwiOiJodHRwOi8vMTI3LjAuMC4xOntwb3J0fS9oZWFsdGh6In0sInJlcXVpcmVkX2NvbW1hbmRzIjpbImJhc2giLCJweXRob24zIiwiY3VybCIsInNlcSIsIm5vaHVwIl0sIndvcmtkaXIiOiIuIn0sImRpc3BsYXlfbmFtZSI6ImNsYXdjaGF0LW9mZmljZWNsaSIsImV2aWRlbmNlIjpbeyJwYXRoIjoiU0tJTEwubWQiLCJyZWFzb24iOiJTdGFibGUgc2tpbGwgaWRlbnRpdHkifSx7InBhdGgiOiJsaXZld2FyZS9zY3JpcHRzL3NlcnZlci5zaCIsInJlYXNvbiI6IkNvbW1hbmQgY29uc3VtZXMgZXhwb3J0ZWQgUE9SVCBlbnZpcm9ubWVudCB2YXJpYWJsZSJ9LHsicGF0aCI6InNjcmlwdHMvb2ZmaWNlLWxpdmUtZGlyZWN0b3J5LnB5IiwicmVhc29uIjoiVXNlci1jb25maXJtZWQgZGlyZWN0b3J5IHNlcnZlciBlbnRyeXBvaW50IGFuZCBoZWFsdGggaW50ZXJmYWNlIn1dLCJpc3N1ZXMiOltdLCJzY2hlbWFfdmVyc2lvbiI6MSwic2tpbGxfbmFtZSI6ImNsYXdjaGF0LW9mZmljZWNsaSIsInN0YXRpY19kaXIiOm51bGwsInN0YXR1cyI6InJlYWR5IiwidGFyZ2V0X3Jvb3QiOiIvVm9sdW1lcy9TQU1TVU5HL1Byb2plY3RzL2NsYXdjaGF0LXNraWxscy9za2lsbHMvY2xhd2NoYXQtb2ZmaWNlY2xpIn0=

SKILL_NAME=clawchat-officecli
SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HERMES_HOME="${HERMES_HOME:-${HOME}/.hermes}"
STATE_FILE="${HOME}/.clawling/apps/${SKILL_NAME}.json"
LIVEWARE_BIN="${LIVEWARE_BIN:-}"

if [ -z "$LIVEWARE_BIN" ]; then
  LIVEWARE_BIN="$(command -v liveware || true)"
fi
if [ -z "$LIVEWARE_BIN" ] && [ -x "${HERMES_HOME}/clawchat/liveware/liveware" ]; then
  LIVEWARE_BIN="${HERMES_HOME}/clawchat/liveware/liveware"
fi
if [ -z "$LIVEWARE_BIN" ] || [ ! -x "$LIVEWARE_BIN" ]; then
  echo "start: Liveware CLI was not found. Install it separately or set LIVEWARE_BIN." >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "start: python3 is required to validate Liveware state." >&2
  exit 1
fi
if [ ! -f "$STATE_FILE" ]; then
  echo "start: Liveware state is missing. Run liveware/scripts/setup.py first." >&2
  exit 1
fi

STATE_LINE="$(python3 - "$STATE_FILE" "$SKILL_NAME" <<'PY'
import json
import re
import sys

path, skill_name = sys.argv[1:]
app_re = re.compile(r"^app-[A-Za-z0-9][A-Za-z0-9_-]*$")
try:
    with open(path, encoding="utf-8") as stream:
        state = json.load(stream)
except (OSError, json.JSONDecodeError):
    raise SystemExit("start: Liveware state is invalid.")
if not isinstance(state, dict):
    raise SystemExit("start: Liveware state is invalid.")
app_id = state.get("app_id")
url = state.get("public_url")
url_re = re.compile(
    rf"^https://{re.escape(app_id) if isinstance(app_id, str) else ''}\."
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$"
)
valid = (
    state.get("schema_version") == 1
    and state.get("skill_name") == skill_name
    and state.get("app_name") == skill_name
    and isinstance(app_id, str)
    and app_re.fullmatch(app_id)
    and isinstance(url, str)
    and url_re.fullmatch(url)
    and state.get("registered") is True
)
if not valid:
    raise SystemExit("start: Liveware state is invalid or registration is incomplete.")
print(f"{app_id}\t{url}")
PY
)" || exit 1
IFS=$'\t' read -r APP_ID PUBLIC_URL <<<"$STATE_LINE"

# BEGIN TARGET SERVER ADAPTER
PORT="${PORT:-26316}"
case "$PORT" in ''|*[!0-9]*) echo "start: PORT must be an integer from 1 to 65535." >&2; exit 1;; esac
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then echo "start: PORT must be an integer from 1 to 65535." >&2; exit 1; fi
export PORT
if ! command -v -- bash >/dev/null 2>&1; then printf 'start: Missing required command: %s.\n' bash >&2; exit 1; fi
if ! command -v -- python3 >/dev/null 2>&1; then printf 'start: Missing required command: %s.\n' python3 >&2; exit 1; fi
if ! command -v -- curl >/dev/null 2>&1; then printf 'start: Missing required command: %s.\n' curl >&2; exit 1; fi
if ! command -v -- seq >/dev/null 2>&1; then printf 'start: Missing required command: %s.\n' seq >&2; exit 1; fi
if ! command -v -- nohup >/dev/null 2>&1; then printf 'start: Missing required command: %s.\n' nohup >&2; exit 1; fi
wait_for_http() {
  python3 - "$1" <<'PY'
import sys
import time
import urllib.request
url = sys.argv[1]
for _ in range(40):
    try:
        with urllib.request.urlopen(url, timeout=0.5):
            raise SystemExit(0)
    except Exception:
        time.sleep(0.25)
raise SystemExit(1)
PY
}
cd -- "$SKILL_ROOT/."
SERVER_COMMAND=(bash liveware/scripts/server.sh)
"${SERVER_COMMAND[@]}"
if ! wait_for_http "http://127.0.0.1:${PORT}/healthz"; then
  echo "start: Existing launcher returned but the target service is not ready." >&2
  exit 1
fi
# END TARGET SERVER ADAPTER

# BEGIN LIVEWARE BINDING
"$LIVEWARE_BIN" tunnel bind "$APP_ID" "http://127.0.0.1:${PORT}"
printf 'Liveware ready: %s\n' "$PUBLIC_URL"
# END LIVEWARE BINDING
