"""Tests for CLI session state management."""

import json
import os

import pytest

from freddy.session import LocalSession, clear_session, get_active_session, save_session


@pytest.fixture
def session_file(tmp_path, monkeypatch):
    """Override session file to use tmp_path."""
    session_file = tmp_path / "session.json"
    monkeypatch.setattr("freddy.session._SESSION_FILE", session_file)
    return session_file


class TestSession:

    def test_no_active_session_by_default(self, session_file):
        assert get_active_session() is None

    def test_save_and_load_session(self, session_file):
        session = LocalSession(
            session_id="abc-123",
            client_name="acme",
            session_type="research",
            purpose="Creator vetting",
        )
        save_session(session)

        loaded = get_active_session()
        assert loaded is not None
        assert loaded.session_id == "abc-123"
        assert loaded.client_name == "acme"
        assert loaded.session_type == "research"
        assert loaded.purpose == "Creator vetting"

    def test_clear_session(self, session_file):
        save_session(LocalSession(session_id="xyz", client_name="test"))
        assert clear_session() is True
        assert get_active_session() is None

    def test_clear_nonexistent_session(self, session_file):
        assert clear_session() is False

    def test_corrupted_session_file_returns_none(self, session_file):
        session_file.write_text("not valid json{{{")
        assert get_active_session() is None

    def test_session_file_missing_keys_returns_none(self, session_file):
        session_file.write_text(json.dumps({"only": "partial"}))
        assert get_active_session() is None
