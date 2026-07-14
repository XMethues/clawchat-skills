#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType


SETUP_PATH = "liveware/scripts/setup.py"
START_PATH = "liveware/scripts/start.sh"
SCRIPTS_PATH = "liveware/scripts"


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    message: str


def add(findings: list[Finding], code: str, path: str, message: str) -> None:
    finding = Finding(code, path, message)
    if finding not in findings:
        findings.append(finding)


_RENDERER: ModuleType | None = None


def load_renderer() -> ModuleType:
    global _RENDERER
    if _RENDERER is None:
        path = Path(__file__).with_name("render_scripts.py")
        spec = importlib.util.spec_from_file_location(
            "creating_liveware_scripts_renderer_for_validation",
            path,
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Renderer could not be loaded.")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _RENDERER = module
    return _RENDERER


def _validate_python_syntax(setup: str, findings: list[Finding]) -> None:
    try:
        ast.parse(setup)
    except SyntaxError as exc:
        add(findings, "LW006", SETUP_PATH, f"Python syntax error: {exc.msg}")


def _setup_diagnostics(setup: str, findings: list[Finding]) -> None:
    standard_root = 'Path.home() / ".clawling" / "apps"' in setup
    standard_file = 'STATE_ROOT / f"{SKILL_NAME}.json"' in setup
    if not (standard_root and standard_file):
        add(findings, "LW002", SETUP_PATH, "Setup does not use per-skill JSON app state.")

    first_app_fallback = (
        "# fallback: first app" in setup.lower()
        or re.search(r"\b(?:apps|items)\s*\[\s*0\s*\]", setup) is not None
    )
    if first_app_fallback:
        add(findings, "LW004", SETUP_PATH, "App recovery can fall back to a non-matching app.")


def _executable_shell_lines(start: str) -> list[str]:
    lines: list[str] = []
    for raw in start.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(("echo ", "printf ")):
            continue
        lines.append(line)
    return lines


def _start_diagnostics(start: str, findings: list[Finding]) -> None:
    standard_assignment = 'STATE_FILE="${HOME}/.clawling/apps/${SKILL_NAME}.json"'
    state_references = start.count("STATE_FILE")
    if start.count(standard_assignment) != 1 or state_references < 2:
        add(findings, "LW003", START_PATH, "Start does not read the standard state file.")

    executable = "\n".join(_executable_shell_lines(start))
    if re.search(r"(?:^|\n)(?:python3?|bash|sh)\b[^\n]*\bsetup\.py\b", executable):
        add(findings, "LW008", START_PATH, "Start invokes setup instead of requiring existing state.")

    unsafe_kill = re.search(
        r"(?:^|[;&|\s])(?:pkill|killall)\b|\bkill\s+(?:-[A-Z0-9]+\s+)?\"?\$\{?EXISTING_PID|\bos\.kill(?:pg)?\s*\(",
        start,
        re.IGNORECASE,
    )
    if unsafe_kill:
        add(findings, "LW010", START_PATH, "Start can terminate a process it cannot prove it owns.")

    renderer = load_renderer()
    try:
        renderer.parse_marker_spans(start)
    except (TypeError, ValueError):
        add(findings, "LW012", START_PATH, "Start has invalid repair-safe block markers.")


def _obvious_cross_script_diagnostics(setup: str, start: str, findings: list[Finding]) -> None:
    combined = setup + "\n" + start
    forbidden = re.search(
        r"\b(?:pip3?|npm|pnpm|yarn)\s+(?:install|add)\b"
        r"|\bpython3?\s+-m\s+pip\s+install\b"
        r"|[\"'](?:pip3?|npm|pnpm|yarn)[\"']\s*,\s*[\"'](?:install|add)[\"']"
        r"|\b(?:curl|wget)\b[^\n|]*\|\s*(?:ba)?sh\b"
        r"|\bliveware\b[^\n]*(?:\bapp\s+(?:delete|remove)\b)",
        combined,
        re.IGNORECASE,
    )
    if forbidden:
        add(
            findings,
            "LW011",
            SCRIPTS_PATH,
            "Scripts contain a forbidden install, download, or app deletion operation.",
        )

    credential = re.search(
        r"(?:os\.environ(?:\.get)?\s*\(|getenv\s*\(|printenv\s+|\$\{?)"
        r"[\"']?(?:[A-Z0-9_]*(?:TOKEN|PASSWORD|PASSWD|SECRET|CREDENTIAL|API_KEY)[A-Z0-9_]*)",
        combined,
        re.IGNORECASE,
    )
    if credential:
        add(findings, "LW015", SCRIPTS_PATH, "Scripts read a credential environment variable directly.")


def _extract_manifest(
    text: str,
    code: str,
    path: str,
    label: str,
    findings: list[Finding],
) -> dict[str, object] | None:
    renderer = load_renderer()
    try:
        return renderer.extract_analysis_manifest(text)
    except (TypeError, ValueError):
        add(
            findings,
            code,
            path,
            f"{label} analysis manifest is missing, invalid, or noncanonical.",
        )
        return None


def _valid_explicit_analysis(analysis: object) -> bool:
    return (
        isinstance(analysis, dict)
        and analysis.get("schema_version") == 1
        and analysis.get("status") == "ready"
        and analysis.get("issues") == []
    )


def _manifest_gate(
    setup: str,
    start: str,
    findings: list[Finding],
    analysis: dict[str, object] | None,
) -> None:
    renderer = load_renderer()
    setup_manifest = _extract_manifest(setup, "LW018", SETUP_PATH, "Setup", findings)
    start_manifest = _extract_manifest(start, "LW019", START_PATH, "Start", findings)

    if setup_manifest is not None and start_manifest is not None and setup_manifest != start_manifest:
        add(findings, "LW018", SETUP_PATH, "Setup and start analysis manifests do not match.")
        add(findings, "LW019", START_PATH, "Setup and start analysis manifests do not match.")

    if analysis is not None:
        if not _valid_explicit_analysis(analysis):
            add(
                findings,
                "LW018",
                "analysis.json",
                "Resolved schema-version-1 analysis with no issues is required.",
            )
        else:
            if setup_manifest is not None and setup_manifest != analysis:
                add(findings, "LW018", SETUP_PATH, "Setup manifest does not match explicit analysis.")
            if start_manifest is not None and start_manifest != analysis:
                add(findings, "LW019", START_PATH, "Start manifest does not match explicit analysis.")

    if setup_manifest is not None:
        try:
            expected_setup = renderer.render_setup(setup_manifest)
        except (KeyError, TypeError, ValueError):
            expected_setup = None
        if setup != expected_setup:
            add(findings, "LW018", SETUP_PATH, "Generated setup does not match analysis.")

    if start_manifest is not None:
        try:
            expected_start = renderer.render_start(start_manifest)
        except (KeyError, TypeError, ValueError):
            expected_start = None
        if start != expected_start:
            add(findings, "LW019", START_PATH, "Generated start or adapter does not match analysis.")


def validate_texts(
    setup: str,
    start: str,
    analysis: dict[str, object] | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    _validate_python_syntax(setup, findings)
    _setup_diagnostics(setup, findings)
    _start_diagnostics(start, findings)
    _obvious_cross_script_diagnostics(setup, start, findings)
    _manifest_gate(setup, start, findings, analysis)
    return findings


def validate_consistency(
    setup: str,
    start: str,
    analysis: dict[str, object],
    findings: list[Finding],
    target: Path | None = None,
) -> None:
    before = validate_texts(setup, start, analysis=analysis)
    for finding in before:
        add(findings, finding.code, finding.path, finding.message)
    if target is not None and _valid_explicit_analysis(analysis):
        try:
            load_renderer().resolve_target_root(analysis, target)
        except (OSError, RuntimeError, TypeError, ValueError):
            add(findings, "LW018", "analysis.json", "Analysis target_root does not match target.")


def validate_target(target: Path, analysis: dict[str, object] | None = None) -> list[Finding]:
    setup_path = target / SETUP_PATH
    start_path = target / START_PATH
    findings: list[Finding] = []
    if not setup_path.is_file():
        add(findings, "LW001", str(setup_path), "Required setup.py is missing.")
    if not start_path.is_file():
        add(findings, "LW005", str(start_path), "Required start.sh is missing.")
    if findings:
        return findings

    setup = setup_path.read_text(encoding="utf-8")
    start = start_path.read_text(encoding="utf-8")
    findings.extend(validate_texts(setup, start, analysis=analysis))
    if analysis is not None and _valid_explicit_analysis(analysis):
        try:
            load_renderer().resolve_target_root(analysis, target)
        except (OSError, RuntimeError, TypeError, ValueError):
            add(findings, "LW018", "analysis.json", "Analysis target_root does not match target.")

    result = subprocess.run(
        ["bash", "-n", str(start_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        add(findings, "LW014", str(start_path), "Bash syntax validation failed.")
    return findings


def print_findings(findings: list[Finding]) -> None:
    print(json.dumps([asdict(item) for item in findings], indent=2, sort_keys=True))


def load_cli_analysis(path: Path) -> tuple[dict[str, object] | None, Finding | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None, Finding("LW018", str(path), "Analysis file could not be read.")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None, Finding("LW018", str(path), "Analysis file is not valid JSON.")
    if not isinstance(payload, dict):
        return None, Finding("LW018", str(path), "Analysis JSON must be an object.")
    return payload, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Statically validate generated Liveware scripts.")
    parser.add_argument("target", type=Path)
    parser.add_argument("--analysis", type=Path)
    args = parser.parse_args()
    analysis = None
    if args.analysis is not None:
        analysis, finding = load_cli_analysis(args.analysis)
        if finding is not None:
            print_findings([finding])
            return 1
    findings = validate_target(args.target.expanduser().resolve(), analysis=analysis)
    print_findings(findings)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
