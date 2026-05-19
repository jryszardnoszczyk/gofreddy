"""Gate-1 substrate: integration tests for the in-loop reviewer-assist
fitness gate (R22).

Per CE-review adversarial finding ADV-001: `evaluate_compliance` was
defined + exported but had zero production call sites — variants
could pass through evolution with Art. 14 hard-block prose intact.
`src/compliance/lane_gate.py` is the integration point; this test
suite pins the contract a future regression would have to break to
slip a non-compliant variant through evolution.

Rule 9: each test names the architectural property it pins (gate
fires when configured / gate is opt-out when unconfigured / sidecar
gets written / hard_block discards / soft_warn passes through).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.compliance.lane_gate import (
    ComplianceGateOutcome,
    apply_compliance_gate,
)


# ---------------------------------------------------------------------------
# Skip semantics — opt-out by default
# ---------------------------------------------------------------------------


def test_gate_skipped_when_no_rule_set_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default: gate is opt-out. Without an explicit rule_set_name
    AND no EVOLUTION_RULE_SET env, the gate returns SKIPPED + does
    NOT write a sidecar. This preserves the v1 substrate's pre-gate
    behavior for lanes that don't yet have a configured rule_set."""
    monkeypatch.delenv("EVOLUTION_RULE_SET", raising=False)
    variant_dir = tmp_path / "v_test"
    drafts = variant_dir / "drafts"
    drafts.mkdir(parents=True)
    (drafts / "article.md").write_text(
        "Najlepszy zabieg w Warszawie. Gwarantujemy efekt.", encoding="utf-8",
    )
    outcome, result = apply_compliance_gate(
        variant_dir, lane="article_engine", rule_set_name=None,
    )
    assert outcome == ComplianceGateOutcome.SKIPPED
    assert result is None
    assert not (variant_dir / "compliance-meta.json").exists()


def test_gate_reads_rule_set_from_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When EVOLUTION_RULE_SET is set in env, the gate fires using
    that rule_set. This is the harness opt-in path: a fixture's env
    block or the lane's configure_env exports the env, the gate
    picks it up."""
    monkeypatch.setenv("EVOLUTION_RULE_SET", "medical_pl")
    variant_dir = tmp_path / "v_test"
    drafts = variant_dir / "drafts"
    drafts.mkdir(parents=True)
    (drafts / "article.md").write_text(
        "Najlepszy zabieg w Warszawie. Gwarantujemy efekt.", encoding="utf-8",
    )
    outcome, result = apply_compliance_gate(
        variant_dir, lane="article_engine", rule_set_name=None,
    )
    assert outcome == ComplianceGateOutcome.HARD_BLOCK
    assert result is not None
    assert result.verdict == "hard_block"


# ---------------------------------------------------------------------------
# Hard-block path — variant discard signal
# ---------------------------------------------------------------------------


def test_hard_block_verdict_signals_discard(tmp_path: Path) -> None:
    """Pin: when verdict='hard_block', outcome is HARD_BLOCK so the
    caller in evolve.py knows to discard the variant. This is the
    load-bearing safety property — without it, R22 gate-1 has no
    operational effect on the evolution loop."""
    variant_dir = tmp_path / "v_klinika"
    drafts = variant_dir / "drafts"
    drafts.mkdir(parents=True)
    (drafts / "article.md").write_text(
        "Najlepszy zabieg w Warszawie. Cena zabiegu mezoterapii to tylko 500 zł. "
        "Gwarantujemy 100% skuteczności.",
        encoding="utf-8",
    )
    outcome, result = apply_compliance_gate(
        variant_dir, lane="article_engine", rule_set_name="medical_pl",
    )
    assert outcome == ComplianceGateOutcome.HARD_BLOCK
    assert result is not None
    assert result.verdict == "hard_block"
    # Multiple rules should fire on this contrived violation-stack
    assert len(result.flags) >= 2


# ---------------------------------------------------------------------------
# Soft-warn path — passes through but persists to sidecar
# ---------------------------------------------------------------------------


def test_soft_warn_verdict_does_not_signal_discard(tmp_path: Path) -> None:
    """Pin: soft_warn verdict means the gate persists the flag but
    does NOT signal discard. Per §Compliance Posture: gate-1 is
    fitness only; the actual safety weight lives at gate-2 (U7
    pre-publish review). soft_warn at gate-1 = reviewer-sees-flag
    at gate-2, not 'evolution rejects.'"""
    variant_dir = tmp_path / "v_klinika_soft"
    drafts = variant_dir / "drafts"
    drafts.mkdir(parents=True)
    # Pain-free claim is soft_warn in medical_pl
    (drafts / "article.md").write_text(
        "Zabieg bezbolesny — minimal discomfort under local anaesthesia.",
        encoding="utf-8",
    )
    outcome, result = apply_compliance_gate(
        variant_dir, lane="article_engine", rule_set_name="medical_pl",
    )
    assert outcome == ComplianceGateOutcome.SOFT_WARN
    assert result is not None
    assert result.verdict == "soft_warn"


# ---------------------------------------------------------------------------
# Clean path — no flags but sidecar still written
# ---------------------------------------------------------------------------


def test_clean_verdict_writes_audit_sidecar(tmp_path: Path) -> None:
    """Pin: when verdict='clean', the gate still writes
    compliance-meta.json. This is the audit-trail property: even a
    clean variant carries evidence-of-evaluation, so the reviewer
    can see that the gate ran + nothing fired."""
    variant_dir = tmp_path / "v_clean"
    drafts = variant_dir / "drafts"
    drafts.mkdir(parents=True)
    (drafts / "article.md").write_text(
        "Mezoterapia to zabieg polegający na wprowadzeniu pod skórę "
        "preparatów rewitalizujących. Procedura wykonywana jest przez "
        "lekarza specjalistę dermatologii estetycznej.",
        encoding="utf-8",
    )
    outcome, result = apply_compliance_gate(
        variant_dir, lane="article_engine", rule_set_name="medical_pl",
    )
    assert outcome == ComplianceGateOutcome.CLEAN
    assert result is not None
    assert result.verdict == "clean"
    sidecar = variant_dir / "compliance-meta.json"
    assert sidecar.is_file()
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["verdict"] == "clean"
    assert payload["flags"] == []


def test_audit_sidecar_captures_full_compliance_result(tmp_path: Path) -> None:
    """Pin: the sidecar JSON carries the full ComplianceResult shape
    (verdict + flags[] with rule_id/severity/matched_text/prose) so
    the pre-publish reviewer at gate-2 has actionable data."""
    variant_dir = tmp_path / "v_sidecar"
    drafts = variant_dir / "drafts"
    drafts.mkdir(parents=True)
    (drafts / "article.md").write_text(
        "Cena zabiegu tylko 500 zł.", encoding="utf-8",
    )
    apply_compliance_gate(
        variant_dir, lane="article_engine", rule_set_name="medical_pl",
    )
    sidecar = variant_dir / "compliance-meta.json"
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["verdict"] == "hard_block"
    assert len(payload["flags"]) >= 1
    flag = payload["flags"][0]
    for required in ("rule_id", "severity", "rule_set_name", "matched_text", "prose"):
        assert required in flag, f"sidecar flag missing {required!r}"
    assert payload["rule_set_name"] == "medical_pl"
    assert payload["lane"] == "article_engine"


# ---------------------------------------------------------------------------
# Lane-deliverable convention
# ---------------------------------------------------------------------------


def test_gate_reads_deliverables_per_lane_glob_site_engine(tmp_path: Path) -> None:
    """Pin: site_engine deliverables are *.html files under drafts/;
    the gate's per-lane glob map must read them, not *.md."""
    variant_dir = tmp_path / "v_site"
    drafts = variant_dir / "drafts"
    drafts.mkdir(parents=True)
    (drafts / "hero.html").write_text(
        "<section><h1>Najlepszy zabieg w Warszawie</h1></section>",
        encoding="utf-8",
    )
    outcome, _ = apply_compliance_gate(
        variant_dir, lane="site_engine", rule_set_name="medical_pl",
    )
    assert outcome == ComplianceGateOutcome.HARD_BLOCK


def test_gate_reads_storyboard_json_deliverables(tmp_path: Path) -> None:
    """Pin: storyboard deliverables are stories/*.json. Gate must
    concatenate JSON text (verbatim) so prose embedded in scene
    captions / voiceover scripts still fires the regex."""
    variant_dir = tmp_path / "v_story"
    stories = variant_dir / "stories"
    stories.mkdir(parents=True)
    (stories / "story-1.json").write_text(
        json.dumps({
            "story_id": "s1",
            "scenes": [
                {"prompt": "Hero shot", "voiceover": "Gwarantujemy efekt po jednej sesji."}
            ],
        }),
        encoding="utf-8",
    )
    outcome, _ = apply_compliance_gate(
        variant_dir, lane="storyboard", rule_set_name="medical_pl",
    )
    assert outcome == ComplianceGateOutcome.HARD_BLOCK


def test_unmapped_lane_returns_skipped(tmp_path: Path) -> None:
    """Pin: lanes without a deliverable-glob entry in the gate's map
    return SKIPPED. This bounds the gate's blast radius — adding a
    lane to gate-1 coverage is an explicit dict-edit, not an
    accident-of-grep on adjacent lane shapes."""
    variant_dir = tmp_path / "v_unknown"
    variant_dir.mkdir(parents=True)
    outcome, result = apply_compliance_gate(
        variant_dir, lane="some_future_lane", rule_set_name="medical_pl",
    )
    assert outcome == ComplianceGateOutcome.SKIPPED
    assert result is None
    assert not (variant_dir / "compliance-meta.json").exists()


def test_empty_variant_dir_returns_skipped(tmp_path: Path) -> None:
    """Pin: variant dir with no deliverable files returns SKIPPED
    rather than firing on empty text. The gate is a content check,
    not a 'variant produced nothing' detector."""
    variant_dir = tmp_path / "v_empty"
    (variant_dir / "drafts").mkdir(parents=True)
    outcome, _ = apply_compliance_gate(
        variant_dir, lane="article_engine", rule_set_name="medical_pl",
    )
    assert outcome == ComplianceGateOutcome.SKIPPED


# ---------------------------------------------------------------------------
# Error path — invalid rule_set name
# ---------------------------------------------------------------------------


def test_unknown_rule_set_returns_skipped_not_raises(tmp_path: Path) -> None:
    """Pin: a typo in rule_set_name (or a missing YAML) fails SAFE —
    returns SKIPPED rather than raising. Operator gets a logged
    error; the variant proceeds through evolution as if no gate
    were configured. Fail-safe is correct here: a misconfigured gate
    that hard-blocked every variant would halt evolution entirely."""
    variant_dir = tmp_path / "v_typo"
    drafts = variant_dir / "drafts"
    drafts.mkdir(parents=True)
    (drafts / "article.md").write_text("Najlepszy zabieg.", encoding="utf-8")
    outcome, result = apply_compliance_gate(
        variant_dir, lane="article_engine", rule_set_name="no_such_checklist",
    )
    assert outcome == ComplianceGateOutcome.SKIPPED
    assert result is None
