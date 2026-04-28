"""Tests for autoresearch/geo_verify.py."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# autoresearch/ is on sys.path via tests/autoresearch/conftest.py
from geo_verify import (  # type: ignore[import-not-found]
    extract_queries,
    load_env,
    main,
    run_visibility_checks,
    write_report,
)


class TestExtractQueriesFromResultsJsonl(unittest.TestCase):
    """test_queries_from_results_jsonl: competitive entries yield sorted, deduplicated queries."""

    def test_extracts_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as td:
            session_dir = Path(td)
            results = session_dir / "results.jsonl"
            results.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "competitive",
                                "queries": ["best pizza nyc", "best tacos nyc"],
                            }
                        ),
                        json.dumps(
                            {
                                "type": "competitive",
                                "queries": ["best tacos nyc", "best sushi nyc"],
                            }
                        ),
                        json.dumps(
                            {
                                "type": "organic",
                                "queries": ["should not appear"],
                            }
                        ),
                        "",  # empty line
                        "invalid json line",
                    ]
                )
            )

            queries = extract_queries(session_dir)
            self.assertEqual(
                queries,
                ["best pizza nyc", "best sushi nyc", "best tacos nyc"],
            )

    def test_empty_results_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            session_dir = Path(td)
            results = session_dir / "results.jsonl"
            results.write_text("")

            queries = extract_queries(session_dir)
            self.assertEqual(queries, [])

    def test_no_results_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            queries = extract_queries(Path(td))
            self.assertEqual(queries, [])


class TestExtractQueriesFromVerificationSchedule(unittest.TestCase):
    """test_queries_from_verification_schedule: schedule file takes precedence."""

    def test_reads_from_schedule(self):
        with tempfile.TemporaryDirectory() as td:
            session_dir = Path(td)
            schedule = session_dir / "verification-schedule.json"
            schedule.write_text(
                json.dumps({"queries": ["query alpha", "query beta"]})
            )
            # Also create results.jsonl — should be ignored
            results = session_dir / "results.jsonl"
            results.write_text(
                json.dumps({"type": "competitive", "queries": ["should not appear"]})
            )

            queries = extract_queries(session_dir)
            self.assertEqual(queries, ["query alpha", "query beta"])

    def test_empty_queries_list(self):
        with tempfile.TemporaryDirectory() as td:
            session_dir = Path(td)
            schedule = session_dir / "verification-schedule.json"
            schedule.write_text(json.dumps({"queries": []}))

            queries = extract_queries(session_dir)
            self.assertEqual(queries, [])


class TestNoQueriesExitsCleanly(unittest.TestCase):
    """test_no_queries_exits_cleanly: empty results → exits 0 with message."""

    def test_empty_results_exits_zero(self):
        with tempfile.TemporaryDirectory() as td:
            session_dir = Path(td)
            results = session_dir / "results.jsonl"
            results.write_text("")

            with mock.patch("sys.argv", ["geo_verify.py", str(session_dir)]):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 0)


class TestMissingSessionDir(unittest.TestCase):
    """test_missing_session_dir: non-existent path → SystemExit."""

    def test_nonexistent_dir_exits_one(self):
        with mock.patch(
            "sys.argv", ["geo_verify.py", "/nonexistent/path/abc123"]
        ):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)


class TestEnvLoading(unittest.TestCase):
    """test_env_loading: verify .env file is parsed correctly."""

    def test_loads_all_keys(self):
        with tempfile.TemporaryDirectory() as td:
            env_file = Path(td) / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "# comment line",
                        "",
                        'FREDDY_API_URL="http://example.com"',
                        "SOME_CUSTOM_KEY='custom_value'",
                        "BARE_KEY=bare_value",
                        "ANTHROPIC_API_KEY=secret_should_be_removed",
                    ]
                )
            )

            # Patch SCRIPT_DIR so load_env finds our .env
            saved_env = {}
            keys_to_check = [
                "FREDDY_API_URL",
                "SOME_CUSTOM_KEY",
                "BARE_KEY",
                "ANTHROPIC_API_KEY",
            ]
            for k in keys_to_check:
                if k in os.environ:
                    saved_env[k] = os.environ[k]

            try:
                with mock.patch(
                    "geo_verify.SCRIPT_DIR", Path(td) / "subdir"
                ):
                    # Parent of SCRIPT_DIR is td, where .env lives
                    load_env()

                self.assertEqual(os.environ.get("FREDDY_API_URL"), "http://example.com")
                self.assertEqual(os.environ.get("SOME_CUSTOM_KEY"), "custom_value")
                self.assertEqual(os.environ.get("BARE_KEY"), "bare_value")
                # ANTHROPIC_API_KEY must be removed
                self.assertNotIn("ANTHROPIC_API_KEY", os.environ)
            finally:
                # Restore environment
                for k in keys_to_check:
                    if k in saved_env:
                        os.environ[k] = saved_env[k]
                    else:
                        os.environ.pop(k, None)


class TestLocalhostRewrite(unittest.TestCase):
    """test_localhost_rewrite: localhost URLs get rewritten to 127.0.0.1."""

    def _run_rewrite(self, input_url: str) -> str:
        """Set FREDDY_API_URL, run load_env with empty .env, return result."""
        saved = os.environ.get("FREDDY_API_URL")
        try:
            os.environ["FREDDY_API_URL"] = input_url
            with tempfile.TemporaryDirectory() as td:
                # Create empty .env so load_env doesn't overwrite FREDDY_API_URL
                env_file = Path(td) / ".env"
                env_file.write_text("")
                with mock.patch(
                    "geo_verify.SCRIPT_DIR", Path(td) / "subdir"
                ):
                    load_env()
            return os.environ.get("FREDDY_API_URL", "")
        finally:
            if saved is not None:
                os.environ["FREDDY_API_URL"] = saved
            else:
                os.environ.pop("FREDDY_API_URL", None)

    def test_localhost_with_port(self):
        result = self._run_rewrite("http://localhost:8080")
        self.assertEqual(result, "http://127.0.0.1:8080")

    def test_localhost_no_port(self):
        result = self._run_rewrite("http://localhost")
        self.assertEqual(result, "http://127.0.0.1")

    def test_non_localhost_unchanged(self):
        result = self._run_rewrite("http://example.com:8080")
        self.assertEqual(result, "http://example.com:8080")


class TestRunVisibilityChecks(unittest.TestCase):
    """Verify freddy visibility subprocess calls are made correctly."""

    @mock.patch("geo_verify.time.sleep")
    @mock.patch("geo_verify.subprocess.run")
    def test_successful_queries(self, mock_run, mock_sleep):
        mock_run.return_value = mock.Mock(
            returncode=0, stdout='{"visibility": "high"}'
        )

        results = run_visibility_checks(["query1", "query2"])

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], ("query1", '{"visibility": "high"}'))
        self.assertEqual(results[1], ("query2", '{"visibility": "high"}'))

        # freddy visibility called twice
        self.assertEqual(mock_run.call_count, 2)
        mock_run.assert_any_call(
            ["freddy", "visibility", "query1"],
            capture_output=True,
            text=True,
        )

        # Sleep called once (between queries, not after last)
        mock_sleep.assert_called_once_with(3)

    @mock.patch("geo_verify.time.sleep")
    @mock.patch("geo_verify.subprocess.run")
    def test_failed_query_captured(self, mock_run, mock_sleep):
        mock_run.return_value = mock.Mock(returncode=1, stdout="")

        results = run_visibility_checks(["bad_query"])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], ("bad_query", '{"error": "query failed"}'))

    @mock.patch("geo_verify.time.sleep")
    @mock.patch("geo_verify.subprocess.run")
    def test_subprocess_exception_captured(self, mock_run, mock_sleep):
        mock_run.side_effect = OSError("command not found")

        results = run_visibility_checks(["query1"])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], ("query1", '{"error": "query failed"}'))


class TestWriteReport(unittest.TestCase):
    """Verify markdown report structure matches bash version."""

    def test_report_structure(self):
        with tempfile.TemporaryDirectory() as td:
            session_dir = Path(td)
            results = [
                ("test query 1", '{"visibility": "high"}'),
                ("test query 2", '{"error": "query failed"}'),
            ]

            report_path = write_report(session_dir, results)

            self.assertTrue(report_path.exists())
            content = report_path.read_text()

            # Check structural elements
            self.assertIn("# GEO Verification Report", content)
            self.assertIn("Date: ", content)
            self.assertIn(f"Session: {session_dir}", content)
            self.assertIn("## Query Results", content)
            self.assertIn("### test query 1", content)
            self.assertIn("### test query 2", content)
            self.assertIn("```json", content)
            self.assertIn('{"visibility": "high"}', content)
            self.assertIn('{"error": "query failed"}', content)
            self.assertIn("## Summary", content)
            self.assertIn(
                "Verification complete. Compare results above with baseline "
                "in competitors/visibility.json.",
                content,
            )


if __name__ == "__main__":
    unittest.main()
