# Hermes Skill Requirements

Use this reference to select Hermes-native fields, resources, installation behavior, and distribution commands.

## Skill boundary

Prefer a Skill when the capability can be expressed as instructions, shell commands, existing Hermes tools, an external CLI or API, references, or small helper scripts. Prefer a Tool or plugin when the capability requires built-in API-key management, an end-to-end authentication flow, precise internal processing on every call, binary streaming, or real-time events.

## Directory structure

`SKILL.md` is required. Add only the resource directories the workflow uses:

```text
<skill-name>/
├── SKILL.md
├── scripts/       # optional deterministic helpers
├── references/    # optional runtime knowledge
└── assets/        # optional output inputs or templates
```

Hermes uses the effective profile's `skills/` directory as the local source of truth. Use `$HERMES_HOME/skills/` when `HERMES_HOME` is set and `~/.hermes/skills/` otherwise. A skill placed there becomes available without a registration step.

## Frontmatter fields

Use this publishable baseline:

```yaml
---
name: my-skill
description: State what the skill does and when Hermes should use it.
version: 0.1.0
author: Author or organization
license: SPDX license identifier or project license
metadata:
  hermes:
    tags: [Category, Capability]
---
```

Use `platforms` only to restrict activation to `macos`, `linux`, or `windows`. Omit it to load on every platform.

### Conditional activation

Put activation conditions under `metadata.hermes`:

- `requires_toolsets`: hide the skill unless every named toolset is active.
- `requires_tools`: hide the skill unless every named tool is available.
- `fallback_for_toolsets`: hide the skill when any named primary toolset is active.
- `fallback_for_tools`: hide the skill when any named primary tool is available.

Use `requires_*` for genuine runtime requirements. Use `fallback_for_*` only for a fallback workflow that should disappear when a primary capability exists.

### Configuration and credentials

Use `metadata.hermes.config` for non-secret paths and preferences stored under `skills.config` in `config.yaml`. Each item requires `key` and `description`; add `default` and `prompt` only when useful.

Use `required_environment_variables` for secret string values. Each item requires `name`; `prompt`, `help`, and `required_for` are optional. Hermes can collect these securely in the local CLI and pass configured values into supported sandboxes. Never ask a user to paste a secret into a gateway or messaging conversation.

Use `required_credential_files` for OAuth tokens, client-secret files, service-account JSON, certificates, and other file-based credentials. Paths are relative to the effective Hermes home.

### Blueprints

Add `metadata.hermes.blueprint` only when the skill is also a proposed automation. Its presence marks the skill as runnable automation metadata. Use `schedule`, optional `deliver`, optional `prompt`, and optional `no_agent` according to the requested behavior. Installation suggests a cron job; it must not silently schedule one.

## Runtime resources

Hermes exposes the absolute loaded skill directory and substitutes:

- `${HERMES_SKILL_DIR}` with the absolute skill directory;
- `${HERMES_SESSION_ID}` with the active session ID, leaving it unchanged when no session exists.

Keep common instructions in `SKILL.md` and move detailed or rare operational knowledge to directly linked references. Prefer standard-library helpers and existing Hermes tools. Include a helper script when complex parsing or deterministic repeated logic would otherwise be rewritten on each run.

Inline shell snippets use the `!` command form and run on the host before the skill message is shown. They are disabled by default, require trusted skill sources and `skills.inline_shell: true`, have a configured timeout, and expose host-execution risk. Avoid them unless dynamic activation context is essential and explicitly accepted.

For a high-resolution image that must be delivered without lossy preview compression, include the literal `[[as_document]]` directive in the runtime response.

## Validation and security

Verify frontmatter, resource references, script syntax, declared requirements, and representative behavior. Test a loaded skill with a new Hermes session:

```sh
hermes chat --toolsets skills -q "/my-skill perform a safe representative task"
```

Treat the live test as an agent execution that can consume model quota and invoke skill actions.

Hub and third-party installs are scanned for exfiltration, prompt injection, destructive commands, shell injection, and supply-chain risks. `--force` can override some caution or warning findings after review; it cannot override a dangerous verdict.

## Distribution

Publish a skill to GitHub with the installed Hermes CLI's supported form:

```sh
hermes skills publish skills/my-skill --to github --repo owner/repo
```

A repository used as a tap normally stores skills under `skills/`:

```text
owner/repo/
└── skills/
    └── my-skill/
        └── SKILL.md
```

Consumers can add the repository or install one skill directly:

```sh
hermes skills tap add owner/repo
hermes skills install owner/repo/my-skill
hermes skills install owner/repo/skills/my-skill
```

Confirm the exact identifier using the repository layout and the installed CLI. Preview and verify distribution with applicable commands:

```sh
hermes skills inspect <source-identifier>
hermes skills install <source-identifier>
hermes skills audit
```

New custom taps and community sources receive community trust and standard security scanning. Publishing, pushing, tap changes, and public visibility are external state changes and require explicit authorization.

## Authoritative documentation

- [Creating Skills](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills)
- [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- [Working with Skills](https://hermes-agent.nousresearch.com/docs/guides/work-with-skills)
