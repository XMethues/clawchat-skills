from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "creating-liveware-scripts"


def load_skill_script(name: str) -> ModuleType:
    path = SKILL_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"creating_liveware_scripts_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_target(root: Path, *, name: str = "sample-skill", display_name: str | None = None) -> Path:
    target = root / name
    target.mkdir(parents=True)
    display = f"display_name: {display_name}\n" if display_name is not None else ""
    (target / "SKILL.md").write_text(
        f"---\nname: {name}\n{display}description: Sample Hermes skill.\n---\n\n# Sample\n",
        encoding="utf-8",
    )
    return target
