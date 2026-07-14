#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Callable

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
PORT_RE = re.compile(r"^([1-9][0-9]{0,4})$")
DEFAULT_PORT_RE = re.compile(r"(?m)^\s*DEFAULT_PORT\s*=\s*([0-9]+)\s*$")
SCRIPT_PORT_RE = re.compile(r"(?:--port(?:=|\s+)|\bPORT=)([0-9]+)")
NODE_ENV_PORT_DEFAULT_RE = re.compile(
    r"\b(?:const|let|var)\s+(?:port|[A-Za-z_$][A-Za-z0-9_$]*port[A-Za-z0-9_$]*)\s*=\s*"
    r"(?:Number\s*\(\s*)?process\s*\.\s*env\s*\.\s*PORT\s*(?:\|\||\?\?)\s*([0-9]+)",
    re.IGNORECASE,
)
PORT_ENV_EVIDENCE_REASON = "Command consumes exported PORT environment variable"
REFERENCE_LIFECYCLE_PATTERNS = (
    re.compile(
        r"\b(?:service\s+|server\s+|process\s+)?lifecycle\b.{0,100}"
        r"\b(?:owned|managed|controlled|started|launched|run)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:owned|managed|controlled)\s+by\b.{0,80}"
        r"\b(?:docker\s+compose|supervisord?|systemd|s6|service manager|launcher)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:use|run|start|launch|invoke)\b.{0,80}"
        r"\b(?:docker\s+compose|supervisord?|systemd|s6|scripts?/[^\s`]+)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:docker\s+compose|supervisord?|systemd|s6|service manager|launcher)\b"
        r".{0,80}\b(?:owns?|manages?|controls?|starts?|launches?|runs?)\b"
        r".{0,80}\b(?:service|server|process|lifecycle)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:service|server|process|lifecycle)\b.{0,50}"
        r"\b(?:is\s+)?(?:owned|managed|controlled|started|launched|runs?)\s+"
        r"(?:by|with|under|through|via)\s+"
        r"(?:docker\s+compose|supervisord?|systemd|s6|service manager|launcher)\b",
        re.IGNORECASE | re.DOTALL,
    ),
)
SCRIPT_LIFECYCLE_PATTERNS = (
    re.compile(
        r"(?m)^\s*(?:exec|nohup)\s+[^\n]*(?:liveware|server|service|serve|uvicorn|gunicorn)"
    ),
    re.compile(r"\b(?:liveware|server|service)[A-Za-z0-9_.-]*\.(?:run|start|serve|listen)\s*\("),
    re.compile(r"\b(?:npm|pnpm|yarn)\s+run\s+[^\n]*(?:liveware|server|serve)\b"),
    re.compile(r"\b(?:docker\s+compose|supervisord?|systemctl|s6-svscan)\b"),
)


def javascript_code_only(source: str) -> str:
    output: list[str] = []
    index = 0
    state = "code"
    quote = ""
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "code":
            if character == "/" and following == "/":
                output.extend((" ", " "))
                index += 2
                state = "line-comment"
                continue
            if character == "/" and following == "*":
                output.extend((" ", " "))
                index += 2
                state = "block-comment"
                continue
            if character in {"'", '"', "`"}:
                output.append(" ")
                quote = character
                state = "string"
                index += 1
                continue
            output.append(character)
            index += 1
            continue
        if state == "line-comment":
            output.append("\n" if character == "\n" else " ")
            index += 1
            if character == "\n":
                state = "code"
            continue
        if state == "block-comment":
            if character == "*" and following == "/":
                output.extend((" ", " "))
                index += 2
                state = "code"
            else:
                output.append("\n" if character == "\n" else " ")
                index += 1
            continue
        if character == "\\" and following:
            output.extend((" ", "\n" if following == "\n" else " "))
            index += 2
        else:
            output.append("\n" if character == "\n" else " ")
            index += 1
            if character == quote:
                state = "code"
    return "".join(output)


def reference_declares_lifecycle(text: str) -> bool:
    return any(pattern.search(text) is not None for pattern in REFERENCE_LIFECYCLE_PATTERNS)


def script_declares_lifecycle(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return any(pattern.search(text) is not None for pattern in SCRIPT_LIFECYCLE_PATTERNS)


@lru_cache(maxsize=1)
def load_renderer() -> ModuleType:
    path = Path(__file__).resolve().with_name("render_scripts.py")
    spec = importlib.util.spec_from_file_location(
        "creating_liveware_scripts_analyzer_renderer",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load renderer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_exact_canonical_generated_start(path: Path, target: Path, skill_name: str) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    try:
        text = path.read_text(encoding="utf-8")
        renderer = load_renderer()
        analysis = renderer.extract_analysis_manifest(text)
        if analysis.get("target_root") != str(target) or analysis.get("skill_name") != skill_name:
            return False
        return renderer.render_start(analysis) == text
    except (OSError, UnicodeError, RuntimeError, ValueError):
        return False


def lifecycle_signals(target: Path, liveware: Path, skill_name: str) -> list[Path]:
    start = liveware / "scripts" / "start.sh"
    paths = [
        target / "Dockerfile",
        target / "docker-compose.yml",
        target / "docker-compose.yaml",
        target / "compose.yml",
        target / "compose.yaml",
        target / "supervisord.conf",
        target / "supervisor.conf",
        target / "s6",
        target / "s6-rc.d",
    ]
    if not is_exact_canonical_generated_start(start, target, skill_name):
        paths.append(start)
    paths.extend(sorted(target.glob("scripts/*liveware*start*.sh")))
    paths.extend(sorted(target.glob("scripts/*start*liveware*.sh")))
    scripts = target / "scripts"
    if scripts.is_dir() and not scripts.is_symlink():
        for path in sorted(scripts.iterdir()):
            if (
                path.is_file()
                and not path.is_symlink()
                and path.suffix in {".sh", ".py", ".js", ".mjs", ".cjs"}
                and script_declares_lifecycle(path)
            ):
                paths.append(path)

    references = target / "references"
    if references.is_dir() and not references.is_symlink():
        for path in sorted(references.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            try:
                declared_signal = reference_declares_lifecycle(
                    path.read_text(encoding="utf-8")
                )
            except (OSError, UnicodeError):
                declared_signal = False
            if declared_signal:
                paths.append(path)

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path.exists() and path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def automatic_candidate_evidence(
    target: Path,
    python_server: Path,
    package_files: list[Path],
    static_index: Path,
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    if python_server.is_file():
        candidates.append(
            {"path": str(python_server.relative_to(target)), "reason": "Automatic Python server candidate"}
        )
    for package_file in package_files:
        if package_file.is_file():
            candidates.append(
                {"path": str(package_file.relative_to(target)), "reason": "Automatic Node package candidate"}
            )
    if static_index.is_file():
        candidates.append(
            {"path": str(static_index.relative_to(target)), "reason": "Automatic static content candidate"}
        )
    return candidates


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
    package_files = [liveware / "package.json", target / "package.json"]

    found_signals = lifecycle_signals(target, liveware, name)
    if found_signals:
        result["status"] = "ambiguous"
        for path in found_signals:
            evidence.append(
                {
                    "path": str(path.relative_to(target)),
                    "reason": "Existing server or service lifecycle declaration",
                }
            )
        evidence.extend(
            automatic_candidate_evidence(
                target,
                python_server,
                package_files,
                static_index,
            )
        )
        issues.append("Existing server lifecycle requires user confirmation before generating an adapter")
        return result

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
        script_port_match = SCRIPT_PORT_RE.search(script)
        source_port_match = NODE_ENV_PORT_DEFAULT_RE.search(javascript_code_only(source))
        port_match = source_port_match or script_port_match
        if port_match is None or not valid_port(int(port_match.group(1))):
            result["status"] = "ambiguous"
            issues.append("No unambiguous default port was found")
            evidence.append({"path": str(package_file.relative_to(target)), "reason": f"Node package script: {script_name}"})
            return result
        if script_port_match is not None or source_port_match is None:
            result["status"] = "ambiguous"
            issues.append("Node command does not prove that it consumes exported PORT")
            evidence.append(
                {
                    "path": str(package_file.relative_to(target)),
                    "reason": f"Node package script requires exported PORT confirmation: {script_name}",
                }
            )
            if entry_file and entry_file.is_file():
                evidence.append(
                    {"path": str(entry_file.relative_to(target)), "reason": "Node server entrypoint"}
                )
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
            evidence.append(
                {"path": str(entry_file.relative_to(target)), "reason": PORT_ENV_EVIDENCE_REASON}
            )
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

    result["status"] = "ambiguous"
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
