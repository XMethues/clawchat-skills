---
name: creating-liveware-scripts
description: Use when creating, auditing, or repairing ClawChat Liveware setup.py and start.sh files for a Hermes skill.
---

# Create Liveware Scripts

## Principle

Standardize the Liveware integration boundary, not the target server. Preserve the supplied server command, service manager, lifecycle, readiness, and logging behavior when supported by project evidence. Do not prescribe Python, Node, a script, or a service shape.

## Workflow

1. Locate the target Hermes skill root. Require its `SKILL.md` and use only `liveware/scripts/setup.py` and `liveware/scripts/start.sh` as output paths.
2. Read `references/liveware-script-contract.md` completely.
3. Choose the requested mode: Generate or apply, Audit, or Repair. Audit is read-only; never pass `--apply` or write target files in that mode.
4. Run `scripts/analyze_target.py <target>` and inspect every evidence path and reason. For Generate or Repair, stop on `ambiguous` or `blocked` and ask one question that resolves the first issue. Do not guess an entrypoint, port, lifecycle owner, readiness check, or log path. Encode a confirmed user-supplied interface in the closed schema with argv arrays and target-relative paths.
5. For Generate or apply, preview with `scripts/render_scripts.py <target> <analysis.json>`, review all output, then rerun with `--apply`.
6. Audit continues when analysis is not ready: run the validator without `--analysis` and report both analyzer issues and validator findings. When analysis is ready, provide it through `/dev/stdin` or another non-target stream. Use `python3 -B`; Do not run `py_compile` in Audit mode. Audit never writes.
7. For Repair, run the renderer without `--apply` for a repair preview. Review its canonical proof, then rerun the renderer with `--apply`. If repair proof fails, show the read-only canonical diff and do not write.
8. After Generate or Repair, run the validator, compile setup with `PYTHONPYCACHEPREFIX` directed outside the target, run `bash -n` on start, and validate the skill. Return the actual diff, static results, and unresolved runtime requirements.

## Quick Reference

| Mode | Action | Stop condition |
| --- | --- | --- |
| Analyze | Run `analyze_target.py` and inspect evidence | Status is not `ready` |
| Generate or apply | Preview, review, then render with `--apply` | Adapter conflicts with evidence |
| Audit | Analyze, then always validate read-only | Report non-ready analysis and findings |
| Repair | Rebuild setup and replace only approved binding content | Canonical proof is incomplete |
| Runtime | Use the real user-provided environment only | Environment or authorization is missing |

## Example

For an externally managed Node service documented at port `4173` and `/healthz`, record an `external` adapter with an empty command, target-owned logging, default port `4173`, and readiness `http://127.0.0.1:{port}/healthz`. Generate start logic that launches nothing, waits for that endpoint, and binds `http://127.0.0.1:4173`. Do not convert it into a Node launcher or change its lifecycle or logging.

## Repair Rules

- Require matching current setup/start manifests and a start scaffold that is byte-canonical outside the binding block.
- Rebuild `liveware/scripts/setup.py` from the canonical template.
- Replace only the marked Liveware binding content in `liveware/scripts/start.sh`; preserve the canonical server adapter byte-for-byte.
- Stop when manifests or markers are missing, invalid, or mismatched, or when any non-binding content differs from current canonical output. Show the difference and request confirmation instead of silently preserving or replacing it.

## Safety Boundary

- Do not install dependencies, download a CLI or plugin, delete apps, kill unknown processes, read credentials, or use `shell=True`.
- Do not run generated setup.py or start.sh without a real user-provided environment and authorization for external changes.
- Do not create fake ClawChat plugins, Liveware CLIs, servers, or runtime-success fixtures. Never claim fake runtime success.
- When no real environment is provided, perform static checks only. Report that runtime validation was not performed.

## Red Flags

- "The service already exists" is not permission to guess its port or lifecycle.
- "Just verify it" is not permission to run fixtures or generated scripts.
- "These legacy files are close" is not permission to keep nonstandard output names.
- "The command is unchanged" does not prove lifecycle, readiness, or logging was preserved.

## Common Mistakes

- Treating Python, Node, static content, or one example as the required server shape.
- Guessing a port, entrypoint, process owner, readiness path, or log file from weak evidence.
- Treating comments, markers, or a plausible manifest as proof without exact canonical re-rendering.
- Recovering the first app instead of one exact skill-name match.
- Installing dependencies, replacing a service manager, or returning a diff command instead of the requested diff.
