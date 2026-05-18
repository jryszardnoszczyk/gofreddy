"""Per-client config object (R26) for the Content Engine lanes.

A `ClientConfig` is the primary onboarding interface for the content
engine. Each client's voice + reviewer routing + enabled channels + brand
assets + regulatory posture lives in `clients/<slug>/client.yaml`, gets
loaded by `src.clients.loader.load_client_config(slug)`, and is consumed
by every Content Engine lane (article_engine, image_engine, ad_engine,
site_engine, storyboard, x_engine, linkedin_engine, marketing_audit).

This module is the **schema only** — frozen Pydantic models with
validation rules. Loading + run-manifest snapshot + drift detection
lives in `src.clients.loader`.

Relationship to `src.clients.models.Client` (existing): `Client` carries
low-level workspace metadata (slug + domain + status + created_at) for
the audit pipeline; `ClientConfig` extends with content-engine-specific
fields. They coexist in v1 with a cross-reference by slug; the existing
`clients/<slug>/config.json` is unchanged. See U2 in
docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md for the
coexistence rationale.

v1 archetype roster (cut from 11 to 4 by TD-56, 2026-05-18): the
substrate accepts any archetype string at runtime; the Literal narrows
to what's actually exercised in v1. New archetypes land as 1-line
Literal edits when their first client onboards. The four:
- b2b_saas — gofreddy.ai canonical; site_engine SE-1..8 calibration target
- b2c_aesthetics — Klinika, first onboarded example
- b2b_regulated — DWF, first onboarded example
- b2b_tech — architectural-validation stub (U19); not onboarded
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Archetype = Literal["b2b_saas", "b2c_aesthetics", "b2b_regulated", "b2b_tech"]
BrandStrictness = Literal["strict", "permissive"]
ReviewerRole = Literal["primary", "secondary"]


class LocaleConfig(BaseModel):
    """Google + content locale config (per TD-33).

    SerpAPI + GSC providers consume `gl/hl/google_domain` directly;
    judges and content-generation prompts consume `country/city` for
    inline localization references. `requires_diacritic_normalization`
    is opt-in (Polish + Czech + Romanian style); `requires_native_judge`
    flags non-European languages where outer-judge prose evaluation
    requires a native-speaker rubric calibration pass."""

    model_config = ConfigDict(frozen=True, extra="allow")

    gl: str = Field(default="en", description="Google country code (e.g. 'en', 'pl')")
    hl: str = Field(default="en", description="Google interface language")
    google_domain: str = Field(default="google.com")
    country: str = Field(default="US")
    city: str = Field(default="San Francisco,CA,US")
    requires_diacritic_normalization: bool = Field(default=False)
    requires_native_judge: bool = Field(default=False)


class SiteEngineConfig(BaseModel):
    """Per-client site_engine config (per TD-27 + TD-28: section-level v1)."""

    model_config = ConfigDict(frozen=True, extra="allow")

    target_url: str = Field(..., description="Client's live site URL")
    sections_in_scope: list[str] = Field(
        default_factory=lambda: ["hero", "value_prop", "social_proof", "faq", "cta", "pricing"],
        description="Section keys site_engine mutates; full-page rewrites not built in v1.",
    )
    brand_tokens: Path = Field(
        ..., description="Path to tokens.json (colors/typefaces/spacing/motion)."
    )
    codex_fallback: bool = Field(
        default=True,
        description="Regulated-vertical fallback to claude/sonnet when codex cyber filter rejects.",
    )
    weekly_section_target: int = Field(
        default=2,
        ge=0,
        description="Section-rewrite cap per week; lower than article/x/linkedin throughput.",
    )


class PrePublishReviewerConfig(BaseModel):
    """Primary pre-publish reviewer (R26 + D14)."""

    model_config = ConfigDict(frozen=True, extra="allow")

    email: str = Field(..., description="Reviewer email; CODEOWNERS-gated changes")
    display_name: str
    sla: str = Field(..., description="SLA token (e.g. '48h_business_pl')")


class PrePublishReviewerSecondaryConfig(BaseModel):
    """Optional secondary reviewer (per TD-2 revised + D14)."""

    model_config = ConfigDict(frozen=True, extra="allow")

    email: str
    display_name: str
    escalate_at_pct_sla: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Pct of primary SLA elapsed before secondary is paged.",
    )


class BrandAssetsConfig(BaseModel):
    """Brand asset paths (per TD-37). All resolved relative to repo root."""

    model_config = ConfigDict(frozen=True, extra="allow")

    style_guide: Path
    logo: Path
    palette: Path


class BriefConsumptionConfig(BaseModel):
    """Per-client brief consumption settings (R26)."""

    model_config = ConfigDict(frozen=True, extra="allow")

    top_k_per_run: int = Field(default=3, ge=1, description="N briefs read per run (priority-sorted).")


class ClientConfig(BaseModel):
    """The content engine's per-client onboarding contract.

    Versioned YAML at `clients/<slug>/client.yaml`. Frozen at load —
    mid-run mutation is fail-loud at finalize for lineage-affecting
    fields; reviewer-routing fields are carve-outs (see D7).

    The model accepts unknown fields (`extra='allow'`) per the
    marketing-audit lesson: start permissive, tighten after 3-5 real
    runs once schema drift is observed."""

    model_config = ConfigDict(frozen=True, extra="allow")

    # ----- identity -----
    slug: str = Field(..., description="Workspace + URL slug; references existing Client.slug")
    display_name: str

    # ----- archetype + onboarding posture -----
    archetype: Archetype = Field(
        ...,
        description=(
            "v1 enum is intentionally narrow (4 values) — new archetypes are "
            "1-line Literal edits when their first client onboards."
        ),
    )
    archetype_stub_allowed: bool = Field(
        default=False,
        description=(
            "True only for stub/architectural-validation clients (e.g. "
            "_stub_b2b_tech in U19). Excludes the client from D11's "
            "≥1-real-client-fixture-per-archetype CI assertion."
        ),
    )

    # ----- voice / locale / brand tone -----
    voice_persona_ref: str = Field(
        ...,
        description=(
            "Persona slug under voice_personas/<persona_ref>.yaml. Multiple "
            "clients MAY share a persona; consumers verify provenance."
        ),
    )
    locale: LocaleConfig = Field(default_factory=LocaleConfig)
    brand_strictness: BrandStrictness = Field(
        default="strict",
        description=(
            "'strict' fails preflight on missing SVG logo + WOFF2 fonts; "
            "'permissive' warns and accepts PNG + system-font fallback."
        ),
    )
    voice_corpus_consent_required: bool | None = Field(
        default=None,
        description=(
            "Per-client override. When None, defaulted from archetype: "
            "b2c_aesthetics + b2b_regulated → True (private/proprietary "
            "corpora); b2b_saas + b2b_tech → False (public corpora)."
        ),
    )
    source_material_paths: list[Path] | None = Field(
        default=None,
        description=(
            "Article-engine source material under clients/<slug>/source_material/. "
            "Operator-curated. Markdown preferred; PDF via pdf_to_markdown.py."
        ),
    )

    # ----- reviewer-assist -----
    reviewer_assist_checklists: list[str] = Field(
        ...,
        description=(
            "Reviewer-assist YAML names under reviewer_assist/checklists/. "
            "v1 constrains length to 1 (D6 revised per TD-18); multi-rule-set "
            "merge logic deferred to first client onboarding that needs it. "
            "These are reviewer-assist checklists, NOT legal-grade compliance "
            "gates — see §Compliance Posture in the plan."
        ),
    )

    # ----- channels + content scope -----
    enabled_channels: list[str] = Field(
        ...,
        description=(
            "Lane names this client publishes through (e.g. 'article_engine', "
            "'site_engine'). Unknown channels are accepted at v1 (extra='allow') "
            "but logged."
        ),
    )
    enabled_platforms_per_channel: dict[str, list[str]] = Field(default_factory=dict)
    content_denylist: list[str] = Field(
        default_factory=list,
        description=(
            "Substrate-enforced denylist (e.g. Klinika denies clinical_visuals "
            "+ before_after_imagery). Lanes refuse to emit denied content types."
        ),
    )

    # ----- site_engine sub-config -----
    site_engine: SiteEngineConfig | None = Field(
        default=None,
        description="Required when 'site_engine' is in enabled_channels.",
    )

    # ----- pre-publish review (D14) -----
    pre_publish_reviewer: PrePublishReviewerConfig
    pre_publish_reviewer_secondary: PrePublishReviewerSecondaryConfig | None = None
    weekly_publish_target: int = Field(
        ...,
        ge=0,
        description=(
            "Right-sizes engine throughput to reviewer capacity. Lane stops "
            "emitting ship-candidates once met. Resets Monday in client tz."
        ),
    )

    # ----- brand assets + briefs -----
    brand_assets: BrandAssetsConfig
    brief_consumption: BriefConsumptionConfig = Field(default_factory=BriefConsumptionConfig)

    # ----- validators -----

    @field_validator("reviewer_assist_checklists")
    @classmethod
    def _checklists_length_one_in_v1(cls, v: list[str]) -> list[str]:
        """Per D6 revised + TD-18: v1 supports a single rule_set per client.
        Multi-rule-set merge logic deferred until a real client onboards
        with two checklists. Schema accepts a list so v1.5+ migration is
        additive — the constraint enforces v1 scope."""
        if len(v) != 1:
            raise ValueError(
                f"reviewer_assist_checklists must have exactly 1 entry in v1 "
                f"(got {len(v)} entries: {v}). Multi-rule-set merge logic is "
                f"deferred per D6 revised / TD-18."
            )
        return v

    @field_validator("slug")
    @classmethod
    def _slug_is_kebab_or_snake(cls, v: str) -> str:
        if not v or any(c.isspace() for c in v):
            raise ValueError(f"slug must be non-empty with no whitespace; got {v!r}")
        return v

    @model_validator(mode="after")
    def _site_engine_required_if_enabled(self) -> "ClientConfig":
        if "site_engine" in self.enabled_channels and self.site_engine is None:
            raise ValueError(
                "site_engine is in enabled_channels but no site_engine sub-config "
                "is set on the client. Add a site_engine block with target_url, "
                "sections_in_scope, and brand_tokens path."
            )
        return self

    @model_validator(mode="after")
    def _default_voice_corpus_consent_from_archetype(self) -> "ClientConfig":
        """When voice_corpus_consent_required is not set in the YAML, derive
        from archetype: b2c_aesthetics + b2b_regulated default True (private
        corpora); b2b_saas + b2b_tech default False (public corpora).

        Pydantic's frozen=True means we use object.__setattr__ to backfill
        the derived default exactly once at construction."""
        if self.voice_corpus_consent_required is None:
            default = self.archetype in {"b2c_aesthetics", "b2b_regulated"}
            object.__setattr__(self, "voice_corpus_consent_required", default)
        return self

    @model_validator(mode="after")
    def _stub_allowed_only_for_b2b_tech_in_v1(self) -> "ClientConfig":
        """Per the plan's onboarded-vs-demonstrated distinction: v1's only
        stub_allowed archetype is b2b_tech (U19's architectural-validation
        stub). Catches misuse where a real-client config mistakenly carries
        archetype_stub_allowed=True."""
        if self.archetype_stub_allowed and self.archetype != "b2b_tech":
            raise ValueError(
                f"archetype_stub_allowed=True is reserved for b2b_tech in v1 "
                f"(got archetype={self.archetype!r}). Real-client configs must "
                f"set archetype_stub_allowed=False (or omit it)."
            )
        return self


# D7 — fields whose mid-run change fails the finalize step.
LINEAGE_AFFECTING_FIELDS: frozenset[str] = frozenset({
    "archetype",
    "voice_persona_ref",
    "reviewer_assist_checklists",
    "enabled_channels",
    "content_denylist",
    "brand_assets",       # path or contents change → fail
    "site_engine",        # target_url + sections_in_scope live inside
})

# D7 — fields whose mid-run change is logged but DOES NOT fail finalize.
# Reviewer absence (vacation, illness, departure) is a real-world ops event
# that must not destroy a multi-hour evolution run.
REVIEWER_ROUTING_CARVE_OUT_FIELDS: frozenset[str] = frozenset({
    "pre_publish_reviewer",
    "pre_publish_reviewer_secondary",
    "weekly_publish_target",
})


__all__ = [
    "Archetype",
    "BrandStrictness",
    "BrandAssetsConfig",
    "BriefConsumptionConfig",
    "ClientConfig",
    "LocaleConfig",
    "PrePublishReviewerConfig",
    "PrePublishReviewerSecondaryConfig",
    "SiteEngineConfig",
    "LINEAGE_AFFECTING_FIELDS",
    "REVIEWER_ROUTING_CARVE_OUT_FIELDS",
]
