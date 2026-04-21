"""Shared fixtures for harness tests."""
from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _neutralise_harness_env(monkeypatch):
    for key in list(os.environ):
        if key.startswith("HARNESS_"):
            monkeypatch.delenv(key, raising=False)
