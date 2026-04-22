"""Smoke test: `freddy fixture --help` returns 0 and mentions the group name."""
import subprocess


def test_fixture_command_group_registered():
    result = subprocess.run(
        ["freddy", "fixture", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "fixture" in result.stdout.lower()
