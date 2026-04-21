"""SMOKE.md parser + runner. Any check failure raises SmokeError."""
from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from harness.config import Config
    from harness.worktree import Worktree

_BLOCK_RE = re.compile(r"^---\s*$\n(.*?)\n^---\s*$", re.MULTILINE | re.DOTALL)


class SmokeError(RuntimeError):
    """Raised on any smoke check failure. Message is user-facing."""


@dataclass
class Check:
    id: str
    type: str  # "shell" | "http" | "playwright"
    raw: dict = field(default_factory=dict)
    trusted: bool = False  # True only for SMOKE.md-authored checks (shell expansion allowed)


@dataclass
class Result:
    check_id: str
    ok: bool
    detail: str = ""


def parse(smoke_text: str) -> list[Check]:
    checks: list[Check] = []
    for match in _BLOCK_RE.finditer(smoke_text):
        data = yaml.safe_load(match.group(1)) or {}
        if not isinstance(data, dict) or not data.get("id"):
            continue
        checks.append(Check(
            id=str(data["id"]), type=str(data.get("type", "shell")), raw=data, trusted=True,
        ))
    return checks


def run_check(check: Check, wt: "Worktree", config: "Config", token: str) -> Result:
    try:
        if check.type == "shell":
            return _shell(check, wt)
        if check.type == "http":
            return _http(check, config, token)
        if check.type == "playwright":
            return _playwright(check, wt, config)
    except Exception as exc:  # noqa: BLE001
        return Result(check.id, False, f"exception: {exc}")
    return Result(check.id, False, f"unknown type: {check.type}")


def check(wt: "Worktree", config: "Config", token: str, extra_checks: list[Check] | None = None) -> None:
    smoke_path = wt.path / "harness" / "SMOKE.md"
    if not smoke_path.is_file():
        raise SmokeError(f"smoke broken: SMOKE.md missing at {smoke_path}")
    all_checks = parse(smoke_path.read_text(encoding="utf-8")) + (extra_checks or [])
    for c in all_checks:
        result = run_check(c, wt, config, token)
        if not result.ok:
            raise SmokeError(f"smoke broken: {result.check_id} — {result.detail}")


def _shell(check: Check, wt: "Worktree") -> Result:
    import shlex  # noqa: C0415 — keep local to the only user
    cmd = check.raw.get("command", "")
    expected = int(check.raw.get("expected_exit", 0))
    if check.trusted:
        # SMOKE.md is version-controlled; shell expansion (e.g. $(date +%s)) is allowed.
        proc = subprocess.run(
            cmd, cwd=wt.path, shell=True, capture_output=True, text=True, check=False, timeout=60,
        )
    else:
        # Untrusted (e.g. LLM-generated repro): no shell, argv only.
        proc = subprocess.run(
            shlex.split(cmd), cwd=wt.path, capture_output=True, text=True, check=False, timeout=60,
        )
    if proc.returncode != expected:
        return Result(check.id, False, f"exit={proc.returncode} expected {expected}: {proc.stderr.strip()[:200]}")
    return Result(check.id, True)


def _http(check: Check, config: "Config", token: str) -> Result:
    method = str(check.raw.get("method", "GET")).upper()
    url = check.raw.get("url", "")
    expected = int(check.raw.get("expected_status", 200))
    headers: dict[str, str] = {}
    if check.raw.get("auth") == "bearer":
        headers["Authorization"] = f"Bearer {token}"
    body: bytes | None = None
    if "body_json" in check.raw:
        headers["Content-Type"] = "application/json"
        body = json.dumps(check.raw["body_json"]).encode()

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            status, payload = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        status, payload = exc.code, exc.read() if exc.fp else b""
    if status != expected:
        return Result(check.id, False, f"status={status} expected {expected}")
    needle = check.raw.get("expected_body_contains")
    if needle and needle not in payload.decode("utf-8", errors="replace"):
        return Result(check.id, False, f"body missing '{needle}'")
    return Result(check.id, True)


def _playwright(check: Check, wt: "Worktree", config: "Config") -> Result:
    url = check.raw.get("url", "")
    expect_no_error = bool(check.raw.get("expect_no_console_error", True))
    script = (
        "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
        f"const p=await b.newPage();const errs=[];p.on('console',m=>{{if(m.type()==='error')errs.push(m.text())}});"
        f"await p.goto({url!r},{{waitUntil:'networkidle',timeout:15000}});"
        "await b.close();process.stdout.write(JSON.stringify({errs}));})()"
    )
    proc = subprocess.run(
        ["node", "-e", script], cwd=wt.path, capture_output=True, text=True, check=False, timeout=30,
    )
    if proc.returncode != 0:
        return Result(check.id, False, f"playwright failed: {proc.stderr.strip()[:200]}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return Result(check.id, False, "playwright: non-json output")
    errs = data.get("errs") or []
    if expect_no_error and errs:
        return Result(check.id, False, f"{len(errs)} console errors: {errs[0][:120]}")
    return Result(check.id, True)
