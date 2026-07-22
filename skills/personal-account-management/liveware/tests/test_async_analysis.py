from __future__ import annotations

import importlib.util
import io
import json
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SERVE_PATH = Path(__file__).resolve().parents[1] / "serve.py"
SPEC = importlib.util.spec_from_file_location("personal_account_liveware_serve", SERVE_PATH)
assert SPEC is not None and SPEC.loader is not None
SERVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SERVE)


class AsyncAnalysisTests(unittest.TestCase):
    def test_analysis_accepts_chunked_request_body_from_liveware_tunnel(self) -> None:
        with TemporaryDirectory() as directory:
            book_path = Path(directory) / "account-book.json"
            book_path.write_text(
                json.dumps({"schema_version": 3, "profile": {}}),
                encoding="utf-8",
            )
            handler = SERVE.Handler(book_path)

            status, _, payload_bytes = handler.route(
                "POST",
                "/api/analyze",
                headers={"Transfer-Encoding": "chunked"},
                rfile=io.BytesIO(b"2\r\n{}\r\n0\r\n\r\n"),
            )

            self.assertEqual(status, 400)
            self.assertEqual(json.loads(payload_bytes)["error"], "missing_window")

    def test_analysis_launch_returns_before_slow_hermes_call_finishes(self) -> None:
        with TemporaryDirectory() as directory:
            book_dir = Path(directory)
            book_path = book_dir / "account-book.json"
            book_path.write_text(
                json.dumps(
                    {
                        "schema_version": 3,
                        "profile": {
                            "base_currency": "CNY",
                            "timezone": "Asia/Shanghai",
                        },
                    }
                ),
                encoding="utf-8",
            )
            (book_dir / "liveware-dashboard.state.json").write_text(
                json.dumps({"public_url": "https://example.invalid"}),
                encoding="utf-8",
            )

            handler = SERVE.Handler(book_path)
            hermes_release = threading.Event()

            def slow_hermes_call(system_prompt: str):
                self.assertIn("single month: 2026-07", system_prompt)
                self.assertTrue(hermes_release.wait(2), "test did not release Hermes stub")
                pending_name = handler._private_analysis_filename(
                    "analysis-2026-07.html",
                    handler._analyze_run_id,
                )
                reports_dir = book_dir / "reports"
                reports_dir.mkdir(parents=True, exist_ok=True)
                (reports_dir / pending_name).write_text("<html>ok</html>", encoding="utf-8")
                return 200, b'{"choices": [{"message": {"content": "ok"}}]}', {}

            handler._call_hermes_api = slow_hermes_call
            request_body = json.dumps(
                {
                    "window": "single month: 2026-07",
                    "delivery": "dashboard only",
                    "output_filename": "analysis-2026-07.html",
                }
            ).encode("utf-8")
            response_holder: list[tuple[int, dict, bytes]] = []
            response_ready = threading.Event()

            def launch() -> None:
                response_holder.append(
                    handler.route(
                        "POST",
                        "/api/analyze",
                        headers={"Content-Length": str(len(request_body))},
                        rfile=io.BytesIO(request_body),
                    )
                )
                response_ready.set()

            request_thread = threading.Thread(target=launch, daemon=True)
            request_thread.start()
            returned_promptly = response_ready.wait(0.5)
            hermes_release.set()
            request_thread.join(3)

            self.assertTrue(returned_promptly, "/api/analyze blocked on the Hermes response")
            self.assertEqual(len(response_holder), 1)
            status, _, payload_bytes = response_holder[0]
            self.assertEqual(status, 202)
            payload = json.loads(payload_bytes)
            self.assertIs(payload.get("accepted"), True)
            self.assertEqual(payload["analysis"]["state"], "running")

            deadline = time.time() + 2
            final_status = None
            while time.time() < deadline:
                with handler._analyze_lock:
                    final_status = handler._analysis_status_locked()
                if final_status["state"] != "running":
                    break
                time.sleep(0.01)

            self.assertIsNotNone(final_status)
            self.assertEqual(final_status["state"], "succeeded")
            self.assertEqual(final_status["upstream_status"], 200)
            self.assertEqual(final_status["report_url"], "#/reports/2026-07")


if __name__ == "__main__":
    unittest.main()
