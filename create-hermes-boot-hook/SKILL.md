---
name: create-hermes-boot-hook
description: Create or update customized Hermes Agent BOOT.md startup checklists and gateway:startup hooks, including HOOK.yaml and handler.py, with correct one-shot agent execution, deterministic delivery, silence handling, validation, and Session-mirroring boundaries. Use when a user asks to run checks, reports, alerts, maintenance, or other agent work whenever the Hermes Gateway starts or restarts.
---

# Create Hermes BOOT Hook

Create a Hermes startup workflow from the user's actual requirements. Generate the runtime files; do not install a generic fixed template.

## Required reference

Read [references/hermes-boot-hooks.md](references/hermes-boot-hooks.md) completely before inspecting or changing runtime files. Follow its architecture and safety boundaries.

## Workflow

1. Determine the Hermes home directory. Default to `~/.hermes` unless the user or environment specifies another location.
2. Inspect any existing `BOOT.md`, `hooks/boot-md/HOOK.yaml`, and `hooks/boot-md/handler.py`. Preserve unrelated behavior and user customizations.
3. Turn the user's request into an explicit startup contract:
   - what the startup agent must inspect or do;
   - what constitutes a useful report;
   - when it must remain silent;
   - which platform and target receive the report;
   - whether an existing Session is expected for conversational continuity;
   - required toolsets, limits, timeout expectations, and failure logging.
4. Ask only for requirements that cannot be safely inferred. A delivery destination is required: use an explicit `platform:target`, or a bare platform only when its home channel is already configured. Do not assume the startup channel directory is populated.
5. Generate or update exactly these runtime artifacts unless the user explicitly requests more:
   - `BOOT.md`: the customized checklist/prompt for the one-shot startup agent;
   - `hooks/boot-md/HOOK.yaml`: a Hermes hook manifest listening to `gateway:startup`;
   - `hooks/boot-md/handler.py`: a non-blocking handler that runs the agent and owns deterministic delivery.
6. Keep the three files consistent. `BOOT.md` controls the work and final-report format; `HOOK.yaml` controls activation; `handler.py` controls execution, silence filtering, delivery, and logging.
7. Validate before reporting completion:
   - parse `HOOK.yaml` as YAML;
   - compile `handler.py` with `python3 -m py_compile`;
   - confirm the manifest event is `gateway:startup` and `handler.py` exists beside it;
   - scan all three files for TODOs, example IDs, placeholder targets, and embedded secrets;
   - confirm exact silence-token comparison and direct in-process `send_message_tool` delivery;
   - confirm the handler never accesses private gateway globals or edits Session storage.
8. Explain the resulting behavior and the Session continuity limitation. Do not restart the gateway or send a real external message without the user's approval.

## Non-negotiable architecture

- Treat startup context as containing `platforms`; do not expect injected `gateway`, `session_store`, or a current chat.
- Return from `handle(event_type, context)` quickly by starting a daemon background thread.
- Construct a one-shot `AIAgent` with Hermes gateway model and runtime resolvers, `platform="gateway"`, bounded iterations, and startup-appropriate context settings; then call `run_conversation()`.
- Tell the agent to produce the report, not to call `send_message` itself.
- Let the handler call `tools.send_message_tool.send_message_tool` directly in the same process.
- Suppress delivery only when the stripped final response exactly equals one of `[SILENT]`, `SILENT`, `NO_REPLY`, or `NO REPLY`.
- Parse the tool's JSON result and log delivery success, error details, and `mirrored` state without leaking credentials.
- Do not shell out to `hermes send`; it is only a wrapper around the same tool and loses the reason to run in-process.
- Never use `_gateway_runner_ref`, mutate `sessions.json` or SQLite, or change `mirror_to_session()` to create sessions.
- State clearly that mirroring succeeds only when the destination Session already exists. A startup hook alone cannot guarantee first-contact reply continuity.

## Output quality

Prefer small, readable generated files. Put user-specific policy in `BOOT.md` and stable execution mechanics in `handler.py`. Add comments only where they explain a Hermes-specific constraint. Never create `scripts/`, `assets/`, or copied runtime templates inside this skill.
