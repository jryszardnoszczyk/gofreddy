"""Auto-generate a per-run markdown inventory of app surfaces.

All introspection runs in subprocesses to avoid import-time pollution of the
orchestrator's os.environ (cli/freddy/config.py calls load_dotenv() at import).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

MAX_SUMMARY_CHARS = 200
_CLI_SCRIPT = r"""
import json, inspect
from cli.freddy.main import app as root

def walk(app, path):
    out = []
    for cmd in getattr(app, "registered_commands", []) or []:
        name = cmd.name or (cmd.callback.__name__ if cmd.callback else "?")
        doc = (cmd.callback.__doc__ or "").strip().splitlines()[0] if cmd.callback else ""
        out.append({"path": path + [name], "doc": doc})
    for group in getattr(app, "registered_groups", []) or []:
        gname = group.name or ""
        gdoc = (group.typer_instance.info.help or "").strip().splitlines()[0]
        out.append({"path": path + [gname], "doc": gdoc, "group": True})
        out.extend(walk(group.typer_instance, path + [gname]))
    return out

print(json.dumps(walk(root, ["freddy"])))
"""


def generate(wt: Path, out_path: Path) -> None:
    """Write an inventory markdown file to `out_path`."""
    sections = [
        "# App inventory (auto-generated)\n",
        _cli_section(wt),
        _api_section(wt),
        _frontend_section(wt),
        _autoresearch_section(wt),
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def _truncate(text: str) -> str:
    text = text.strip()
    return text if len(text) <= MAX_SUMMARY_CHARS else text[: MAX_SUMMARY_CHARS - 1] + "…"


def _cli_section(wt: Path) -> str:
    proc = subprocess.run(
        [str(wt / ".venv" / "bin" / "python"), "-c", _CLI_SCRIPT],
        cwd=wt, capture_output=True, text=True, check=False, timeout=30,
    )
    if proc.returncode != 0:
        return f"## CLI\n\n_introspection failed: {proc.stderr.strip()[:300]}_"
    try:
        items = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return f"## CLI\n\n_json parse failed: {exc}_"
    lines = ["## CLI"]
    for item in items:
        label = " ".join(item["path"])
        tag = " (group)" if item.get("group") else ""
        lines.append(f"- `{label}`{tag} — {_truncate(item.get('doc', ''))}")
    return "\n".join(lines)


def _api_section(wt: Path) -> str:
    export_script = wt / "scripts" / "export_openapi.py"
    if not export_script.is_file():
        return "## API\n\n_scripts/export_openapi.py missing_"
    env = os.environ.copy()
    env["PATH"] = f"{wt / '.venv' / 'bin'}:{env.get('PATH', '')}"
    spec_path = wt / "harness-openapi.tmp.json"
    env["OPENAPI_OUTPUT_PATH"] = str(spec_path)
    proc = subprocess.run(
        [str(wt / ".venv" / "bin" / "python"), str(export_script)],
        cwd=wt, env=env, capture_output=True, text=True, check=False, timeout=60,
    )
    if proc.returncode != 0 or not spec_path.is_file():
        return f"## API\n\n_export_openapi failed: {proc.stderr.strip()[:300]}_"
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    finally:
        spec_path.unlink(missing_ok=True)

    lines = ["## API"]
    for path, methods in sorted((spec.get("paths") or {}).items()):
        for method, meta in sorted(methods.items()):
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            summary = meta.get("summary") or meta.get("operationId") or ""
            lines.append(f"- `{method.upper()} {path}` — {_truncate(summary)}")
    return "\n".join(lines)


def _frontend_section(wt: Path) -> str:
    routes_ts = wt / "frontend" / "src" / "lib" / "routes.ts"
    if not routes_ts.is_file():
        return "## Frontend\n\n_routes.ts missing — placeholder_"
    text = routes_ts.read_text(encoding="utf-8")
    lines = ["## Frontend"]
    obj_match = re.search(r"export const ROUTES\s*=\s*\{(.*?)\}\s*as const", text, re.DOTALL)
    if obj_match:
        for name, path in re.findall(r"(\w+)\s*:\s*\"([^\"]+)\"", obj_match.group(1)):
            lines.append(f"- `{path}` — {name}")
    legacy = re.search(r"export const LEGACY_PRODUCT_ROUTES\s*=\s*\[(.*?)\]\s*as const", text, re.DOTALL)
    if legacy:
        for path in re.findall(r"\"([^\"]+)\"", legacy.group(1)):
            lines.append(f"- `{path}` — legacy product route")
    return "\n".join(lines)


def _autoresearch_section(wt: Path) -> str:
    root = wt / "autoresearch"
    if not root.is_dir():
        return "## Autoresearch\n\n_no autoresearch programs detected_"
    lines = ["## Autoresearch"]
    for entry in sorted(root.glob("*.py")):
        if entry.name in {"__init__.py"} or entry.name.startswith("_"):
            continue
        summary = _first_docstring_line(entry)
        lines.append(f"- `autoresearch/{entry.name}` — {_truncate(summary)}")

    programs = root / "archive" / "current_runtime" / "programs"
    if programs.is_dir():
        for prog in sorted(programs.glob("*.md")):
            header = _first_header_line(prog)
            lines.append(f"- `autoresearch/archive/current_runtime/programs/{prog.name}` — {_truncate(header)}")

    if len(lines) == 1:
        return "## Autoresearch\n\n_no autoresearch programs detected_"
    return "\n".join(lines)


def _first_docstring_line(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    match = re.search(r'"""(.+?)"""', text, re.DOTALL)
    if match:
        return match.group(1).strip().splitlines()[0] if match.group(1).strip() else ""
    return ""


def _first_header_line(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("#"):
                return line.lstrip("#").strip()
    except OSError:
        pass
    return ""
