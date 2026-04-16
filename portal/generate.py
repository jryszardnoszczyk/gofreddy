"""Client portal static site generator.

Renders per-client dashboards from data under ``clients/<name>/``.

Usage:
    python portal/generate.py                       # all clients
    python portal/generate.py --client demo-clinic  # single client
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_CLIENTS_DIR = _SCRIPT_DIR.parent / "clients"
_DEFAULT_OUTPUT_DIR = _SCRIPT_DIR / "output"
_TEMPLATE_DIR = _SCRIPT_DIR / "templates"


@dataclass
class SessionSummary:
    session_id: str
    started_at: str | None
    status: str
    action_count: int
    total_credits: int


@dataclass
class ActionRow:
    timestamp: str
    tool_name: str
    status: str
    duration_ms: int | None
    cost_usd: float | None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _collect_client_data(client_dir: Path) -> dict[str, Any]:
    config = _read_json(client_dir / "config.json")
    sessions_dir = client_dir / "sessions"
    sessions: list[SessionSummary] = []
    all_actions: list[ActionRow] = []

    earliest: datetime | None = None
    latest: datetime | None = None

    if sessions_dir.exists():
        for session_dir in sorted(sessions_dir.iterdir()):
            if not session_dir.is_dir():
                continue
            meta = _read_json(session_dir / "meta.json")
            if not meta:
                continue
            started_at = meta.get("started_at")
            if started_at:
                try:
                    dt = datetime.fromisoformat(started_at)
                    if earliest is None or dt < earliest:
                        earliest = dt
                    if latest is None or dt > latest:
                        latest = dt
                except ValueError:
                    pass
            sessions.append(SessionSummary(
                session_id=meta.get("id", session_dir.name),
                started_at=started_at,
                status=meta.get("status", "unknown"),
                action_count=int(meta.get("action_count", 0)),
                total_credits=int(meta.get("total_credits", 0)),
            ))
            for row in _read_jsonl(session_dir / "actions.jsonl"):
                all_actions.append(ActionRow(
                    timestamp=row.get("created_at", ""),
                    tool_name=row.get("tool_name", ""),
                    status=row.get("status", ""),
                    duration_ms=row.get("duration_ms"),
                    cost_usd=None,
                ))

    cost_rows = _read_jsonl(client_dir / "cost_log.jsonl")
    total_cost = 0.0
    by_provider: dict[str, float] = defaultdict(float)
    for row in cost_rows:
        cost = row.get("cost_usd") or 0.0
        try:
            cost = float(cost)
        except (TypeError, ValueError):
            cost = 0.0
        total_cost += cost
        by_provider[row.get("provider") or "unknown"] += cost

    all_actions.sort(key=lambda a: a.timestamp, reverse=True)

    return {
        "name": client_dir.name,
        "config": config,
        "sessions": sessions,
        "actions": all_actions[:200],
        "total_sessions": len(sessions),
        "total_actions": sum(s.action_count for s in sessions),
        "total_cost_usd": round(total_cost, 4),
        "cost_by_provider": [
            {"provider": p, "cost_usd": round(v, 4)}
            for p, v in sorted(by_provider.items(), key=lambda kv: kv[1], reverse=True)
        ],
        "date_range": {
            "earliest": earliest.isoformat() if earliest else None,
            "latest": latest.isoformat() if latest else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _render(client_data: dict[str, Any], output_path: Path, env: Environment) -> None:
    template = env.get_template("client.html")
    html = template.render(**client_data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)


def generate(clients_dir: Path, output_dir: Path, client: str | None = None) -> list[Path]:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    written: list[Path] = []

    if not clients_dir.exists():
        return written

    candidates = [clients_dir / client] if client else sorted(clients_dir.iterdir())
    for entry in candidates:
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        data = _collect_client_data(entry)
        out = output_dir / entry.name / "index.html"
        _render(data, out, env)
        written.append(out)
    return written


def _main() -> int:
    parser = argparse.ArgumentParser(description="Generate client portal HTML.")
    parser.add_argument("--clients-dir", default=str(_DEFAULT_CLIENTS_DIR))
    parser.add_argument("--output-dir", default=str(_DEFAULT_OUTPUT_DIR))
    parser.add_argument("--client", default=None, help="Only generate for this client")
    args = parser.parse_args()

    written = generate(
        clients_dir=Path(args.clients_dir),
        output_dir=Path(args.output_dir),
        client=args.client,
    )
    for p in written:
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
