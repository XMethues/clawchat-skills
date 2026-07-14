from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

from tests.creating_liveware_scripts.helpers import REPO_ROOT, load_skill_script, write_target


class AnalyzeTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_skill_script("analyze_target")
        cls.renderer = load_skill_script("render_scripts")

    def write_python_candidate(self, target: Path) -> None:
        liveware = target / "liveware"
        liveware.mkdir(exist_ok=True)
        (liveware / "server.py").write_text(
            'DEFAULT_PORT = 5080\nROUTES = ["/healthz"]\n',
            encoding="utf-8",
        )

    def write_node_candidate(self, target: Path) -> None:
        liveware = target / "liveware"
        liveware.mkdir(exist_ok=True)
        (liveware / "package.json").write_text(
            json.dumps({"scripts": {"liveware": "node server.js"}}),
            encoding="utf-8",
        )
        (liveware / "server.js").write_text(
            'const port = Number(process.env.PORT || 4173);\nconst health = "/healthz";\n',
            encoding="utf-8",
        )

    def write_static_candidate(self, target: Path) -> None:
        static = target / "liveware" / "static"
        static.mkdir(parents=True, exist_ok=True)
        (static / "index.html").write_text("<!doctype html>", encoding="utf-8")

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
        self.assertEqual(result["target_root"], str(target.resolve()))
        self.assertFalse(result["target_root"].startswith("//"))
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
        self.assertIn(
            {
                "path": "liveware/server.js",
                "reason": "Command consumes exported PORT environment variable",
            },
            result["evidence"],
        )

    def test_node_hardcoded_port_is_ambiguous_without_exported_port_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = write_target(Path(tmp))
            liveware = target / "liveware"
            liveware.mkdir()
            (liveware / "package.json").write_text(
                json.dumps({"scripts": {"liveware": "node server.js --port 4173"}}),
                encoding="utf-8",
            )
            (liveware / "server.js").write_text(
                "const port = 4173;\n",
                encoding="utf-8",
            )
            result = self.module.analyze_target(
                target,
                which=lambda command: f"/bin/{command}",
            )
        self.assertEqual(result["status"], "ambiguous")
        self.assertIsNone(result["adapter"])
        self.assertIn("exported PORT", result["issues"][-1])

    def test_node_port_proof_ignores_comments_strings_and_unrelated_reads(self) -> None:
        sources = (
            "const PORT = 4173; // process.env.PORT || 4173 is ignored\nserver.listen(PORT);\n",
            'const note = "process.env.PORT || 4173";\nconst PORT = 4173;\nserver.listen(PORT);\n',
            "console.log(process.env.PORT);\nconst PORT = 4173;\nserver.listen(PORT);\n",
        )
        for source in sources:
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                target = write_target(Path(tmp))
                liveware = target / "liveware"
                liveware.mkdir()
                (liveware / "package.json").write_text(
                    json.dumps({"scripts": {"liveware": "node server.js"}}),
                    encoding="utf-8",
                )
                (liveware / "server.js").write_text(source, encoding="utf-8")
                result = self.module.analyze_target(
                    target,
                    which=lambda command: f"/bin/{command}",
                )
            self.assertEqual(result["status"], "ambiguous")
            self.assertIsNone(result["adapter"])

    def test_reports_service_manager_evidence_without_inventing_a_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = write_target(Path(tmp))
            (target / "supervisord.conf").write_text("[program:sample]\ncommand=node server.js\n", encoding="utf-8")
            result = self.module.analyze_target(target, which=lambda command: f"/bin/{command}")
        self.assertEqual(result["status"], "ambiguous")
        self.assertIsNone(result["adapter"])
        self.assertEqual(result["evidence"][-1]["path"], "supervisord.conf")
        self.assertIn("requires user confirmation", result["issues"][-1])

    def test_existing_lifecycle_evidence_precedes_every_automatic_candidate(self) -> None:
        cases = (
            (
                "python-start",
                self.write_python_candidate,
                lambda target: (
                    (target / "liveware" / "scripts").mkdir(parents=True),
                    (target / "liveware" / "scripts" / "start.sh").write_text(
                        "#!/usr/bin/env bash\nnohup python3 server.py &\n",
                        encoding="utf-8",
                    ),
                ),
                "liveware/scripts/start.sh",
            ),
            (
                "node-docker",
                self.write_node_candidate,
                lambda target: (target / "Dockerfile").write_text(
                    "CMD [\"npm\", \"run\", \"liveware\"]\n",
                    encoding="utf-8",
                ),
                "Dockerfile",
            ),
            (
                "static-supervisor",
                self.write_static_candidate,
                lambda target: (target / "supervisord.conf").write_text(
                    "[program:liveware]\ncommand=serve liveware/static\n",
                    encoding="utf-8",
                ),
                "supervisord.conf",
            ),
        )
        for name, write_candidate, write_signal, signal_path in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                target = write_target(Path(tmp))
                write_candidate(target)
                write_signal(target)
                result = self.module.analyze_target(
                    target,
                    which=lambda command: f"/bin/{command}",
                )
            self.assertEqual(result["status"], "ambiguous")
            self.assertIsNone(result["adapter"])
            paths = {item["path"] for item in result["evidence"]}
            self.assertIn(signal_path, paths)
            self.assertTrue(
                any("candidate" in item["reason"].lower() for item in result["evidence"]),
                result["evidence"],
            )

    def test_all_supported_lifecycle_signal_shapes_block_automatic_detection(self) -> None:
        signal_writers = {
            "compose.yaml": lambda target: (target / "compose.yaml").write_text(
                "services:\n  app:\n    image: sample\n", encoding="utf-8"
            ),
            "s6-rc.d": lambda target: (target / "s6-rc.d").mkdir(),
            "scripts/start-liveware-service.sh": lambda target: (
                (target / "scripts").mkdir(),
                (target / "scripts" / "start-liveware-service.sh").write_text(
                    "#!/usr/bin/env bash\nexec sample-service\n", encoding="utf-8"
                ),
            ),
            "references/runtime.md": lambda target: (
                (target / "references").mkdir(),
                (target / "references" / "runtime.md").write_text(
                    "The service lifecycle is owned by the deployment supervisor.\n",
                    encoding="utf-8",
                ),
            ),
        }
        for signal_path, write_signal in signal_writers.items():
            with self.subTest(signal=signal_path), tempfile.TemporaryDirectory() as tmp:
                target = write_target(Path(tmp))
                self.write_static_candidate(target)
                write_signal(target)
                result = self.module.analyze_target(target)
            self.assertEqual(result["status"], "ambiguous")
            self.assertIn(signal_path, {item["path"] for item in result["evidence"]})

    def test_generic_and_non_shell_lifecycle_launchers_block_static_detection(self) -> None:
        launchers = {
            "scripts/start.sh": "#!/usr/bin/env bash\nexec liveware-server\n",
            "scripts/run-liveware.py": "import liveware_server\nliveware_server.run()\n",
        }
        for launcher, content in launchers.items():
            with self.subTest(launcher=launcher), tempfile.TemporaryDirectory() as tmp:
                target = write_target(Path(tmp))
                self.write_static_candidate(target)
                scripts = target / "scripts"
                scripts.mkdir()
                (target / launcher).write_text(content, encoding="utf-8")
                result = self.module.analyze_target(target)
            self.assertEqual(result["status"], "ambiguous")
            self.assertIn(launcher, {item["path"] for item in result["evidence"]})

    def test_harmless_script_names_do_not_count_as_lifecycle_evidence(self) -> None:
        scripts = {
            "scripts/restart-tests.sh": "#!/usr/bin/env bash\nprintf 'tests only\\n'\n",
            "scripts/test-liveware.py": "print('schema test only')\n",
            "scripts/liveware-lint.js": "console.log('lint only');\n",
        }
        for script, content in scripts.items():
            with self.subTest(script=script), tempfile.TemporaryDirectory() as tmp:
                target = write_target(Path(tmp))
                self.write_static_candidate(target)
                directory = target / "scripts"
                directory.mkdir()
                (target / script).write_text(content, encoding="utf-8")
                result = self.module.analyze_target(target)
            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["adapter"]["kind"], "static")

    def test_reference_filename_without_lifecycle_declaration_does_not_block(self) -> None:
        texts = (
            "# Product notes\nThis page describes visible UI labels only.\n",
            "The Docker SDK client is available through the API.\n",
            "The Start command is displayed in the menu.\n",
        )
        for text in texts:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                target = write_target(Path(tmp))
                self.write_static_candidate(target)
                references = target / "references"
                references.mkdir()
                (references / "service.md").write_text(text, encoding="utf-8")
                result = self.module.analyze_target(target)
            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["adapter"]["kind"], "static")

    def test_common_reference_lifecycle_ownership_phrases_are_detected(self) -> None:
        declarations = (
            "systemd owns the service lifecycle.\n",
            "The server is managed with systemd.\n",
            "The service runs under supervisor.\n",
        )
        for declaration in declarations:
            with self.subTest(declaration=declaration), tempfile.TemporaryDirectory() as tmp:
                target = write_target(Path(tmp))
                self.write_static_candidate(target)
                references = target / "references"
                references.mkdir()
                (references / "runtime.md").write_text(declaration, encoding="utf-8")
                result = self.module.analyze_target(target)
            self.assertEqual(result["status"], "ambiguous")
            self.assertIn(
                "references/runtime.md",
                {item["path"] for item in result["evidence"]},
            )

    def test_exact_canonical_generated_start_is_not_lifecycle_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = write_target(Path(tmp))
            self.write_python_candidate(target)
            first = self.module.analyze_target(
                target,
                which=lambda command: f"/bin/{command}",
            )
            scripts = target / "liveware" / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "start.sh").write_text(
                self.renderer.render_start(first),
                encoding="utf-8",
            )
            second = self.module.analyze_target(
                target,
                which=lambda command: f"/bin/{command}",
            )
        self.assertEqual(first["status"], "ready")
        self.assertEqual(second, first)

    def test_plausible_or_tampered_generated_markers_do_not_hide_a_launcher(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = write_target(Path(tmp))
            self.write_python_candidate(target)
            analysis = self.module.analyze_target(
                target,
                which=lambda command: f"/bin/{command}",
            )
            scripts = target / "liveware" / "scripts"
            scripts.mkdir(parents=True)
            canonical = self.renderer.render_start(analysis)
            (scripts / "start.sh").write_text(
                canonical.replace("SERVER_COMMAND=(python3", "SERVER_COMMAND=(nohup python3", 1),
                encoding="utf-8",
            )
            result = self.module.analyze_target(
                target,
                which=lambda command: f"/bin/{command}",
            )
        self.assertEqual(result["status"], "ambiguous")
        self.assertIn(
            "liveware/scripts/start.sh",
            {item["path"] for item in result["evidence"]},
        )

    def test_real_tarot_launcher_prevents_automatic_python_replacement(self) -> None:
        target = REPO_ROOT / "creative" / "tarot-arcana"
        result = self.module.analyze_target(
            target,
            which=lambda command: f"/bin/{command}",
        )
        self.assertEqual(result["status"], "ambiguous")
        self.assertIsNone(result["adapter"])
        self.assertIn(
            "liveware/scripts/start.sh",
            {item["path"] for item in result["evidence"]},
        )

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
