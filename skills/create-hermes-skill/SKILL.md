---
name: create-hermes-skill
description: Create or update production-ready Hermes Agent skills, including requirements discovery, Skill-versus-Tool qualification, Hermes-native frontmatter, minimal supporting resources, profile installation, validation, testing guidance, and publication guidance. Use when a user wants to create, scaffold, revise, install, test, or prepare a Hermes skill for GitHub publication or a custom tap.
version: 0.1.0
author: ClawChat
license: MIT
metadata:
  hermes:
    tags: [Development, Hermes, Skills, Publishing]
---

# Create Hermes Skill

Create or update a focused Hermes Agent skill that is ready for runtime use. Produce a skill, not documentation about developing one.

## Required reference

Read [references/hermes-skill-requirements.md](references/hermes-skill-requirements.md) completely before creating, updating, installing, validating, or publishing a skill.

## Discover facts first

Inspect available context before asking questions:

- the user's request, concrete use cases, project instructions, and existing domain documentation;
- whether a skill with the requested name already exists;
- `HERMES_HOME`, the active Hermes profile, and the effective skills directory;
- the current workspace, Git repository, remote, license, author identity, and existing skill conventions;
- available Hermes CLI commands and their installed-version help when an action depends on them;
- tools, toolsets, platforms, environment variables, credential files, configuration, and external dependencies the workflow actually needs.

Do not ask the user for a fact that can be established safely from the environment. Do not install dependencies, collect secrets in chat, publish, push, or overwrite divergent copies during discovery.

## Qualify the capability

Use a skill when instructions, existing tools, shell commands, references, or small helper scripts can express the capability. Stop and explain the mismatch when the request requires a precise internal integration, built-in authentication flow, binary streaming, or real-time event handling that belongs in a Hermes Tool or plugin.

Do not silently turn a Tool request into a skill or a skill request into a Tool.

## Resolve requirements

Ask only unresolved questions that materially change the result. Ask exactly one question at a time, state relevant discovered facts, and recommend an answer with a short reason. Skip mechanical questioning when the request and environment already determine the answer.

Resolve applicable decisions in dependency order:

1. Exact triggers, supported tasks, expected outputs, and explicit exclusions.
2. Personal-only or publishable maintenance mode.
3. Skill name, version, author, license, tags, and platform restrictions.
4. Required tools, toolsets, configuration, secrets, credential files, and dependencies.
5. Reusable scripts, references, or assets that materially improve reliability.
6. Verification criteria and a safe representative live-test prompt.
7. Installation target and, for publishable skills, repository and distribution method.

Before writing, summarize the resolved contract and ask whether shared understanding has been reached. Do not create or change files until the user confirms.

## Select the maintenance location

- For a personal skill, maintain it directly under the effective Hermes skills directory.
- Resolve that directory as `$HERMES_HOME/skills` when `HERMES_HOME` is set; otherwise use `~/.hermes/skills`.
- For a publishable skill, maintain the source under the selected Git repository's `skills/<skill-name>/` directory and install a copy into the effective Hermes skills directory for testing.
- Never write the same skill to both `~/.hermes` and a different `$HERMES_HOME`.
- Always report the source directory and installed directory when they differ.

If the skill already exists, update it. Inspect every referenced support file, preserve unrelated behavior, and make the smallest coherent change. Ask before deleting or renaming files, replacing a divergent source or installed copy, or overwriting unrelated user work.

## Build the skill

Create `SKILL.md` in a directory whose name exactly matches the frontmatter `name`. Use lowercase letters, digits, and hyphens; start with a letter and keep the name concise.

Include publication-ready frontmatter:

- `name`, `description`, `version`, `author`, and `license`;
- `metadata.hermes.tags`;
- `platforms`, Hermes activation conditions, config declarations, environment variables, credential files, or blueprint metadata only when required by the confirmed behavior.

Use `0.1.0` as the default initial version. Never guess an unavailable author or license. Put trigger wording and supported contexts in `description` so Hermes can discover the skill correctly.

Write direct runtime instructions in imperative form. Cover, explicitly or by clear equivalent structure:

- when and how to perform the workflow;
- the operational procedure and decision boundaries;
- known failure modes and safe handling;
- verification of the result.

Put the common path first. Add a quick reference only when repeated commands benefit from one. Keep rare details in directly linked references.

Create only resources that the workflow uses:

- `scripts/` for repeated deterministic logic;
- `references/` for runtime knowledge loaded on demand;
- `assets/` for files copied or transformed into outputs.

Do not create empty directories, samples, placeholders, README files, changelogs, installation guides, or duplicate content. Prefer standard-library scripts, `curl`, and existing Hermes tools. Document an unavoidable external dependency in the skill's runtime procedure.

Reference bundled files with paths relative to `SKILL.md`. Use `${HERMES_SKILL_DIR}` when runtime commands need an absolute skill path. Use `${HERMES_SESSION_ID}` only when session identity is required. Do not add inline shell snippets unless the user explicitly accepts host execution and the installed Hermes configuration enables them.

## Keep the artifact runtime-pure

Include only instructions and knowledge required when the skill runs. Remove:

- interview transcripts, requirements prose, design rationale, research notes, and implementation retrospectives;
- TODOs, examples posing as real values, placeholders, and speculative future work;
- author-facing commentary such as "while developing this skill" or "according to the user's request";
- source summaries or citations that do not serve a runtime operation;
- duplicated setup, testing, or publishing documentation unrelated to the skill's own task.

Apply the same rule to references, scripts, comments, and assets. A finished skill must behave as an executable operating guide, not a development document.

## Install safely

After validation, install personal skills in place. For publishable skills, copy the validated source bundle to the effective Hermes skills directory without copying repository-only files.

Before replacing an installed skill, compare it with the source. Proceed without another question when it is the same maintained skill or the user already approved the update. Stop when both copies contain independent changes and ask which copy is authoritative.

Never modify `.bundled_manifest`, provenance records, tap state, or Hermes core files to force installation. Never use `--force` to bypass a security finding automatically.

## Validate

Perform every applicable check:

1. Parse YAML frontmatter and confirm required fields, valid types, semantic version, and directory/name agreement.
2. Confirm all relative links and `${HERMES_SKILL_DIR}` resources exist and remain inside the bundle.
3. Compile, parse, or syntax-check every included script and run a safe representative invocation when possible.
4. Scan for secrets, credential values, destructive or injection-prone commands, unbounded network actions, unsafe inline shell, and undeclared dependencies.
5. Scan for development traces, TODOs, placeholders, empty sections, empty directories, and auxiliary documentation.
6. Confirm declared platforms, tool conditions, configuration, environment variables, and credential files match actual runtime use.
7. Confirm the installed bundle is discoverable from the effective Hermes profile.

Generate a concrete `hermes chat -q "/<skill-name> ..."` test using a safe representative task. Explain that it starts an agent and may consume model quota or perform skill actions; run it only after explicit approval.

## Guide publication

For publishable skills, inspect the actual Git remote and produce exact commands for the selected path:

- `hermes skills publish skills/<skill-name> --to github --repo <owner/repo>`;
- direct GitHub installation of one skill;
- a custom tap whose default skill root is `skills/`;
- post-publication `inspect`, `install`, and security-audit checks.

Explain community trust and security scanning when relevant. Never publish, push, add a tap, change a public repository, or make the skill public without explicit authorization. Treat `--force` as a user-reviewed exception that cannot override a dangerous verdict, never as a normal publishing step.

## Report completion

Report the created or updated files, effective Hermes profile, installation result, validation evidence, safe live-test command, and exact publication next step. Mention unresolved limitations without adding them to the runtime artifact.
