"""Pytest config — tmp_path-isolated DB, fixture data."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_tweets() -> list[dict]:
    return json.loads((FIXTURES_DIR / "sample_tweets.json").read_text())


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Redirect x_engine.pipeline.db.DB_PATH to a tmp file."""
    from x_engine.pipeline import db as db_mod

    test_db = tmp_path / "state.db"
    monkeypatch.setattr(db_mod, "DB_PATH", test_db)
    db_mod.init_db(test_db)
    return test_db
