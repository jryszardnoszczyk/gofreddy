"""Unit tests for lane_paths.path_owned_by_lane — single source of truth for lane ownership."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import lane_paths


def test_geo_owns_geo_files():
    assert lane_paths.path_owned_by_lane("workflows/geo.py", "geo")
    assert lane_paths.path_owned_by_lane("geo-findings.md", "geo")
    assert lane_paths.path_owned_by_lane("templates/geo/some_template.md", "geo")


def test_competitive_owns_competitive_files():
    assert lane_paths.path_owned_by_lane("workflows/competitive.py", "competitive")
    assert lane_paths.path_owned_by_lane("competitive-findings.md", "competitive")


def test_monitoring_owns_monitoring_files():
    assert lane_paths.path_owned_by_lane("programs/monitoring-session.md", "monitoring")
    assert lane_paths.path_owned_by_lane("workflows/session_eval_monitoring.py", "monitoring")


def test_storyboard_owns_storyboard_files():
    assert lane_paths.path_owned_by_lane("workflows/storyboard.py", "storyboard")
    assert lane_paths.path_owned_by_lane("storyboard-findings.md", "storyboard")


def test_core_does_not_own_workflow_files():
    assert not lane_paths.path_owned_by_lane("workflows/geo.py", "core")
    assert not lane_paths.path_owned_by_lane("competitive-findings.md", "core")
    assert not lane_paths.path_owned_by_lane("programs/monitoring-session.md", "core")
    assert not lane_paths.path_owned_by_lane("workflows/storyboard.py", "core")


def test_core_owns_shared_files():
    assert lane_paths.path_owned_by_lane("workflows/specs.py", "core")
    assert lane_paths.path_owned_by_lane("programs/research-session.md", "core")
    assert lane_paths.path_owned_by_lane("run.py", "core")


def test_lane_does_not_own_other_lane_files():
    assert not lane_paths.path_owned_by_lane("workflows/geo.py", "competitive")
    assert not lane_paths.path_owned_by_lane("monitoring-findings.md", "storyboard")
    assert not lane_paths.path_owned_by_lane("workflows/storyboard.py", "geo")
