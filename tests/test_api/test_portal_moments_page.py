"""Unit 7 portal-moments shell + JS bootstrap tests.

Most of this file is pure-static assertions against the rendered template
HTML and the static JS file — no Supabase, no Postgres, no fixtures. The
goal is to lock in the contract that Unit 7 promised:

  * /portal/<slug> serves the new portal_moments.html template.
  * CSP header matches Unit 6's policy.
  * No filter chips / no load-more / no active-sessions / no awaiting-input
    pane / no narrative-intro section (R1.2 negatives).
  * JS bootstrap points at /v1/portal/<slug>/moments + /v1/portal/<slug>/stream.
  * 50-row cap baked into the JS.
  * R3.1 session-tag rendering (covered through the moments REST endpoint
    server-side; cross-checked via a unit call to _moment_session_tag).
  * R-Schema-2 class mapping ("k-moment k-mk-cost_milestone", etc.) covered
    by string presence in the JS row builder.
  * R-Live-3 ?since=<event_id> reconnect path referenced in JS.
  * R-Auth-4 401 redirect to /login referenced in JS.
  * T4 textContent (not innerHTML) on title insertion.
  * Smoke: portal_phase2.html no longer present under portal/templates/ or src/.

The one live-integration test (test_portal_shell_renders_moments_template)
uses the api_client + test_tenant fixtures and falls back to the regular
conftest skip when Supabase is unreachable.

Plan: docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md
Spec: §"Unit 7: Filterless moments-timeline frontend".
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import httpx
import pytest


# ---------------------------------------------------------------------------
# File paths (resolve once, used by every static assertion below).
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = REPO_ROOT / "portal" / "templates" / "portal_moments.html"
JS_PATH = REPO_ROOT / "portal" / "static" / "portal_moments.js"


@pytest.fixture(scope="module")
def template_text() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def js_text() -> str:
    return JS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Smoke: the artifacts exist where the rest of the unit expects them.
# ---------------------------------------------------------------------------


def test_template_file_exists() -> None:
    assert TEMPLATE_PATH.is_file(), TEMPLATE_PATH


def test_js_file_exists() -> None:
    assert JS_PATH.is_file(), JS_PATH


# ---------------------------------------------------------------------------
# Template shape: cost-ledger header, timeline container, JS bootstrap.
# (Happy-path content assertion from plan §Unit 7 Test Scenarios.)
# ---------------------------------------------------------------------------


def test_template_extends_base(template_text: str) -> None:
    """U7 template extends base.html per the plan §Patterns to follow."""
    assert '{% extends "base.html" %}' in template_text


def test_template_renders_cost_ledger_header(template_text: str) -> None:
    """Three numerics labelled today / this week / this month."""
    lower = template_text.lower()
    assert 'id="cost-today"' in template_text
    assert 'id="cost-week"' in template_text
    assert 'id="cost-month"' in template_text
    assert "today" in lower
    assert "this week" in lower
    assert "this month" in lower


def test_template_renders_empty_timeline_container(template_text: str) -> None:
    """Timeline container present, JS will populate on load."""
    assert 'id="timeline"' in template_text
    # log-stream is the reused landing-page CSS vocabulary class.
    assert "log-stream" in template_text


def test_template_loads_external_js_bootstrap(template_text: str) -> None:
    """JS lives at /static/portal_moments.js (CSP forbids inline)."""
    assert '<script src="/static/portal_moments.js">' in template_text


def test_template_has_no_inline_script_tags(template_text: str) -> None:
    """CSP: no inline <script>...</script> blocks. T4 + Hard rule."""
    # The only allowed <script> tag is the external src= one above.
    # Count inline script-open tags (no src attribute on the same line).
    import re

    inline = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>", template_text)
    assert inline == [], f"Inline scripts present: {inline}"


def test_template_data_slug_attribute_present(template_text: str) -> None:
    """JS reads SLUG from data-slug on <main>."""
    assert 'data-slug="{{ slug }}"' in template_text


# ---------------------------------------------------------------------------
# R1.2 negatives: NO filter chips, NO load-more, NO active-sessions card,
# NO awaiting-input pane, NO narrative-intro section.
# ---------------------------------------------------------------------------


def test_template_has_no_filter_chips(template_text: str) -> None:
    """R1.2: filter-chip UI removed."""
    assert "filter-chips" not in template_text
    assert "chip-row" not in template_text
    # "chip" appears in some unrelated contexts ("role-chip"), but the
    # specific filter-chip class from phase2 is gone.
    assert "class=\"chip" not in template_text
    assert "is-active" not in template_text or "chip" not in template_text


def test_template_has_no_load_more_button(template_text: str) -> None:
    """R1.2: load-more / pager removed."""
    assert "load more" not in template_text.lower()
    assert "load-more" not in template_text.lower()
    assert 'id="audit-prev"' not in template_text
    assert 'id="audit-next"' not in template_text


def test_template_has_no_active_sessions_card(template_text: str) -> None:
    """R1.2: active-sessions card removed."""
    assert "active-sessions" not in template_text.lower()
    assert "active sessions" not in template_text.lower()


def test_template_has_no_awaiting_input_pane(template_text: str) -> None:
    """R1.2: awaiting-input pane removed."""
    assert "awaiting-input" not in template_text.lower()
    assert "awaiting input" not in template_text.lower()


def test_template_has_no_narrative_intro(template_text: str) -> None:
    """R1.2: narrative-intro section removed."""
    assert "narrative-intro" not in template_text.lower()
    assert "narrative intro" not in template_text.lower()


def test_template_has_no_reports_list(template_text: str) -> None:
    """R1.2 (implied by single-page layout): reports-list section removed."""
    assert 'id="reports-list"' not in template_text


# ---------------------------------------------------------------------------
# R2: 50-row hard cap referenced in the JS.
# ---------------------------------------------------------------------------


def test_js_references_50_row_cap(js_text: str) -> None:
    """R2 hard cap: 50 newest moments only."""
    assert "TIMELINE_CAP = 50" in js_text


# ---------------------------------------------------------------------------
# R-Live-1 + R-Live-2: JS bootstrap points at the moments REST + SSE stream.
# ---------------------------------------------------------------------------


def test_js_fetches_moments_endpoint(js_text: str) -> None:
    """JS bootstraps via GET /v1/portal/<slug>/moments."""
    assert "/v1/portal/" in js_text
    assert "/moments" in js_text


def test_js_connects_sse_stream(js_text: str) -> None:
    """JS opens an EventSource at /v1/portal/<slug>/stream."""
    assert "EventSource(" in js_text
    assert "/stream" in js_text


def test_js_filters_timeline_eligible_kinds_clientside(js_text: str) -> None:
    """R-Live-2: client-side filter for timeline-eligible kinds.

    Set must match portal.py TIMELINE_ELIGIBLE_KINDS — explicit sync comment.
    """
    # Sync-comment present (so future drift gets flagged in code-review).
    assert "TIMELINE_ELIGIBLE_KINDS" in js_text
    # Every member of the server-side set is referenced.
    for kind in [
        "moment",
        "session_start",
        "session_end",
        "review_required",
        "review_approve",
        "review_reject",
        "sla_breach",
        "render",
        "promotion",
    ]:
        assert kind in js_text, f"missing client-side kind filter: {kind}"


def test_js_clientside_kinds_match_server(js_text: str) -> None:
    """The client filter set is the same membership as the server's set."""
    from src.api.routers.portal import TIMELINE_ELIGIBLE_KINDS as SERVER_KINDS
    for kind in SERVER_KINDS:
        assert kind in js_text


# ---------------------------------------------------------------------------
# R3.1: session-tag formatting. The server already computes session_tag, but
# the JS sessionTagFrom() fallback exercises the same logic against
# metadata.lane + metadata.variant.
# ---------------------------------------------------------------------------


def test_js_session_tag_uses_dot_separator(js_text: str) -> None:
    """R3.1: <lane>·<variant> with mid-dot separator."""
    # mid-dot character (U+00B7).
    assert "·" in js_text


def test_moment_session_tag_lane_only() -> None:
    """R3.1 fallback: lane-only -> bare lane name."""
    from src.api.routers.portal import _moment_session_tag

    assert _moment_session_tag({"lane": "marketing_audit"}) == "marketing_audit"


def test_moment_session_tag_lane_and_variant() -> None:
    """R3.1: lane + variant -> 'marketing_audit·v007'."""
    from src.api.routers.portal import _moment_session_tag

    tag = _moment_session_tag({"lane": "marketing_audit", "variant": "v007"})
    assert tag == "marketing_audit·v007"


# ---------------------------------------------------------------------------
# R-Schema-2: kind/moment_kind → class mapping. The JS row builder emits
# "k-<kind> k-mk-<moment_kind>" — verify class strings present.
# ---------------------------------------------------------------------------


def test_js_row_builder_emits_kind_class(js_text: str) -> None:
    """Class string 'k-' prefix appears in row builder."""
    assert '"k-" + safeClass(kind)' in js_text


def test_js_row_builder_emits_moment_kind_class(js_text: str) -> None:
    """Class string 'k-mk-' prefix appears when moment_kind is set."""
    assert '"k-mk-" + safeClass(momentKind)' in js_text


def test_template_defines_cost_milestone_class_styling(template_text: str) -> None:
    """k-mk-cost_milestone styled to dim ink-500 per R-Schema-2 mapping."""
    assert "k-mk-cost_milestone" in template_text


def test_template_defines_deliverable_ready_class_styling(template_text: str) -> None:
    """k-mk-deliverable_ready styled to lime per R-Schema-2 mapping."""
    assert "k-mk-deliverable_ready" in template_text


def test_template_defines_review_required_class_styling(template_text: str) -> None:
    """k-review_required styled to warm per R-Schema-2 mapping."""
    assert "k-review_required" in template_text


def test_template_unrecognized_default_dim(template_text: str) -> None:
    """Default row colour cascade puts unrecognized rows at dim ink-300/500.

    Implementation: a.log-line base colour is var(--ink-300); any kind class
    that doesn't match the lime/warm cascades inherits that default.
    """
    # The base anchor declares the default colour explicitly.
    assert "a.log-line" in template_text
    assert "color: var(--ink-300)" in template_text


# ---------------------------------------------------------------------------
# review_required badge (R3 + plan inheritance).
# ---------------------------------------------------------------------------


def test_template_defines_badge_action_style(template_text: str) -> None:
    """review_required rows get the 'needs review' badge."""
    assert "badge-action" in template_text


def test_js_inserts_needs_review_badge_for_review_required(js_text: str) -> None:
    """JS only injects the badge for kind === 'review_required'."""
    assert '"needs review"' in js_text
    assert 'kind === "review_required"' in js_text


# ---------------------------------------------------------------------------
# R-Live-3: SSE reconnect backfills via ?since=<event_id>.
# ---------------------------------------------------------------------------


def test_js_reconnect_uses_since_param(js_text: str) -> None:
    """R-Live-3: backfillSinceLast() constructs ?since=<last_seen_event_id>."""
    assert "?since=" in js_text
    assert "lastEventId" in js_text or "last_event_id" in js_text


# ---------------------------------------------------------------------------
# R-Auth-4: 401 → /login redirect.
# ---------------------------------------------------------------------------


def test_js_redirects_to_login_on_401(js_text: str) -> None:
    """R-Auth-4: window.location = '/login' on 401 from the auth-probe."""
    assert 'window.location = "/login"' in js_text
    assert "401" in js_text


def test_js_auth_probe_uses_moments_limit_1(js_text: str) -> None:
    """The auth-probe is intentionally lightweight (limit=1 row)."""
    assert "limit=1" in js_text


# ---------------------------------------------------------------------------
# T4: textContent (not innerHTML) for moment title insertion.
# ---------------------------------------------------------------------------


def test_js_uses_text_content_for_title(js_text: str) -> None:
    """T4 belt-and-suspenders: title goes in via textContent, not innerHTML."""
    assert "title.textContent" in js_text


def test_js_does_not_assign_inner_html_for_titles(js_text: str) -> None:
    """No innerHTML assignment on the .title node.

    innerHTML appears in the JS at clear/render-skeleton points (where the
    string is hard-coded literal, no user input) but never on a node carrying
    moment title text.
    """
    # The only innerHTML assignments are the clear-and-rebuild paths in
    # renderTimelineFromRest and renderCostLedger (literal empty string +
    # static markup). Guard against accidental use on user-input nodes.
    assert "title.innerHTML" not in js_text


# ---------------------------------------------------------------------------
# Interaction state strings present in the JS.
# ---------------------------------------------------------------------------


def test_js_empty_state_literal_copy(js_text: str) -> None:
    """R1.2 / Interaction States: literal empty-new-client copy."""
    expected = "No moments yet. Activity will appear here as agents work for you."
    assert expected in js_text


def test_js_partial_load_literal_copy(js_text: str) -> None:
    """Interaction States: partial-load row when has_more=true."""
    assert "Showing newest" in js_text
    assert "older history via ?before=" in js_text


def test_template_has_reconnect_indicator(template_text: str) -> None:
    """SSE-disconnected indicator at the bottom of the timeline."""
    assert "reconnect-indicator" in template_text
    assert "reconnecting" in template_text.lower()


def test_template_skeleton_state_six_rows(template_text: str) -> None:
    """loading-from-REST: 6 skeleton .log-line placeholders."""
    assert template_text.count("skeleton-line") >= 6


# ---------------------------------------------------------------------------
# Cost-ledger header states.
# ---------------------------------------------------------------------------


def test_js_renders_cost_unavailable_on_null_rollup(js_text: str) -> None:
    """ledger-bridge-down: 'cost data unavailable' dim row."""
    assert "cost data unavailable" in js_text


# ---------------------------------------------------------------------------
# Smoke: portal_phase2.html retired from source tree.
# ---------------------------------------------------------------------------


def test_phase2_template_removed_from_source_tree() -> None:
    """R-Schema retirement of phase2 — file should not exist anywhere under
    portal/templates/ or be referenced from src/.
    """
    phase2_template = REPO_ROOT / "portal" / "templates" / "portal_phase2.html"
    assert not phase2_template.exists(), (
        f"portal_phase2.html should be retired but still exists at {phase2_template}"
    )


def test_no_phase2_references_in_source() -> None:
    """grep -rn 'portal_phase2' portal/templates/ src/ returns 0 hits."""
    result = subprocess.run(
        [
            "grep",
            "-rn",
            "portal_phase2",
            str(REPO_ROOT / "portal" / "templates"),
            str(REPO_ROOT / "src"),
        ],
        capture_output=True,
        text=True,
    )
    # grep exit code 1 = no matches found (success for us).
    assert result.returncode == 1, (
        f"portal_phase2 still referenced in source:\n{result.stdout}"
    )


# ---------------------------------------------------------------------------
# Live integration: shell renders + CSP header attached.
# Uses the same conftest skip mechanism as other test_api/* files.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_portal_shell_renders_moments_template(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """GET /portal/<slug> returns 200 + the U7 template body."""
    slug = test_tenant["client_slug"]
    r = await api_client.get(f"/portal/{slug}")
    assert r.status_code == 200
    # Moments-page markers.
    assert 'id="timeline"' in r.text
    assert "moments timeline" in r.text.lower()
    # Slug rendered for personalization.
    assert slug in r.text
    # External JS bootstrap referenced.
    assert "/static/portal_moments.js" in r.text


@pytest.mark.asyncio
async def test_portal_shell_attaches_csp_header(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """U7 inherits Unit 6's CSP shape — same _TRANSCRIPT_CSP string."""
    r = await api_client.get(f"/portal/{test_tenant['client_slug']}")
    assert r.status_code == 200
    csp = r.headers.get("content-security-policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    # 'unsafe-inline' scoped to style only (Unit 6 contract); F1 added
    # fonts.googleapis.com to style-src for the Inter / JetBrains Mono CDN.
    assert "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com" in csp
    assert "font-src 'self' https://fonts.gstatic.com" in csp
