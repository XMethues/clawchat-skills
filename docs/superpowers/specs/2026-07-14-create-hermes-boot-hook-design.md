# Create Hermes BOOT Hook Skill Design

## Goal

Create a repository-root skill named `create-hermes-boot-hook`. The skill guides an agent to generate or update a customized Hermes startup checklist and Gateway Hook from the user's requirements.

The generated artifact is not merely three files. It must implement Hermes's verified BOOT lifecycle and delivery behavior correctly.

## Skill structure

```text
create-hermes-boot-hook/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    └── hermes-boot-hooks.md
```

Do not add `scripts/` or `assets/`. The agent generates the output files dynamically because their instructions, target, silence conditions, and operational checks vary by user request.

## Generated artifact

The skill creates or updates:

```text
~/.hermes/
├── BOOT.md
└── hooks/
    └── boot-md/
        ├── HOOK.yaml
        └── handler.py
```

Respect a relocated Hermes home when the environment exposes one. Never assume that a project-local `.hermes` directory is the runtime state directory.

## Verified Hermes contract

The skill must teach and enforce these facts:

1. `HOOK.yaml` subscribes to `gateway:startup`.
2. A Gateway Hook handler is named `handle` and receives `event_type: str` and `context: dict`.
3. `gateway:startup` context contains the active platform-name list under `platforms`. It does not provide `GatewayRunner`, `SessionStore`, or a delivery target.
4. The handler must return quickly and run the one-shot BOOT agent in a daemon background thread.
5. Construct `AIAgent` with `_resolve_gateway_model()` and `_resolve_runtime_agent_kwargs()` so configured providers, endpoints, OAuth, and credential pools work.
6. Configure the one-shot run with `platform="gateway"`, `quiet_mode=True`, `skip_context_files=True`, `skip_memory=True`, and a bounded `max_iterations`.
7. Hermes does not ship BOOT.md as a built-in behavior. The user opts in by installing the generated files.

## Delivery design

The handler owns user-visible delivery. The BOOT agent must not call `send_message` itself.

The generated prompt tells the agent to put any report in its final response. After the run:

1. Normalize the final response only for silence-token comparison.
2. Treat exact `[SILENT]`, `SILENT`, `NO_REPLY`, or `NO REPLY` as no delivery.
3. Do not use substring matching; a real report containing one of those words must still be delivered.
4. For a non-silent response, call `tools.send_message_tool.send_message_tool` directly in the Gateway process with `action="send"`, the configured target, and the final response.
5. Parse its JSON-string result and log delivery success, failure, and whether `mirrored` is true.
6. Do not call `hermes send` as a subprocess from the handler. `hermes send` is only a CLI wrapper over the same tool and a separate process may not have access to a live plugin adapter.
7. Do not also return or send the report through a second path.

## Target rules

The skill asks for a target when the user wants delivery. Accept Hermes target forms such as:

- `platform` to use its configured home channel;
- `platform:chat_id` for an explicit conversation;
- `platform:chat_id:thread_id` where the platform supports threads.

Prefer an explicit ID or a configured home channel. `gateway:startup` fires before the initial channel directory build, so generated startup behavior must not depend on resolving a newly discovered human-readable channel name.

Validate the target as inert data. Never interpolate it into a shell command.

Allow a log-only BOOT hook when the user explicitly does not want message delivery.

## Session continuity boundary

`send_message_tool` calls `mirror_to_session()` after successful delivery. The mirror operation appends to an existing matching Gateway Session; it does not create one.

Therefore the skill must:

- report that a successful delivery may have `mirrored=false` when no matching Session exists;
- never claim that the generated BOOT Hook alone guarantees first-contact conversation continuity;
- never edit `sessions.json` or SQLite directly;
- never use private `_gateway_runner_ref` or add unsupported objects to `gateway:startup` context;
- never make `mirror_to_session()` create Sessions;
- explain that guaranteed first-contact continuity requires a platform integration to seed the canonical Session through its injected `SessionStore`, before the BOOT Hook runs.

For an existing Session, handler-owned delivery uses the standard `send_message_tool` path and is mirrored into that transcript.

## Agent workflow

When invoked, the skill instructs the agent to:

1. Discover the Hermes home and inspect existing `BOOT.md` and `hooks/boot-md` files.
2. Ask only for missing requirements: startup tasks, delivery target or log-only behavior, silence condition, iteration limit, and whether existing files may be replaced.
3. Preserve unrelated existing configuration and back up or patch existing BOOT files instead of blindly overwriting them.
4. Generate the three files from the confirmed requirements.
5. Validate `HOOK.yaml` as YAML, compile `handler.py`, and inspect permissions and paths.
6. Restart the Gateway only when the user authorizes a restart.
7. Verify hook discovery and logs after restart. Do not send a real external test message without explicit authorization.
8. Report the installed paths, validation evidence, target, silence behavior, and Session-continuity limitation.

## Safety requirements

- Do not put secrets, tokens, or private user data in `BOOT.md`, `HOOK.yaml`, logs, or generated source.
- Do not embed target values into shell source.
- Bound the one-shot agent iterations.
- Catch and log agent and delivery errors so the Gateway remains operational.
- Treat existing user files as user-owned and avoid destructive replacement.
- Do not promise successful delivery before checking the tool result.

## Validation

Validate the skill itself with the skill-creator validator. Then forward-test it against at least these cases in the isolated Hermes container without mounting unrelated skills:

1. A log-only startup checklist that returns a silent token.
2. A delivered report using a configured target with a mocked delivery backend.
3. A delivery to an existing synthetic Session, verifying `mirrored=true` and transcript persistence.
4. A delivery with no existing Session, verifying delivery can succeed while `mirrored` is absent/false.
5. Existing BOOT files, verifying the agent preserves or intentionally updates them rather than silently destroying them.
