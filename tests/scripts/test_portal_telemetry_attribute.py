"""Unit tests for the CC hook attribution helper.

R7 HOOK PATH coverage:
  (a) env=A, cwd=A          → attribute to A,        no conflict
  (b) env unset, cwd=A      → attribute to A,        no conflict
  (c) env=A, cwd=B          → operator-internal,     conflict (env_vs_cwd_disagree)
  (d) env=A, cwd unset      → attribute to A,        no conflict
  (e) env unset, cwd unset  → operator-internal,     no conflict
  (f) env=invalid-slug      → operator-internal,     conflict (slug_invalid)

We exercise the resolver two ways:

1. **Direct function calls** via the importable ``resolve_attribution``.
   Fast + structured-error visibility.
2. **Subprocess** with stdin JSON + env, asserting the two-line stdout
   contract (line 1 = client_id, line 2 = conflict-payload JSON). This
   guards the bash hook's actual parsing behavior.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HELPER_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "claude-code-hooks"
    / "portal-telemetry-attribute.py"
)


@pytest.fixture(scope="module")
def helper_module():
    """Import the helper as a Python module (handles the hyphenated filename)."""
    spec = importlib.util.spec_from_file_location(
        "portal_telemetry_attribute", HELPER_PATH
    )
    assert spec and spec.loader, f"failed to load spec for {HELPER_PATH}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Direct function-call tests (R7 HOOK PATH a–f).
# ---------------------------------------------------------------------------


def test_case_a_env_and_cwd_agree(helper_module):
    """(a) env=A, cwd=A → A, no conflict."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id="klinika-melitus",
        cwd="/Users/op/code/clients/klinika-melitus/work",
    )
    assert cid == "klinika-melitus"
    assert conflict is None


def test_case_b_env_unset_cwd_set(helper_module):
    """(b) env unset, cwd=A → A, no conflict."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id=None,
        cwd="/srv/clients/dwf-poland/code",
    )
    assert cid == "dwf-poland"
    assert conflict is None


def test_case_b_env_empty_string_treated_as_unset(helper_module):
    """Empty string env is treated as unset (shell-export edge)."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id="",
        cwd="/srv/clients/dwf-poland/code",
    )
    assert cid == "dwf-poland"
    assert conflict is None


def test_case_c_env_cwd_disagree(helper_module):
    """(c) env=A, cwd=B → conflict env_vs_cwd_disagree, operator-internal."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id="klinika-melitus",
        cwd="/srv/clients/dwf-poland/code",
    )
    assert cid is None
    assert conflict is not None
    assert conflict["kind"] == "moment"
    assert conflict["source"] == "claude_code"
    meta = conflict["metadata"]
    assert meta["moment_kind"] == "attribution_conflict"
    assert meta["reason"] == "env_vs_cwd_disagree"
    assert meta["env_client_id"] == "klinika-melitus"
    assert meta["cwd_client_id"] == "dwf-poland"
    assert "klinika-melitus" not in str(conflict.get("client_id", ""))  # absent


def test_case_d_env_set_cwd_unset(helper_module):
    """(d) env=A, cwd unset → A, no conflict."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id="acme-corp",
        cwd=None,
    )
    assert cid == "acme-corp"
    assert conflict is None


def test_case_d_env_set_cwd_no_clients_segment(helper_module):
    """env=A, cwd missing clients/ segment → A (treated as cwd-unset)."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id="acme-corp",
        cwd="/Users/op/projects/personal/notes",
    )
    assert cid == "acme-corp"
    assert conflict is None


def test_case_e_both_unset(helper_module):
    """(e) env unset, cwd unset → operator-internal, no conflict."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id=None, cwd=None
    )
    assert cid is None
    assert conflict is None


def test_case_e_cwd_set_but_outside_clients(helper_module):
    """env unset, cwd has no clients/ segment → operator-internal, no conflict."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id=None,
        cwd="/Users/op/projects/personal/notes",
    )
    assert cid is None
    assert conflict is None


def test_case_f_env_invalid_slug_uppercase(helper_module):
    """(f) env=INVALID (uppercase) → conflict slug_invalid, operator-internal."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id="KlinikaMelitus", cwd=None
    )
    assert cid is None
    assert conflict is not None
    assert conflict["metadata"]["reason"] == "slug_invalid"
    assert conflict["metadata"]["env_client_id"] == "KlinikaMelitus"


def test_case_f_env_invalid_slug_special_chars(helper_module):
    """env with special chars (e.g. underscore) fails the regex."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id="klinika_melitus", cwd=None
    )
    assert cid is None
    assert conflict is not None
    assert conflict["metadata"]["reason"] == "slug_invalid"


def test_case_f_env_invalid_too_long(helper_module):
    """env > 64 chars fails the regex."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id="a" * 65, cwd=None
    )
    assert cid is None
    assert conflict is not None
    assert conflict["metadata"]["reason"] == "slug_invalid"


def test_cwd_invalid_slug_silently_falls_through(helper_module):
    """env unset + cwd has clients/<bad-slug>/ → operator-internal, NO emission.

    The hook doesn't emit slug_invalid for cwd-only candidates — the
    tailer will catch it later (R5.4 path), and we don't want two
    emissions on the same session. Documented in resolve_attribution.
    """
    cid, conflict = helper_module.resolve_attribution(
        env_client_id=None,
        cwd="/srv/clients/Bad_Slug/work",
    )
    assert cid is None
    assert conflict is None


def test_cwd_extracts_first_clients_segment(helper_module):
    """Nested clients/ paths: first match wins."""
    cid, conflict = helper_module.resolve_attribution(
        env_client_id=None,
        cwd="/srv/clients/acme/sub/clients/other/work",
    )
    assert cid == "acme"
    assert conflict is None


# ---------------------------------------------------------------------------
# Subprocess tests — verify the 2-line stdout contract the bash hook reads.
# ---------------------------------------------------------------------------


def _run_helper(stdin_json: dict | str, env: dict[str, str]) -> tuple[str, str]:
    """Invoke the helper as a subprocess. Returns (line1, line2) of stdout.

    ``env`` REPLACES the process env (except PATH, inherited), so callers
    explicitly opt into ``GOFREDDY_CLIENT_ID``.
    """
    full_env = {"PATH": os.environ.get("PATH", "")}
    full_env.update(env)
    stdin_str = (
        stdin_json if isinstance(stdin_json, str) else json.dumps(stdin_json)
    )
    result = subprocess.run(
        [sys.executable, str(HELPER_PATH)],
        input=stdin_str,
        capture_output=True,
        text=True,
        env=full_env,
        timeout=5,
    )
    assert result.returncode == 0, (
        f"helper exited non-zero: rc={result.returncode} stderr={result.stderr}"
    )
    lines = result.stdout.split("\n")
    # The helper always prints exactly 2 lines (line1, line2) + trailing newline
    line1 = lines[0] if len(lines) > 0 else ""
    line2 = lines[1] if len(lines) > 1 else ""
    return line1, line2


def test_subprocess_case_a_env_and_cwd_agree():
    """(a) via subprocess: env=A + cwd=A → line1=A, line2 empty."""
    line1, line2 = _run_helper(
        {"cwd": "/srv/clients/acme/work", "session_id": "s1"},
        env={"GOFREDDY_CLIENT_ID": "acme"},
    )
    assert line1 == "acme"
    assert line2 == ""


def test_subprocess_case_c_disagree_emits_conflict_with_session_id():
    """(c) via subprocess: conflict payload includes session_id passthrough."""
    line1, line2 = _run_helper(
        {"cwd": "/srv/clients/dwf-poland/code", "session_id": "sess-xyz"},
        env={"GOFREDDY_CLIENT_ID": "acme"},
    )
    assert line1 == ""
    payload = json.loads(line2)
    assert payload["kind"] == "moment"
    assert payload["session_id"] == "sess-xyz"
    assert payload["metadata"]["moment_kind"] == "attribution_conflict"
    assert payload["metadata"]["reason"] == "env_vs_cwd_disagree"


def test_subprocess_case_e_both_unset():
    """(e) via subprocess: empty env + no cwd → both lines empty."""
    line1, line2 = _run_helper({}, env={})
    assert line1 == ""
    assert line2 == ""


def test_subprocess_case_f_invalid_env_slug():
    """(f) via subprocess: invalid env slug → line1 empty, line2 conflict."""
    line1, line2 = _run_helper(
        {"cwd": None, "session_id": "s2"},
        env={"GOFREDDY_CLIENT_ID": "Has Space"},
    )
    assert line1 == ""
    payload = json.loads(line2)
    assert payload["metadata"]["reason"] == "slug_invalid"
    assert payload["session_id"] == "s2"


def test_subprocess_handles_malformed_stdin():
    """Bad JSON on stdin → falls through to operator-internal, no crash."""
    line1, line2 = _run_helper("{not json", env={})
    assert line1 == ""
    assert line2 == ""


def test_subprocess_handles_empty_stdin():
    """Empty stdin → operator-internal, no crash."""
    line1, line2 = _run_helper("", env={})
    assert line1 == ""
    assert line2 == ""
