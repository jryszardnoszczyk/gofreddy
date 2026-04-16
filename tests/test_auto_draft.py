"""Tests for auto-draft CLI command helpers."""

from cli.freddy.commands.auto_draft import _check_trigger, _build_command


class TestTriggerEvaluation:
    def test_cron_always_triggers(self, tmp_path):
        assert _check_trigger({"type": "cron"}, tmp_path) is True

    def test_unknown_type_does_not_trigger(self, tmp_path):
        assert _check_trigger({"type": "unknown"}, tmp_path) is False

    def test_empty_type_does_not_trigger(self, tmp_path):
        assert _check_trigger({}, tmp_path) is False

    def test_brief_available_checks_brief_md(self, tmp_path):
        session_dir = tmp_path / "my_session"
        session_dir.mkdir()
        (session_dir / "brief.md").write_text("test brief")
        assert _check_trigger(
            {"type": "brief_available", "session_dir": "my_session"}, tmp_path
        ) is True

    def test_brief_available_checks_digest_md(self, tmp_path):
        session_dir = tmp_path / "my_session"
        session_dir.mkdir()
        (session_dir / "digest.md").write_text("test digest")
        assert _check_trigger(
            {"type": "brief_available", "session_dir": "my_session"}, tmp_path
        ) is True

    def test_brief_available_missing_files(self, tmp_path):
        session_dir = tmp_path / "my_session"
        session_dir.mkdir()
        assert _check_trigger(
            {"type": "brief_available", "session_dir": "my_session"}, tmp_path
        ) is False

    def test_brief_available_no_session_dir(self, tmp_path):
        assert _check_trigger({"type": "brief_available"}, tmp_path) is False

    def test_digest_available_no_sessions(self, tmp_path):
        assert _check_trigger(
            {"type": "digest_available", "monitor_id": "test"}, tmp_path
        ) is False

    def test_digest_available_with_digest(self, tmp_path):
        digest_dir = tmp_path / "sessions" / "monitoring" / "mon123"
        digest_dir.mkdir(parents=True)
        (digest_dir / "digest.md").write_text("digest content")
        assert _check_trigger(
            {"type": "digest_available", "monitor_id": "mon123"}, tmp_path
        ) is True


class TestBuildCommand:
    def test_build_simple_command(self):
        action = {"command": "freddy write", "args": {"monitor_id": "abc"}}
        cmd = _build_command(action)
        assert cmd == ["freddy", "write", "--monitor-id", "abc"]

    def test_build_command_no_args(self):
        action = {"command": "freddy sync"}
        cmd = _build_command(action)
        assert cmd == ["freddy", "sync"]

    def test_build_command_multiple_args(self):
        action = {
            "command": "freddy draft",
            "args": {"monitor_id": "m1", "format": "markdown"},
        }
        cmd = _build_command(action)
        assert "freddy" in cmd
        assert "draft" in cmd
        assert "--monitor-id" in cmd
        assert "m1" in cmd
        assert "--format" in cmd
        assert "markdown" in cmd

    def test_build_command_underscores_to_hyphens(self):
        action = {"command": "test", "args": {"dry_run": "yes"}}
        cmd = _build_command(action)
        assert "--dry-run" in cmd
        assert "yes" in cmd

    def test_build_command_bool_flag(self):
        action = {"command": "test", "args": {"verbose": True, "quiet": False}}
        cmd = _build_command(action)
        assert "--verbose" in cmd
        # False bools should not be added
        assert "--quiet" not in cmd
