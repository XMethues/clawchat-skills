# Hermes BOOT Hook reference

Use this reference to design user-owned Hermes Gateway startup workflows. Verify version-sensitive interfaces against the installed Hermes source and the current [Hermes Event Hooks documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks) before generating runtime code.

## Contents

- [Select a mode](#select-a-mode)
- [Respect runtime ownership](#respect-runtime-ownership)
- [Resolve the active Hermes home](#resolve-the-active-hermes-home)
- [Build the runtime artifacts](#build-the-runtime-artifacts)
- [Run an agent checklist](#run-an-agent-checklist)
- [Orchestrate deterministic actions](#orchestrate-deterministic-actions)
- [Apply the Liveware extension](#apply-the-liveware-extension)
- [Deliver through a Session](#deliver-through-a-session)
- [Test a deterministic greeting](#test-a-deterministic-greeting)
- [Validate safely](#validate-safely)

## Select a mode

| Mode | Use when | Runtime artifacts | Model cost |
| --- | --- | --- | --- |
| Agent checklist | Work needs tools, reasoning, summarization, or conditional reporting | `BOOT.md`, `HOOK.yaml`, `handler.py` | One agent turn per gateway start |
| Deterministic Hook | The action and success predicate are known | `HOOK.yaml`, `handler.py` | None |
| Hybrid | Known actions must run before a reasoned report | `BOOT.md`, `HOOK.yaml`, `handler.py` | One agent turn per gateway start |

Do not use an agent as a service manager. Do not use `BOOT.md` merely to hold configuration for deterministic code. If the user only wants to start Liveware, prefer a deterministic Hook. If the user wants to inspect several signals and decide whether to alert, prefer an agent checklist. Use the hybrid mode only when both responsibilities are real.

## Respect runtime ownership

Hermes discovers Gateway Hooks from the active profile's `hooks/<hook-name>/` directory. A Hook directory contains `HOOK.yaml` and `handler.py`; the handler must expose `handle(event_type, context)` and may be synchronous or asynchronous.

`gateway:startup` currently provides the active platform names. In the Hermes v2026.7.7.2 runtime inspected for this skill, the emitted context is `{ "platforms": [...] }`; it does not inject the Gateway's `SessionStore`. It fires before the initial channel directory is built, so platform names are not delivery destinations and human-readable destination lookup may not be ready. Recheck this interface against the installed runtime instead of coding against an assumed context shape. Gateway Hook dispatch catches handler exceptions, but a synchronous handler still occupies dispatch while it runs. Start a daemon worker and return immediately for any nontrivial work.

Keep ownership explicit:

1. `HOOK.yaml` subscribes to `gateway:startup`.
2. `handle()` reads only minimal state, suppresses duplicate execution, starts one daemon worker, and returns.
3. The worker owns deterministic steps, the optional agent turn, optional delivery, and bounded logging.
4. Target scripts own their own service, login, registration, tunnel, readiness, and logging behavior.
5. The agent owns reasoning and report text only.

Gateway Hooks run only in the messaging Gateway, not ordinary Hermes CLI sessions. They are trusted in-process Python and therefore have the same host access as Hermes.

## Resolve the active Hermes home

Never derive runtime paths from `Path.home() / ".hermes"` alone. Hermes supports `HERMES_HOME`, profiles, containers, and platform-native defaults. Inspect the installed version and prefer its single source of truth:

```python
from hermes_constants import get_hermes_home

HERMES_HOME = get_hermes_home()
BOOT_FILE = HERMES_HOME / "BOOT.md"
```

Resolve the home once at module load for a profile-scoped Gateway process. Propagate `str(HERMES_HOME)` as `HERMES_HOME` in every child-process environment. If the installed version does not expose `get_hermes_home`, identify its supported equivalent; do not silently fall back to a different profile.

During discovery, report the effective home and inspect only that profile. Do not write duplicate artifacts to both the default home and a profile home.

## Build the runtime artifacts

### `HOOK.yaml`

Use the installed manifest schema. The current minimal shape is:

```yaml
name: boot-md
description: Run the user-defined gateway startup workflow
events:
  - gateway:startup
```

Hermes discovers the sibling file as `handler.py`; do not invent a `handler:` field. Preserve supported metadata from an existing manifest. Require exactly one event: `gateway:startup`.

### `BOOT.md`

Write `BOOT.md` as a one-shot task, not general persona or memory. Include only applicable parts:

- the exact checks and their scope;
- permitted tools and read/write boundaries;
- evidence and freshness windows;
- definitions of failure, warning, and success;
- final report language and structure;
- the exact whole-response silence token;
- a statement that the handler owns deterministic startup and delivery.

Keep the checklist platform-neutral unless its actual checks concern one platform. Do not place platform routing, Session selection, home bindings, or destination identifiers in `BOOT.md`. Avoid “check everything,” placeholder paths, example destinations, open-ended maintenance, and instructions that are unsafe to repeat after every restart.

### `handler.py`

Keep top-level imports light and version-sensitive imports close to their use. Use one module-level lock or state guard so a repeated event cannot start a duplicate worker in the same process. Catch exceptions inside the worker; do not let them escape the thread.

Use this dispatch shape and keep all selected actions inside `_run_workflow()`:

```python
import logging
import threading

logger = logging.getLogger("hooks.boot-md")
_START_LOCK = threading.Lock()
_STARTED = False


def handle(event_type: str, context: dict) -> None:
    if event_type != "gateway:startup":
        return

    global _STARTED
    with _START_LOCK:
        if _STARTED:
            logger.info("BOOT workflow already started in this process")
            return
        _STARTED = True

    threading.Thread(
        target=_run_workflow,
        args=(tuple((context or {}).get("platforms") or ()),),
        name="hermes-boot-md",
        daemon=True,
    ).start()
```

Keep the one-shot guard set for the lifetime of the Gateway process. If the workflow fails, report or log that failure; do not silently rerun it in the same process.

Store user policy in named constants or a small immutable configuration block. Keep secret values out of generated code and logs. Log step names and bounded redacted details, never full provider configuration, environment contents, tokens, or raw credential errors.

## Run an agent checklist

Use the installed gateway's resolved model and provider runtime. The current documented imports are private-but-documented integration points and must be rechecked for the installed version:

```python
from gateway.run import _resolve_gateway_model, _resolve_runtime_agent_kwargs
from run_agent import AIAgent
```

Construct one quiet, bounded agent turn. Skip ambient context and memory unless the user's confirmed task needs them. Wrap the `BOOT.md` content in a short system-owned prompt that says:

- execute the checklist once;
- return the user-facing report as the final response;
- do not run deterministic lifecycle actions;
- do not call delivery tools;
- return only the configured silence token when there is nothing to report.

Treat a missing, empty, or malformed final response as a distinct failure. Strip only surrounding whitespace, then compare the whole response to the configured silence token or explicitly supported legacy tokens. Never use substring matching.

Keep `max_iterations` explicit. Inspect whether the installed `AIAgent` exposes a cleanup method or context manager and use it when required. Do not retry a full agent turn unless the user accepted the extra model cost and a precise retryable-failure classification.

For log-only mode, log a bounded summary instead of the complete report. For no-output mode, log only completion state. Delivery is a separate extension.

## Orchestrate deterministic actions

Put deterministic actions at the beginning of the daemon worker. Represent every step as a structured result such as:

```python
{"ok": True, "step": "liveware-start", "detail": "ready"}
```

Use one bounded subprocess helper:

```python
import os
import subprocess


def run_step(argv: list[str], cwd: Path, label: str, timeout: int) -> dict:
    env = os.environ.copy()
    env["HERMES_HOME"] = str(HERMES_HOME)
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "step": label, "detail": "timed out"}
    except OSError as exc:
        return {"ok": False, "step": label, "detail": redact(str(exc))}

    stream = completed.stdout if completed.returncode == 0 else completed.stderr or completed.stdout
    detail = redact((stream or "no output").strip()[-500:])
    return {
        "ok": completed.returncode == 0,
        "step": label,
        "detail": detail,
    }
```

Use the installed Hermes redaction helper when available; otherwise generate a narrow redactor for known secret forms and keep output aggressively bounded. Fixed argument arrays and `shell=False` are mandatory. A timeout bounds the orchestration attempt; it does not prove the target process stopped, so invoke only target scripts whose timeout behavior and lifecycle ownership were inspected.

Do not add an automatic retry merely because an action failed. A retry requires a known transient class, a fixed cap, and a delay bound. Never add an unbounded loop.

In hybrid mode, convert deterministic results into a short credential-free status block. Give that block to the agent with `BOOT.md`; do not inject raw process output or environment values. State whether a deterministic failure must always produce a report or may still result in silence.

## Apply the Liveware extension

Liveware setup and start are separate policies. Inspect the target skill before selecting either script or path; repository layouts vary.

Establish these facts:

- exact `setup.py` and `start.sh` locations and invocation contracts;
- state schema and what counts as prepared;
- setup effects, including login, remote app recovery or creation, local state writes, and registration;
- start lifecycle, idempotency, readiness, tunnel binding, logs, and exit behavior;
- behavior when a healthy service survived the Gateway restart;
- behavior when credentials, ClawChat activation, the Liveware CLI, or the target service are unavailable.

Select one setup policy:

| Policy | Behavior | Default guidance |
| --- | --- | --- |
| `require-prepared` | Run start; report its actionable prepared-state failure | Prefer when setup has external effects or no reliable predicate exists |
| `setup-if-needed` | Evaluate an inspected structured predicate, run setup at most once, then start | Use only with explicit standing approval and idempotent exact-match setup |
| `setup-always` | Run setup once on every Gateway start, then start | Use only when the user accepts repeated control-plane and authentication work |

Missing local state does not prove a remote app is absent. Let an inspected, idempotent setup script recover an exact-name app; never reproduce app lookup or creation in the Hook. Do not treat an arbitrary start failure as permission to run setup. Permit a setup-and-retry branch only for an inspected, setup-recoverable failure and run each step at most once.

Invoke `setup.py` with the confirmed Python executable and invoke `start.sh` with the confirmed shell. Do not copy Liveware login, registration, server launch, readiness, tunnel binding, or log handling into the Hook. Refuse boot automation when the launcher kills an unknown process, creates duplicates, never returns after readiness, or is otherwise unsafe to repeat.

## Deliver through a Session

Keep report generation independent from chat platforms. `BOOT.md` returns text; the handler selects the Session and performs delivery.

Treat these as different objects:

- **Hermes Session**: the conversation context that must receive the mirrored assistant message;
- **platform home binding**: configuration that points a platform at its intended conversation;
- **transport target**: the value consumed internally by the installed delivery adapter.

Do not ask the user for internal routing coordinates, expose them in the startup contract, or hard-code them in generated files. Store a semantic policy such as “the configured home Session for the selected platform,” then resolve it internally from platform configuration and Session metadata.

### Correct startup decision flow

Resolve continuity before spending model quota when the report exists only for delivery:

```text
Gateway starts
  ↓ emits {platforms: [...]}
Handler selects one configured platform
  ├─ no selected platform or no home binding → stop before model and send
  ├─ home binding has no existing Session → stop or defer; do not create
  ├─ home binding resolves ambiguously → stop; do not guess
  └─ home binding resolves to one existing Session
       ↓ run deterministic work and/or one agent turn
       ↓ send through the platform's bare target
       ↓ require transport success and mirroring into that Session
```

If the startup task must run even without delivery, run it under its confirmed log-only or no-output policy. Lack of a delivery route must not silently change whether unrelated deterministic work is required.

Use this delivery sequence:

1. Select the platform by configured name only. `context["platforms"]` may confirm availability, but it cannot select a conversation. If several platforms are enabled and the user has not selected one, stop instead of guessing.
2. Read that platform's home binding through the installed Hermes configuration API. Inspect its type and public fields; do not assume it is a string.
3. Resolve the binding to exactly one existing Hermes Session through the installed read-only Session lookup. Include all internally required participant and thread metadata without surfacing those values in policy or logs.
4. Stop without sending when no Session exists or more than one Session matches.
5. Invoke the installed delivery interface with the platform's bare target so the adapter uses its own home binding.
6. Parse either JSON text or a dictionary defensively, reject an `error` field, and require `success is True`.
7. Require the result to confirm mirroring into the pre-resolved Session when conversational continuity is part of the contract.

### Version-sensitive home resolution

Inspect the installed home-binding type and exact Session lookup before generating the handler. In the verified Hermes runtime, the home binding is a structured object rather than a destination string. Use its public origin and thread metadata only inside the handler's exact lookup. Do not stringify the object, request its internal values from the user, embed them as constants, or write them to logs.

Treat both the home object and Session lookup as version-sensitive interfaces. Generate code only after confirming their current fields and signature. Missing participant context, a missing match, or an ambiguous match must still fail closed.

In current Hermes versions, trusted runtime code can call `tools.send_message_tool.send_message_tool()`, but this is version-sensitive and must be inspected before generation. Never let the agent call the delivery tool itself.

For ClawChat, use the bare target `clawchat`. Activation owns the ClawChat home binding and records the activation conversation internally. Do not request, display, or persist its raw routing value in the Hook. Before sending, verify that the home binding resolves to one intended ClawChat Session. A direct Session is normally unambiguous; a group may have participant-specific Sessions and must include enough internal origin metadata to select exactly one.

The Session may not exist before the first inbound conversation. In that case a startup Hook cannot provide correct Session continuity. Fail closed and log the pending report; do not select the newest Session, call `get_or_create_session()`, create a row in storage, or fall back to another platform. Add deferred delivery on a later Session event only as a separately confirmed extension.

Recency is an activity signal, not a routing decision. The current `SessionStore.get_or_create_session()` also owns routing-key generation, reset policy, recovery, the in-memory index, and persistence. A standalone Hook does not own that lifecycle, and the current startup context does not provide the store. Reading a private runner reference or constructing another store would create split ownership.

If guaranteed delivery before an inbound Session is a product requirement, change Hermes core through a narrow public capability that resolves and delivers to the configured home Session. Do not pass the whole mutable store merely to make this Hook work. Until such an interface exists, stopping or explicitly deferring is the safe behavior.

After delivery reports `mirrored: true`, the proactive assistant message belongs to the resolved Session history. A later inbound message with the same platform, conversation, participant, type, and thread reuses that active Session under normal routing. An explicit new-session command, reset policy, ended Session, or changed origin may select a different Session.

Log these states separately:

- report produced or silent;
- Session resolved, missing, or ambiguous;
- transport succeeded or failed;
- mirror reached the resolved Session or failed.

Never solve routing by importing a private Gateway runner, editing `sessions.json`, writing to the state database, or changing mirror semantics.

## Test a deterministic greeting

Use this sequence for a disposable end-to-end test. Do not test first-contact delivery by pre-populating or manufacturing a Session.

1. Create a fresh disposable Hermes data copy and start it without the generated Hook.
2. Send one ordinary inbound message through the intended chat conversation. Confirm that exactly one active Session now represents that full origin.
3. Stop the Gateway without deleting the disposable data. Record only assertions or counts needed to identify the pre-existing Session; do not expose its internal routing values.
4. Generate a deterministic `HOOK.yaml` and `handler.py`; do not create `BOOT.md` for a fixed greeting.
5. Run static validation with transport and mirroring stubbed. Assert that a missing or ambiguous Session prevents sending.
6. Start the Gateway once. Verify that the exact greeting is visible in the chat client and appears exactly once as an assistant message in the pre-existing Session.
7. Send a normal reply through the same conversation. Verify that the reply is appended to the same active Session and that the agent can observe the mirrored greeting in its history.
8. Clean up the disposable container and data copy while preserving the reusable base.

When this repository's `.e2e` scripts are available, use their base-copy and cleanup flow. A fresh test copy clears runtime Session state, so the inbound-message step must happen before the Hook-bearing restart.

## Validate safely

Static validation must not execute user startup actions.

1. Parse the manifest and require the confirmed event set and sibling handler.
2. Compile the handler with bytecode redirected to a temporary directory.
3. Import the module with version-sensitive dependencies stubbed where needed.
4. Replace the thread target with a no-op and assert `handle()` returns promptly.
5. Trigger `handle()` twice in the same process and assert the guard prevents duplicate workers.
6. Unit-test silence handling with an exact token, a real report containing the token as a substring, an empty response, and surrounding whitespace.
7. Unit-test Session delivery with one match, no match, and ambiguous matches. Assert that only one match can reach transport, that the home object is not stringified, that mirroring is checked against the same resolved Session, and that recency never selects a destination.
8. Unit-test each deterministic policy branch with subprocess stubs; assert fixed argv, timeouts, retry caps, redaction, and failure propagation.
9. Scan for `TODO`, placeholder values, secrets, embedded routing values, `Path.home() / ".hermes"`, `shell=True`, unbounded loops or output, assumed `session_store` injection, recency-based routing, startup Session creation, private Gateway runner access, and direct Session persistence.

Then explain the proposed live test separately. Restarting the Gateway triggers the Hook and may consume model quota, run setup, start services, create or recover remote apps, bind tunnels, and send messages. Obtain explicit approval for each applicable effect before running `hermes gateway restart` or invoking target scripts directly.
