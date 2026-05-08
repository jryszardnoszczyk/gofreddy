"""α7 unit tests for `freddy autoresearch` Typer subcommands.

Covers `render`, `publish`, and `detect-meta-patterns` happy paths + error
paths. Subprocess invocations are mocked so we don't actually spawn codex
or chrome from the test runner.
"""
from __future__ import annotations

import json
from unittest import mock

from typer.testing import CliRunner

from freddy.main import app

runner = CliRunner()


class TestAutoresearchRender:

    def test_render_unknown_lane_exits_2(self, tmp_path):
        result = runner.invoke(
            app,
            ["autoresearch", "render", "v007", "fakelane", "fakefixture"],
        )
        assert result.exit_code == 2
        assert "unknown lane" in result.stdout.lower() + (result.stderr or "").lower()

    def test_render_missing_session_exits_1(self, tmp_path, monkeypatch):
        # Point archive root at an empty tmp_path so the session lookup fails
        from freddy.commands import autoresearch as ar_cmd
        monkeypatch.setattr(ar_cmd, "_ARCHIVE_ROOT", tmp_path)
        result = runner.invoke(
            app, ["autoresearch", "render", "v007", "geo", "nonexistent"],
        )
        assert result.exit_code == 1
        assert "session dir not found" in result.stdout.lower() + (result.stderr or "").lower()

    def test_render_invokes_subprocess(self, tmp_path, monkeypatch):
        # Build a fake session dir + fake render_report.py so the path checks pass
        from freddy.commands import autoresearch as ar_cmd
        archive = tmp_path / "archive"
        sd = archive / "v007" / "sessions" / "geo" / "mayoclinic"
        sd.mkdir(parents=True)
        scripts_dir = archive / "v007" / "scripts"
        scripts_dir.mkdir(parents=True)
        script = scripts_dir / "render_report.py"
        script.write_text("# stub", encoding="utf-8")
        monkeypatch.setattr(ar_cmd, "_ARCHIVE_ROOT", archive)
        monkeypatch.setattr(ar_cmd, "_resolve_python", lambda: "/usr/bin/true")

        with mock.patch.object(ar_cmd.subprocess, "run") as mocked_run:
            mocked_run.return_value = mock.Mock(returncode=0)
            result = runner.invoke(
                app, ["autoresearch", "render", "v007", "geo", "mayoclinic"],
            )

        assert result.exit_code == 0
        assert mocked_run.called
        called_args = mocked_run.call_args[0][0]
        assert called_args[1] == str(script)
        assert called_args[-3:] == [str(sd), "geo", "mayoclinic"]


class TestAutoresearchPublish:

    def test_publish_missing_html_exits_1(self, tmp_path, monkeypatch):
        from freddy.commands import autoresearch as ar_cmd
        archive = tmp_path / "archive"
        sd = archive / "v007" / "sessions" / "geo" / "mayoclinic"
        sd.mkdir(parents=True)
        monkeypatch.setattr(ar_cmd, "_ARCHIVE_ROOT", archive)

        result = runner.invoke(
            app,
            ["autoresearch", "publish", "v007", "geo", "mayoclinic", "--client", "demo"],
        )
        assert result.exit_code == 1
        assert "report.html missing" in result.stdout.lower() + (result.stderr or "").lower()

    def test_publish_portal_gated_returns_url(self, tmp_path, monkeypatch):
        from freddy.commands import autoresearch as ar_cmd
        archive = tmp_path / "archive"
        sd = archive / "v007" / "sessions" / "geo" / "mayoclinic"
        sd.mkdir(parents=True)
        (sd / "report.html").write_text("<html></html>", encoding="utf-8")
        monkeypatch.setattr(ar_cmd, "_ARCHIVE_ROOT", archive)
        monkeypatch.setenv("FREDDY_PORTAL_DOMAIN", "portal.test.example")

        result = runner.invoke(
            app,
            ["autoresearch", "publish", "v007", "geo", "mayoclinic", "--client", "acme"],
        )
        assert result.exit_code == 0
        assert "portal.test.example" in result.stdout
        assert "/v1/portal/acme/reports/geo/v007/mayoclinic" in result.stdout


class TestAutoresearchDetectMetaPatterns:

    def test_detect_meta_patterns_invokes_subprocess(self, tmp_path, monkeypatch):
        from freddy.commands import autoresearch as ar_cmd

        archive = tmp_path / "archive"
        runtime_scripts = archive / "current_runtime" / "scripts"
        runtime_scripts.mkdir(parents=True)
        script = runtime_scripts / "detect_meta_patterns.py"
        script.write_text("# stub", encoding="utf-8")
        monkeypatch.setattr(ar_cmd, "_ARCHIVE_ROOT", archive)
        monkeypatch.setattr(ar_cmd, "_resolve_python", lambda: "/usr/bin/true")

        out_path = tmp_path / "out.json"
        with mock.patch.object(ar_cmd.subprocess, "run") as mocked_run:
            mocked_run.return_value = mock.Mock(returncode=0)
            result = runner.invoke(
                app,
                ["autoresearch", "detect-meta-patterns", "-o", str(out_path)],
            )
        assert result.exit_code == 0
        assert mocked_run.called
        called_args = mocked_run.call_args[0][0]
        assert called_args[1] == str(script)
        assert "--all-lanes" in called_args
        assert str(out_path) in called_args
