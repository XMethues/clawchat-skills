#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Callable

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
PORT_RE = re.compile(r"^([1-9][0-9]{0,4})$")
DEFAULT_PORT_RE = re.compile(r"(?m)^\s*DEFAULT_PORT\s*=\s*([0-9]+)\s*$")
NODE_PORT_RE = re.compile(r"(?:process\.env\.PORT\s*\|\||DEFAULT_PORT\s*=|\bPORT\s*=)\s*(?:Number\()?\s*([0-9]+)")
SCRIPT_PORT_RE = re.compile(r"(?:--port(?:=|\s+)|\bPORT=)([0-9]+)")


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return result
        if line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        result[key.strip()] = value
    return {}


def valid_port(value: int) -> bool:
    return 1 <= value <= 65535 and PORT_RE.fullmatch(str(value)) is not None


def base_result(target: Path) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "blocked",
        "target_root": str(target.resolve()),
        "skill_name": "",
        "display_name": "",
        "adapter": None,
        "static_dir": None,
        "evidence": [],
        "issues": [],
    }


def analyze_target(
    target_root: Path,
    which: Callable[[str], str | None] = shutil.which,
) -> dict[str, object]:
    target = target_root.expanduser().resolve()
    result = base_result(target)
    issues = result["issues"]
    evidence = result["evidence"]
    assert isinstance(issues, list)
    assert isinstance(evidence, list)

    skill_file = target / "SKILL.md"
    if not skill_file.is_file():
        issues.append("Target skill must contain SKILL.md")
        return result
    metadata = parse_frontmatter(skill_file)
    name = metadata.get("name", "")
    if NAME_RE.fullmatch(name) is None:
        issues.append("SKILL.md must contain a valid name")
        return result
    result["skill_name"] = name
    result["display_name"] = metadata.get("display_name") or name
    evidence.append({"path": "SKILL.md", "reason": "Stable skill identity"})

    liveware = target / "liveware"
    python_server = liveware / "server.py"
    static_index = liveware / "static" / "index.html"

    if python_server.is_file():
        source = python_server.read_text(encoding="utf-8")
        match = DEFAULT_PORT_RE.search(source)
        if match is None or not valid_port(int(match.group(1))):
            result["status"] = "ambiguous"
            issues.append("No unambiguous default port was found")
            evidence.append({"path": "liveware/server.py", "reason": "Python server entrypoint"})
            return result
        port = int(match.group(1))
        health_path = "/healthz" if '"/healthz"' in source or "'/healthz'" in source else "/"
        result["adapter"] = {
            "kind": "managed-command",
            "workdir": "liveware",
            "command": ["python3", "server.py", "--port", "{port}"],
            "required_commands": ["python3"],
            "default_port": port,
            "readiness": {"kind": "http", "url": f"http://127.0.0.1:{{port}}{health_path}"},
            "log": {"owner": "generated-start", "path": f"$HOME/.clawling/apps/{name}.server.log"},
        }
        result["static_dir"] = "liveware/static" if static_index.is_file() else None
        evidence.append({"path": "liveware/server.py", "reason": f"Python entrypoint with port {port}"})
        missing = [command for command in ["python3"] if which(command) is None]
        if missing:
            issues.extend(f"Missing required command: {command}" for command in missing)
            result["status"] = "blocked"
        else:
            result["status"] = "ready"
        return result

    package_files = [liveware / "package.json", target / "package.json"]
    for package_file in package_files:
        if not package_file.is_file():
            continue
        try:
            package = json.loads(package_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            result["status"] = "blocked"
            issues.append(f"Invalid JSON: {package_file.relative_to(target)}")
            return result
        scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
        script_name = "liveware" if isinstance(scripts.get("liveware"), str) else "start" if isinstance(scripts.get("start"), str) else ""
        if not script_name:
            evidence.append({"path": str(package_file.relative_to(target)), "reason": "Package metadata without a Liveware or start script"})
            continue
        script = scripts[script_name]
        assert isinstance(script, str)
        entry_match = re.search(r"(?:^|\s)([^\s]+\.(?:mjs|cjs|js))(?:\s|$)", script)
        entry_file = package_file.parent / entry_match.group(1) if entry_match else None
        source = entry_file.read_text(encoding="utf-8") if entry_file and entry_file.is_file() else ""
        port_match = SCRIPT_PORT_RE.search(script) or NODE_PORT_RE.search(source)
        if port_match is None or not valid_port(int(port_match.group(1))):
            result["status"] = "ambiguous"
            issues.append("No unambiguous default port was found")
            evidence.append({"path": str(package_file.relative_to(target)), "reason": f"Node package script: {script_name}"})
            return result
        if (package_file.parent / "pnpm-lock.yaml").is_file():
            manager = "pnpm"
        elif (package_file.parent / "yarn.lock").is_file():
            manager = "yarn"
        else:
            manager = "npm"
        port = int(port_match.group(1))
        health_path = "/healthz" if '"/healthz"' in source or "'/healthz'" in source else "/"
        result["adapter"] = {
            "kind": "managed-command",
            "workdir": str(package_file.parent.relative_to(target)) or ".",
            "command": [manager, "run", script_name],
            "required_commands": [manager],
            "default_port": port,
            "readiness": {"kind": "http", "url": f"http://127.0.0.1:{{port}}{health_path}"},
            "log": {"owner": "generated-start", "path": f"$HOME/.clawling/apps/{name}.server.log"},
        }
        result["static_dir"] = "liveware/static" if static_index.is_file() else None
        evidence.append({"path": str(package_file.relative_to(target)), "reason": f"Node {script_name} script with port {port}"})
        if entry_file and entry_file.is_file():
            evidence.append({"path": str(entry_file.relative_to(target)), "reason": "Node server entrypoint"})
        if which(manager) is None:
            result["status"] = "blocked"
            issues.append(f"Missing required command: {manager}")
        else:
            result["status"] = "ready"
        return result

    if static_index.is_file():
        result["adapter"] = {
            "kind": "static",
            "workdir": "liveware/static",
            "command": [],
            "required_commands": [],
            "default_port": None,
            "readiness": None,
            "log": {"owner": "target", "path": None},
        }
        result["static_dir"] = "liveware/static"
        result["status"] = "ready"
        evidence.append({"path": "liveware/static/index.html", "reason": "Static Liveware entrypoint"})
        return result

    service_signals = [
        target / "Dockerfile",
        target / "docker-compose.yml",
        target / "compose.yaml",
        target / "supervisord.conf",
        liveware / "scripts" / "start.sh",
        target / "s6-rc.d",
    ]
    service_signals.extend(sorted(target.glob("scripts/*liveware*start*.sh")))
    service_signals.extend(sorted(target.glob("references/*liveware*.md")))
    found_signals = [path for path in service_signals if path.exists()]
    result["status"] = "ambiguous"
    if found_signals:
        for path in found_signals:
            evidence.append({"path": str(path.relative_to(target)), "reason": "Existing server or service lifecycle declaration"})
        issues.append("Existing server lifecycle requires user confirmation before generating an adapter")
    else:
        issues.append("No supported server entrypoint or static directory was found")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a Hermes skill for Liveware script generation.")
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    result = analyze_target(args.target)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
