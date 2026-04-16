from __future__ import annotations

import re
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run_frontend_critical_e2e.sh"


def _mktemp_templates(script_text: str) -> list[str]:
    templates = re.findall(r"mktemp\s+([^\s)]+)", script_text)
    return [template.strip("\"'") for template in templates]


def test_critical_e2e_runner_uses_bsd_compatible_mktemp_templates() -> None:
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    templates = _mktemp_templates(script_text)

    assert templates, "Expected mktemp template usage in critical e2e runner"
    assert len(templates) >= 3

    for template in templates:
        assert template.count("XXXXXX") == 1
        assert template.endswith("XXXXXX")


def test_critical_e2e_runner_does_not_append_suffix_after_x_placeholders() -> None:
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    templates = _mktemp_templates(script_text)

    for template in templates:
        assert not re.search(r"XXXXXX\.[A-Za-z0-9]+$", template)


def test_critical_e2e_runner_uses_socket_bind_port_guard_not_http_probe() -> None:
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "port_is_free()" in script_text
    assert "sock.bind((\"127.0.0.1\", port))" in script_text
    assert "if ! port_is_free \"$E2E_API_PORT\"; then" in script_text
    assert "if ! port_is_free \"$E2E_WEB_PORT\"; then" in script_text
    assert "if curl -fsS \"http://127.0.0.1:${E2E_API_PORT}/health\"" not in script_text
    assert "if curl -fsS \"http://127.0.0.1:${E2E_WEB_PORT}\"" not in script_text
