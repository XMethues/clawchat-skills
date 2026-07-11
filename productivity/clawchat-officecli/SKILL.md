---
name: clawchat-officecli
description: Use this skill when Hermes needs to work with OfficeCLI in ClawChat, route Office document tasks to official OfficeCLI skills, read browser-selected Office content, manage the Office document root, or start the Liveware preview directory.
---

# Clawchat OfficeCLI

Use this skill to guide OfficeCLI usage in ClawChat and to expose an OfficeCLI
preview directory through Liveware. For Office document content work, route to
the most specific official OfficeCLI skill first, then use the OfficeCLI CLI or
MCP exactly as that official skill instructs. Liveware is only the browser
preview and file-directory layer.

## Primary Rule

When the user asks to create, read, inspect, edit, format, summarize, validate,
or continue work on an Office document, use OfficeCLI. Do not use Liveware,
directory JSON APIs, or watch HTTP endpoints as the document API.

Use this order:

1. Select the most specific official OfficeCLI skill for the task.
2. Resolve `OFFICE_BIN` and set `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1`.
3. Locate or create the target file in the managed document root.
4. Use OfficeCLI commands or OfficeCLI MCP for document reads and writes.
5. Use Liveware only when the user wants a browser preview or file directory.

OfficeCLI command bootstrap:

```bash
HERMES_HOME="${HERMES_HOME:-${HOME}/.hermes}"
OFFICE_BIN="${OFFICE_BIN:-$(command -v officecli || true)}"
OFFICE_BIN="${OFFICE_BIN:-$HOME/.local/bin/officecli}"
if [ ! -x "$OFFICE_BIN" ] && [ -x "${HERMES_HOME}/home/.local/bin/officecli" ]; then OFFICE_BIN="${HERMES_HOME}/home/.local/bin/officecli"; fi
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" --help
```

Common OfficeCLI commands:

```bash
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" create "$DOC"
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" get "$DOC" "/" --json
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" get "$DOC" selected --json
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" query "$DOC" "p" --json
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" set "$DOC" "/body/p[1]" --prop text="Updated text"
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" add "$DOC" "/body" --type p --prop text="New paragraph"
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" remove "$DOC" "/body/p[2]"
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" batch "$DOC" --commands "$COMMANDS_JSON"
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" validate "$DOC" --json
```

Selection workflow:

1. Ask the user to click or select content in the browser preview.
2. Read the current selection with:

   ```bash
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" get "$DOC" selected --json
   ```

3. Modify the selected node with the official OfficeCLI skill's recommended
   `set`, `add`, `remove`, or `batch` command.
4. Do not call `/api/selection`; it is an internal watch-page write channel.

## Scope

Use this skill to:

- Guide agents to use official OfficeCLI skills and OfficeCLI commands.
- Read browser-selected preview content through `officecli get <file> selected --json`.
- Choose and enforce the managed Office file directory.
- Start the browser preview directory.
- List managed `.docx`, `.pptx`, and `.xlsx` files.
- Route document work to the most specific official OfficeCLI skill.
- Keep runtime state and logs out of document directories.

## Requirements

Install and verify these before using the preview-directory workflow.

Required:

1. Install OfficeCLI and set `OFFICE_BIN` to the actual binary path.

   ```bash
   INSTALL_DIR="${HERMES_HOME}/workspace/office-live/.state/scratch"
   mkdir -p "$INSTALL_DIR"
   OFFICECLI_INSTALLER="$INSTALL_DIR/officecli-install.sh"
   curl -fsSL https://d.officecli.ai/install.sh -o "$OFFICECLI_INSTALLER"
   bash "$OFFICECLI_INSTALLER"
   OFFICE_BIN="${OFFICE_BIN:-$(command -v officecli || true)}"
   OFFICE_BIN="${OFFICE_BIN:-$HOME/.local/bin/officecli}"
   if [ ! -x "$OFFICE_BIN" ] && [ -x "$HERMES_HOME/home/.local/bin/officecli" ]; then OFFICE_BIN="$HERMES_HOME/home/.local/bin/officecli"; fi
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" --help
   ```

   Always run OfficeCLI with `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1` in this container.

2. Install the official OfficeCLI Hermes skills.

   ```bash
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills hermes
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills install word hermes
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills install pptx hermes
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills install excel hermes
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills install word-form hermes
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills install morph-ppt hermes
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills install morph-ppt-3d hermes
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills install pitch-deck hermes
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills install academic-paper hermes
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills install data-dashboard hermes
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills install financial-model hermes
   ```

   Check available official skills with:

   ```bash
   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 "$OFFICE_BIN" skills list
   ```

3. Install this skill and its scripts in a Hermes skill directory and run it through
   `${HERMES_SKILL_DIR}`.

Recommended:

- Configure OfficeCLI MCP as server `officecli` in `$HOME/.hermes/config.yaml`.
- Restart Hermes Agent after adding or changing MCP config so MCP tools are discovered.
- Use MCP for structured OfficeCLI operations when available, while still following
  the matching official OfficeCLI skill.

## Official Skill Routing

Before any Office document operation, choose the most specific official OfficeCLI skill.
Task-specific skills take precedence over file-format skills.

| User request | Official skill to use first |
| --- | --- |
| Form or structured Word form | `officecli-word-form` |
| Pitch deck | `officecli-pitch-deck` |
| Academic paper | `officecli-academic-paper` |
| Data dashboard | `officecli-data-dashboard` |
| Financial model | `officecli-financial-model` |
| PowerPoint morph animation | `morph-ppt` or `morph-ppt-3d` |
| Generic Word document | `officecli-docx` |
| Generic PowerPoint deck | `officecli-pptx` |
| Generic Excel workbook | `officecli-xlsx` |

Rules:

1. Use this skill only for workspace location, preview-directory startup, and file listing.
2. Use the selected official skill for creation, editing, reading, formatting, schema paths, save behavior, and validation.
3. Treat official OfficeCLI skills as the source of truth for document operations.
4. The browser directory may create blank files through the OfficeCLI CLI so a preview can open; chat-driven document content work still belongs to the official skills.
5. The browser directory can submit a prompt to a Hermes gateway agent, and that agent must send ClawChat messages with the `send_message` tool.
6. Do not use `hermes send` for ClawChat delivery from Liveware or directory-server processes.
7. If no official skill appears to fit, inspect the installed official OfficeCLI skills before inventing a document workflow.

## Liveware Reference

Liveware service details are intentionally kept out of this main skill. When the
user needs browser preview, file-directory UI, Liveware setup, tunnel binding,
directory-server state, or preview troubleshooting, read:

```bash
${HERMES_SKILL_DIR}/references/officecli-liveware.md
```

Use the bundled scripts described there. Do not ask the user to complete preview
setup before trying the start script.

## List Managed Files

When the user asks which Office files are available, list the managed document root first:

```bash
DOC_ROOT="${OFFICE_DOC_ROOTS:-${OFFICE_LIVE_HOME:-$HERMES_HOME/workspace/office-live}/documents}"
find "$DOC_ROOT" -maxdepth 1 -type f \( -name '*.docx' -o -name '*.pptx' -o -name '*.xlsx' \) -print
```

Search the managed document root before considering user-provided additional roots.

## Selection Guardrails

- Browser selection is an OfficeCLI watch feature.
- After the user selects content in the preview, read it with
  `officecli get <file> selected --json`.
- Do not call `/api/selection` from the agent to read selection state.
- Do not call `/api/selection` to modify documents.
- `/api/selection` is an internal watch-page write channel used by the browser
  preview to synchronize selection into the watch process.
- If `get selected` returns no matches, ask the user to click/select content in
  the preview and then retry the official CLI command.

## Agent Workflow

1. Select the most specific official OfficeCLI skill for the requested document work.
2. Follow that official skill for all document operations.
3. List managed Office files from the document root when file discovery is needed.
4. Identify the target file or ask the user to choose one.
5. Read `references/officecli-liveware.md` only when Liveware account, app, tunnel, preview startup, or preview-directory troubleshooting is needed.
6. Keep files in the managed document root unless the user explicitly provides another clean workspace.

## Troubleshooting

- If OfficeCLI exits with an ICU error, rerun with `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1`.
- If the preview directory or Liveware tunnel has issues, read `references/officecli-liveware.md`.

## Script Shareability

The bundled scripts under `scripts/` are designed to be shared — no hardcoded
app IDs, user IDs, domains, or absolute paths. All configuration is through
environment variables with sensible defaults:

| Env var | Default | Purpose |
| --- | --- | --- |
| `HERMES_HOME` | `~/.hermes` | Hermes home directory (optional fallback) |
| `LIVEWARE_DOMAIN` | `apps.clawling.io` | Liveware public URL domain |
| `OFFICE_LIVE_HOME` | `$HERMES_HOME/workspace/office-live` | Workflow home |
| `LIVEWARE_BIN` | `liveware` | Liveware CLI binary |
| `OFFICE_BIN` | auto-detected | OfficeCLI binary |

The Liveware app name is **hardcoded** as `OfficeCLI-Live` in
`scripts/office-liveware-setup.py` — not configurable. This keeps the script
clean for sharing.

When extending these scripts:
- Never hardcode an app ID, user ID, or absolute path.
- New configuration should follow the env-var-with-default pattern.
- State files (`liveware.env`, `directory.pid`) go under `.state/` at runtime,
  not in the script source.

### ClawChat registration

Registration must use the **Hermes plugin's internal credential store**, which
is only accessible from Python code running inside the gateway process. The
`$CLAWCHAT_TOKEN` env var is NOT the ClawChat API token.

The bundled `scripts/office-liveware-setup.py` handles this correctly:

```python
from clawchat_gateway.tools import register_app
# await register_app(name="OfficeCLI-Live", app_id="...", url="...")
```

Or via the Hermes tool call in a conversation:
```
clawchat_register_app(name="OfficeCLI-Live", appId="...", url="...")
```

### Integration: boot-md hook

The `boot-md` hook at `hooks/boot-md/handler.py` drives the full startup flow:

```
handler.py (_run_boot_policy)
  ├─ _ensure_liveware_sample_disabled()
  ├─ _ensure_officecli_ready()
  ├─ _prepare_liveware()
  │    ├─ check APP_ID in state file
  │    ├─ if missing → python3 setup.py   ← steps 1-4: login, create app, register, sync SOUL
  │    └─ start.sh <port>                 ← steps 5-6: start directory, tunnel bind
  ├─ _draft_message_sync()
  ├─ _finalize_message_sync()
  └─ _send_to_clawchat()
```

The boot hook reads the APP_ID from the liveware state file. If missing, it
runs `setup.py` (login → create app → register to ClawChat). Then it always
runs `start.sh` to start the directory service and bind the tunnel.

The ClawChat registration via plugin tools happens inside `setup.py`, not in
the boot hook or `start.sh`.

The boot hook also has a regex to extract the public URL from script output:

```python
PUBLIC_URL_RE = re.compile(r"https://[A-Za-z0-9_.-]+\\\\.apps\\\\.clawling\\\\.io")
```

If `LIVEWARE_DOMAIN` is changed to a non-`apps.clawling.io` value, this regex
must be updated in sync — otherwise the URL won't be captured.

### Architecture: 6-step workflow model

The liveware service follows a clean 6-step model split across two scripts:

```
setup.py (one-time):       start.sh (every boot):
  1. login                   5. start directory server
  2. create app              6. tunnel bind
  3. register to ClawChat
  4. sync SOUL.md → profile
```

**Setup.py does 4 things, not 3.** In addition to login, create app, and register,
it also reads `SOUL.md` (the agent's identity file) and syncs the `name` and
`avatar` to the ClawChat account profile via `clawchat_gateway.tools.update_account_profile`.
This happens only once during setup — subsequent boots skip it entirely and just
greet.

The SOUL.md parsing follows the Hermes docs convention (headings, "You are" style):

```
# Persona — Caden

Your name is Caden.       → extracts "Caden" as nickname
Avatar: https://...       → extracts URL as avatar_url
```

SOUL.md is a third-person description of the agent, not first-person. It uses
`# Persona — <name>` as the heading, `Your name is` for the name line, and
`You are` / `You don't` / `You value` throughout — never "I" statements.

If SOUL.md is missing or has no name/avatar, the sync is silently skipped.

**Registration doesn't need tunnel bind.** The ClawChat
registration URL is deterministic from the app ID alone:

```
https://{app_id}.{LIVEWARE_DOMAIN}
# e.g. https://app-8096cb458a8459da.apps.clawling.io
```

So step 3 can happen immediately after step 2, before the directory server or
tunnel exist. The two halves are independent:

| Step | Requires | Handled by |
|------|----------|-----------|
| 1. login | Plugin credential store | `setup.py` |
| 2. create app | liveware CLI | `setup.py` |
| 3. register | Plugin credential store | `setup.py` |
| 4. start server | Python + network port | `start.sh` |
| 5. tunnel bind | Running directory server | `start.sh` |

**start.sh is intentionally shell, not Python.** It only does process
management (`nohup`, PID files), `curl` health checks, and liveware CLI calls
— all shell-friendly. No ClawChat plugin tools are needed, so no Python
conversion is required.

### Architecture: registration in setup.py (not shell, not handler.py)

ClawChat app registration (`POST /v1/agents/me/apps`) must use the **Hermes
plugin's internal credential store**, which is only accessible from Python code
running inside the gateway process. A shell script cannot do this correctly
because `$CLAWCHAT_TOKEN` is not the ClawChat API token.

The correct architecture separates concerns:

```
handler.py (gateway:startup)
  ├─ check APP_ID in state file
  ├─ if missing → python3 setup.py   ← steps 1-4: login, create app, register, sync SOUL
  ├─ start.sh <port>                 ← steps 5-6: start directory, bind tunnel
  └─ send startup message
```

`setup.py` (Python, not shell) has access to plugin tools:

```python
# scripts/office-liveware-setup.py
import sys
sys.path.insert(0, str(Path.home() / ".hermes" / "plugins" / "clawchat"))

from clawchat_gateway.tools import liveware_login, register_app
import asyncio

async def setup():
    await liveware_login()                       # login via plugin credential store
    app_id = create_or_reuse_app()               # liveware CLI
    await register_app(                          # register via plugin credential store
        name="OfficeCLI-Live",
        appId=app_id,
        url=f"https://{app_id}.{domain}"
    )
    await sync_soul_profile()                    # read SOUL.md, update ClawChat name/avatar

asyncio.run(setup())
```

The Python script dynamically resolves the clawchat plugin directory by
traversing up from the script's own location to find `plugins/clawchat` under
`HERMES_HOME` (fallback `~/.hermes`). This makes the script portable and
shareable — no hardcoded paths.

**Why not handler.py?** Registration is a one-time setup action (app creation),
not a per-boot action. Putting it in setup.py keeps the boot hook focused on
startup orchestration and makes the setup/start separation clear. The
ClawChat registration API is idempotent, so running it from setup.py on
first install is sufficient.

### Pitfall: stale demo-doc app

Older versions created an app named `demo-doc`. If you see this in `liveware
app list`, it's a leftover from before the naming convention was set to
`OfficeCLI-Live`. Delete it with `liveware app delete <id>` and unregister
from ClawChat with `clawchat_unregister_app(appId="<id>")` if it was
registered.
