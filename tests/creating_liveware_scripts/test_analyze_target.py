from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

from tests.creating_liveware_scripts.helpers import load_skill_script, write_target


class AnalyzeTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_skill_script("analyze_target")

    def test_detects_python_server_and_preserves_display_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = write_target(Path(tmp), display_name="塔罗入口")
            liveware = target / "liveware"
            liveware.mkdir()
            (liveware / "server.py").write_text(
                'DEFAULT_PORT = 5080\nROUTES = ["/healthz"]\n', encoding="utf-8"
            )
            result = self.module.analyze_target(target, which=lambda command: f"/bin/{command}")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["skill_name"], "sample-skill")
        self.assertEqual(result["display_name"], "塔罗入口")
        self.assertEqual(result["adapter"]["kind"], "managed-command")
        self.assertEqual(result["adapter"]["command"], ["python3", "server.py", "--port", "{port}"])
        self.assertEqual(result["adapter"]["default_port"], 5080)
        self.assertEqual(result["adapter"]["readiness"]["url"], "http://127.0.0.1:{port}/healthz")

    def test_detects_static_directory_without_creating_a_server(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = write_target(Path(tmp))
            static = target / "liveware" / "static"
            static.mkdir(parents=True)
            (static / "index.html").write_text("<!doctype html>", encoding="utf-8")
            result = self.module.analyze_target(target, which=lambda command: f"/bin/{command}")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["adapter"]["kind"], "static")
        self.assertEqual(result["static_dir"], "liveware/static")
        self.assertEqual(result["adapter"]["command"], [])

    def test_detects_node_service_and_declared_package_manager(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = write_target(Path(tmp))
            liveware = target / "liveware"
            liveware.mkdir()
            (liveware / "package.json").write_text(
                json.dumps({"scripts": {"liveware": "node server.js"}}), encoding="utf-8"
            )
            (liveware / "package-lock.json").write_text("{}\n", encoding="utf-8")
            (liveware / "server.js").write_text(
                'const port = Number(process.env.PORT || 4173);\nconst health = "/healthz";\n',
                encoding="utf-8",
            )
            result = self.module.analyze_target(target, which=lambda command: f"/bin/{command}")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["adapter"]["kind"], "managed-command")
        self.assertEqual(result["adapter"]["command"], ["npm", "run", "liveware"])
        self.assertEqual(result["adapter"]["required_commands"], ["npm"])
        self.assertEqual(result["adapter"]["default_port"], 4173)

    def test_reports_service_manager_evidence_without_inventing_a_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = write_target(Path(tmp))
            (target / "supervisord.conf").write_text("[program:sample]\ncommand=node server.js\n", encoding="utf-8")
            result = self.module.analyze_target(target, which=lambda command: f"/bin/{command}")
        self.assertEqual(result["status"], "ambiguous")
        self.assertIsNone(result["adapter"])
        self.assertEqual(result["evidence"][-1]["path"], "supervisord.conf")
        self.assertIn("requires user confirmation", result["issues"][-1])

    def test_blocks_when_a_declared_dependency_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = write_target(Path(tmp))
            liveware = target / "liveware"
            liveware.mkdir()
            (liveware / "server.py").write_text("DEFAULT_PORT = 5080\n", encoding="utf-8")
            result = self.module.analyze_target(target, which=lambda command: None)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("Missing required command: python3", result["issues"])

    def test_reports_ambiguous_instead_of_guessing_a_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = write_target(Path(tmp))
            liveware = target / "liveware"
            liveware.mkdir()
            (liveware / "server.py").write_text("print('server')\n", encoding="utf-8")
            result = self.module.analyze_target(target, which=lambda command: f"/bin/{command}")
        self.assertEqual(result["status"], "ambiguous")
        self.assertIn("No unambiguous default port was found", result["issues"])

    def test_blocks_invalid_or_missing_skill_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "broken"
            target.mkdir()
            (target / "SKILL.md").write_text("# Missing frontmatter\n", encoding="utf-8")
            result = self.module.analyze_target(target)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("SKILL.md must contain a valid name", result["issues"])


if __name__ == "__main__":
    unittest.main()
