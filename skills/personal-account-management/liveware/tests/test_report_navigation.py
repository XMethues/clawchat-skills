from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


COMPONENT = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "src"
    / "lib"
    / "components"
    / "AnalysisSection.svelte"
)
SERVE_PATH = Path(__file__).resolve().parents[1] / "serve.py"
SPEC = importlib.util.spec_from_file_location("personal_account_liveware_serve", SERVE_PATH)
assert SPEC is not None and SPEC.loader is not None
SERVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SERVE)


class ReportNavigationTests(unittest.TestCase):
    def test_report_opens_as_a_sveltekit_hash_route(self) -> None:
        source = COMPONENT.read_text(encoding="utf-8")

        self.assertIn('href={`#/reports/${displayedMonth}`}', source)
        self.assertIn('href="#/reports"', source)
        self.assertNotIn('href={analysis.report_url}', source)
        self.assertNotIn('target="_blank"', source)
        self.assertNotIn("window.open", source)

    def test_report_api_lists_and_returns_embeddable_monthly_reports(self) -> None:
        with TemporaryDirectory() as directory:
            book_dir = Path(directory)
            book_path = book_dir / "account-book.json"
            book_path.write_text(
                json.dumps({"schema_version": 3, "profile": {}}),
                encoding="utf-8",
            )
            reports_dir = book_dir / "reports"
            reports_dir.mkdir()
            (reports_dir / "analysis-2026-07.html").write_text(
                '<footer><a href="/reports/">View all monthly reports</a></footer>',
                encoding="utf-8",
            )

            handler = SERVE.Handler(book_path)
            index_status, index_headers, index_body = handler.route(
                "GET",
                "/api/reports",
            )
            self.assertEqual(index_status, 200)
            self.assertEqual(index_headers["Content-Type"], "application/json; charset=utf-8")
            index = json.loads(index_body)
            self.assertEqual([entry["month"] for entry in index["reports"]], ["2026-07"])
            self.assertEqual(index["reports"][0]["file_name"], "analysis-2026-07.html")

            status, headers, body = handler.route("GET", "/api/reports/2026-07")
            self.assertEqual(status, 200)
            self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
            report = json.loads(body)
            self.assertEqual(report["month"], "2026-07")
            self.assertIn("<footer>", report["html"])
            self.assertNotIn('href="/reports/"', report["html"])
            self.assertNotIn("View all monthly reports", report["html"])

            missing_status, _, _ = handler.route("GET", "/api/reports/2026-06")
            self.assertEqual(missing_status, 404)

    def test_analysis_prompt_leaves_navigation_to_sveltekit(self) -> None:
        with TemporaryDirectory() as directory:
            book_dir = Path(directory)
            book_path = book_dir / "account-book.json"
            book_path.write_text(
                json.dumps({"schema_version": 3, "profile": {}}),
                encoding="utf-8",
            )
            prompt = SERVE.Handler(book_path)._render_analyze_prompt(
                window="single month: 2026-07",
                delivery="dashboard only",
                output_filename="analysis-2026-07.html",
            )

            self.assertIn("Do not add\nnavigation links", prompt)
            self.assertNotIn('<a href="/reports.html">', prompt)
            self.assertNotIn('<a href="/reports/">', prompt)
            self.assertNotIn(
                '<a href="https://app.example.test/reports/">',
                prompt,
            )


if __name__ == "__main__":
    unittest.main()
