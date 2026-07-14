# Create Hermes BOOT Hook Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repository-root skill that guides an agent to generate safe, customized Hermes `BOOT.md`, `HOOK.yaml`, and `handler.py` files using the verified Gateway Hook and delivery behavior.

**Architecture:** Keep the skill procedural and dynamic: `SKILL.md` owns the workflow and routes detailed Hermes contracts to one reference file. `agents/openai.yaml` exposes only UI metadata. Do not add scripts or assets because the consuming agent generates the requested files from user requirements.

**Tech Stack:** Markdown skill instructions, YAML skill metadata, Hermes Python Gateway Hooks, skill-creator validation, Docker-based Hermes E2E fixture.

---

### Task 1: Initialize the skill skeleton

**Files:**
- Create: `create-hermes-boot-hook/SKILL.md`
- Create: `create-hermes-boot-hook/agents/openai.yaml`
- Create: `create-hermes-boot-hook/references/`

- [ ] **Step 1: Verify the skill does not already exist**

Run: `test ! -e create-hermes-boot-hook`

Expected: exit code 0.

- [ ] **Step 2: Initialize through skill-creator**

Run:

```bash
python /Users/nb-colin/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  create-hermes-boot-hook \
  --path . \
  --resources references \
  --interface 'display_name=Create Hermes BOOT Hook' \
  --interface 'short_description=Create safe Hermes startup agent hooks' \
  --interface 'default_prompt=Use $create-hermes-boot-hook to create a Hermes BOOT.md startup hook for my requirements.'
```

Expected: the skill directory contains `SKILL.md`, `agents/openai.yaml`, and an empty `references/` directory, with no `scripts/` or `assets/`.

- [ ] **Step 3: Inspect generated metadata**

Run: `sed -n '1,160p' create-hermes-boot-hook/agents/openai.yaml`

Expected: quoted interface strings and a default prompt that names `$create-hermes-boot-hook`.

- [ ] **Step 4: Commit the skeleton**

```bash
git add create-hermes-boot-hook
git commit -m "feat: initialize Hermes boot hook skill"
```

### Task 2: Write the verified Hermes reference and skill workflow

**Files:**
- Modify: `create-hermes-boot-hook/SKILL.md`
- Create: `create-hermes-boot-hook/references/hermes-boot-hooks.md`

- [ ] **Step 1: Write the detailed reference**

Create `references/hermes-boot-hooks.md` with these explicit contracts:

```markdown
# Hermes BOOT Hook Reference

- `gateway:startup` context contains only `platforms`.
- Run the one-shot agent in a daemon thread.
- Resolve the configured model and runtime credentials with Hermes helpers.
- Make the handler, not the agent, own delivery.
- Deliver through `tools.send_message_tool.send_message_tool` in-process.
- Treat only exact silence tokens as silent.
- Use an explicit target or a configured home channel; startup precedes initial channel-directory construction.
- Mirroring only appends to an existing Session and never creates one.
- Never use `_gateway_runner_ref`, mutate session storage directly, expose secrets, or send external test messages without approval.
```

Include complete example shapes for `BOOT.md`, `HOOK.yaml`, and `handler.py`. The handler example must parse the JSON tool result, log `mirrored`, catch exceptions, bound iterations, and avoid duplicate delivery.

- [ ] **Step 2: Replace the generated SKILL.md**

Use frontmatter containing only:

```yaml
---
name: create-hermes-boot-hook
description: Create or update customized Hermes Agent BOOT.md startup checklists and gateway:startup hooks, including HOOK.yaml and handler.py, with correct one-shot agent execution, deterministic delivery, silence handling, validation, and Session-mirroring boundaries. Use when a user asks to run checks, reports, alerts, maintenance, or other agent work whenever the Hermes Gateway starts or restarts.
---
```

The body must direct the consuming agent to read `references/hermes-boot-hooks.md`, inspect existing files, collect only missing requirements, generate the three runtime files, validate them, and avoid restarting or externally messaging without authorization.

- [ ] **Step 3: Scan for forbidden architecture drift**

Run:

```bash
rg -n '_gateway_runner_ref|context.*session_store|mirror_to_session.*create|hermes send' create-hermes-boot-hook
```

Expected: forbidden APIs appear only in explicit “do not use” guidance; `hermes send` is described only as a non-preferred subprocess wrapper.

- [ ] **Step 4: Commit the skill content**

```bash
git add create-hermes-boot-hook
git commit -m "feat: add Hermes boot hook workflow"
```

### Task 3: Validate structure and runtime templates

**Files:**
- Modify if needed: `create-hermes-boot-hook/SKILL.md`
- Modify if needed: `create-hermes-boot-hook/references/hermes-boot-hooks.md`
- Modify if needed: `create-hermes-boot-hook/agents/openai.yaml`

- [ ] **Step 1: Run skill-creator validation**

Run:

```bash
python /Users/nb-colin/.codex/skills/.system/skill-creator/scripts/quick_validate.py create-hermes-boot-hook
```

Expected: validation succeeds.

- [ ] **Step 2: Check structural constraints**

Run:

```bash
find create-hermes-boot-hook -maxdepth 3 -type f -print | sort
```

Expected: exactly `SKILL.md`, `agents/openai.yaml`, and `references/hermes-boot-hooks.md`.

- [ ] **Step 3: Extract and validate the documented handler example**

Copy the reference example into `.e2e/generated-boot-hook/handler.py`, substitute a synthetic target, and run:

```bash
python -m py_compile .e2e/generated-boot-hook/handler.py
python -c 'import yaml; yaml.safe_load(open(".e2e/generated-boot-hook/HOOK.yaml"))'
```

Expected: both commands exit 0.

- [ ] **Step 4: Verify delivery behavior in the isolated container**

Run the documented handler delivery helper with a mocked `_send_to_platform` for two cases:

```text
existing synthetic Session → success=true, mirrored=true, transcript contains final response
missing synthetic Session  → success=true, mirrored absent/false
```

Expected: behavior matches both lines and no real external message is sent.

- [ ] **Step 5: Run placeholder and secret scans**

Run:

```bash
rg -n 'TODO|TBD|PLACEHOLDER|access_token|refresh_token|api_key' create-hermes-boot-hook
```

Expected: no placeholders or embedded credentials; generic warnings about secrets are allowed.

- [ ] **Step 6: Commit validation fixes if any**

```bash
git add create-hermes-boot-hook
git commit -m "test: validate Hermes boot hook skill"
```
