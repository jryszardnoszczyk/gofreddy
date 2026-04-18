"""Scorecard data layer for the QA eval-fix harness.

Replaces ~450 lines of awk state machines in eval_fix_harness.sh with typed
dataclasses and yaml.safe_load() parsing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from harness.config import normalize_id

# Characters that require YAML quoting when they appear in scalar values.
_YAML_NEEDS_QUOTING = re.compile(r"[:\[\]{}&*!|>'\"%@`#,?\\]")


def _yaml_quote(value: str) -> str:
    """Quote a YAML scalar value if it contains special characters.

    Uses double-quote style with internal double-quotes and backslashes escaped.
    Plain scalars that are safe are returned unquoted for readability.
    """
    if not value or _YAML_NEEDS_QUOTING.search(value):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    """A single capability finding from an evaluator scorecard."""

    id: str
    capability: str
    grade: str
    summary: str


@dataclass
class Scorecard:
    """Parsed scorecard with typed fields and computed properties."""

    cycle: int
    track: str | None
    findings: list[Finding]
    evaluator_failed: bool = False
    evaluator_failure_reason: str = ""
    timestamp: str | None = None
    # Body text sections keyed by track letter (or "" for non-track content).
    body_sections: dict[str, str] = field(default_factory=dict, repr=False)

    # -- Computed counts -------------------------------------------------------

    @property
    def pass_count(self) -> int:
        return sum(1 for f in self.findings if f.grade == "PASS")

    @property
    def fail_count(self) -> int:
        return sum(1 for f in self.findings if f.grade == "FAIL")

    @property
    def partial_count(self) -> int:
        return sum(1 for f in self.findings if f.grade == "PARTIAL")

    @property
    def blocked_count(self) -> int:
        return sum(1 for f in self.findings if f.grade == "BLOCKED")

    # -- Parsing ---------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: Path) -> "Scorecard":
        """Parse a scorecard markdown file with YAML frontmatter.

        Expects ``---`` delimiters around the frontmatter block.  Anything
        after the closing ``---`` is captured as body text.
        """
        text = path.read_text(encoding="utf-8")
        return cls.from_text(text)

    @classmethod
    def from_text(cls, text: str) -> "Scorecard":
        """Parse scorecard from its full text content."""
        parts = text.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Scorecard missing YAML frontmatter (expected --- delimiters)")

        frontmatter_raw = parts[1]
        body = parts[2] if len(parts) > 2 else ""

        try:
            data: dict[str, Any] = yaml.safe_load(frontmatter_raw) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Malformed YAML frontmatter: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"YAML frontmatter is not a mapping: {type(data)}")

        findings: list[Finding] = []
        raw_findings = data.get("findings") or []
        if isinstance(raw_findings, list):
            for item in raw_findings:
                if not isinstance(item, dict):
                    continue
                findings.append(
                    Finding(
                        id=normalize_id(str(item.get("id", ""))),
                        capability=str(item.get("capability", "")),
                        grade=str(item.get("grade", "")).upper(),
                        summary=str(item.get("summary", "")),
                    )
                )

        # evaluator_failure_reason may be stored under different keys in
        # track vs merged scorecards.
        efr = data.get("evaluator_failure_reason", "")
        if not efr:
            efr = data.get("evaluator_failure_reasons", "")

        return cls(
            cycle=int(data.get("cycle", 0)),
            track=data.get("track"),
            findings=findings,
            evaluator_failed=bool(data.get("evaluator_failed", False)),
            evaluator_failure_reason=str(efr),
            timestamp=str(data["timestamp"]) if data.get("timestamp") is not None else None,
            body_sections={"": body},
        )

    # -- Merge -----------------------------------------------------------------

    @classmethod
    def merge(cls, scorecards: list["Scorecard"]) -> "Scorecard":
        """Merge multiple track scorecards into one.

        Sums counts via concatenated findings, aggregates evaluator_failed,
        and concatenates body sections keyed by track letter.
        """
        if not scorecards:
            return cls(cycle=0, track=None, findings=[])

        cycle = scorecards[0].cycle
        all_findings: list[Finding] = []
        any_failed = False
        failure_reasons: list[str] = []
        body: dict[str, str] = {}

        for sc in scorecards:
            all_findings.extend(sc.findings)
            if sc.evaluator_failed:
                any_failed = True
                track_label = sc.track or "?"
                failure_reasons.append(
                    f"track-{track_label}: {sc.evaluator_failure_reason}"
                )
            # Collect body sections
            track_key = sc.track or ""
            for _k, v in sc.body_sections.items():
                body[track_key] = v

        return cls(
            cycle=cycle,
            track=None,
            findings=all_findings,
            evaluator_failed=any_failed,
            evaluator_failure_reason="; ".join(failure_reasons) + ("; " if failure_reasons else ""),
            body_sections=body,
        )

    # -- Capping ---------------------------------------------------------------

    def cap(self, max_findings: int) -> tuple["Scorecard", list[str]]:
        """Cap FAIL/PARTIAL findings to *max_findings*, keep PASS/BLOCKED.

        Returns ``(capped_scorecard, deferred_ids)`` where *deferred_ids*
        lists the finding IDs that were dropped.

        Findings are processed in document order.  FAIL and PARTIAL count
        toward the cap; PASS and BLOCKED are always kept.
        """
        kept: list[Finding] = []
        deferred: list[str] = []
        actionable_count = 0

        for f in self.findings:
            if f.grade in ("FAIL", "PARTIAL"):
                if actionable_count < max_findings:
                    kept.append(f)
                    actionable_count += 1
                else:
                    deferred.append(f.id)
            else:
                # PASS, BLOCKED, or anything else — always kept
                kept.append(f)

        capped = Scorecard(
            cycle=self.cycle,
            track=self.track,
            findings=kept,
            evaluator_failed=self.evaluator_failed,
            evaluator_failure_reason=self.evaluator_failure_reason,
            timestamp=self.timestamp,
            body_sections=self.body_sections,
        )
        return capped, deferred

    # -- Domain splitting ------------------------------------------------------

    def split_by_domain(self, domains: list[str]) -> dict[str, "Scorecard"]:
        """Split findings by domain prefix (first char of normalized ID).

        Returns a dict keyed by each domain letter (uppercase).  Findings
        whose prefix doesn't match any domain are silently dropped.
        Empty scorecards are included for every requested domain.
        """
        upper_domains = [d.upper() for d in domains]
        buckets: dict[str, list[Finding]] = {d: [] for d in upper_domains}

        for f in self.findings:
            prefix = normalize_id(f.id)[0].upper()
            if prefix in buckets:
                buckets[prefix].append(f)

        return {
            d: Scorecard(
                cycle=self.cycle,
                track=self.track,
                findings=buckets[d],
                evaluator_failed=self.evaluator_failed,
                evaluator_failure_reason=self.evaluator_failure_reason,
                timestamp=self.timestamp,
                body_sections=self.body_sections,
            )
            for d in upper_domains
        }

    # -- Grades ----------------------------------------------------------------

    def extract_grades(self) -> dict[str, str]:
        """Return ``{normalized_id: grade}`` for every finding."""
        return {normalize_id(f.id): f.grade for f in self.findings}

    # -- YAML output -----------------------------------------------------------

    def to_yaml_frontmatter(self) -> str:
        """Hand-built YAML frontmatter preserving exact bash key order.

        Key order: cycle, track (if present), timestamp (if present), pass,
        partial, fail, blocked, evaluator_failed (if true),
        evaluator_failure_reason(s) (if present), findings.
        """
        lines: list[str] = ["---"]
        lines.append(f"cycle: {self.cycle}")
        if self.track is not None:
            lines.append(f"track: {self.track}")
        if self.timestamp is not None:
            lines.append(f"timestamp: {self.timestamp}")
        lines.append(f"pass: {self.pass_count}")
        lines.append(f"partial: {self.partial_count}")
        lines.append(f"fail: {self.fail_count}")
        lines.append(f"blocked: {self.blocked_count}")
        if self.evaluator_failed:
            lines.append("evaluator_failed: true")
            if self.evaluator_failure_reason:
                escaped = self.evaluator_failure_reason.replace("'", "''")
                lines.append(f"evaluator_failure_reasons: '{escaped}'")
        lines.append("findings:")
        if not self.findings:
            lines.append("  []")
        else:
            for f in self.findings:
                lines.append(f"  - id: {f.id}")
                lines.append(f"    capability: {_yaml_quote(f.capability)}")
                lines.append(f"    grade: {f.grade}")
                lines.append(f"    summary: {_yaml_quote(f.summary)}")
        lines.append("---")
        return "\n".join(lines) + "\n"

    def to_markdown(self, track_order: list[str] | None = None) -> str:
        """Combine frontmatter + per-track body sections into full markdown."""
        parts = [self.to_yaml_frontmatter()]

        if track_order is not None:
            for track in track_order:
                body = self.body_sections.get(track, "")
                if body:
                    parts.append(f"\n### Track {track.upper()}\n")
                    parts.append(body.strip())
                    parts.append("")
        else:
            for _key, body in self.body_sections.items():
                if body and body.strip():
                    parts.append(body)

        return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# Convergence
# ---------------------------------------------------------------------------


def check_convergence(
    current: Scorecard,
    previous: Scorecard,
    flow4_ids: set[str],
    escalated_ids: set[str],
) -> bool:
    """Compare id:grade pairs between cycles, excluding Flow 4 and escalated.

    Returns True if the non-excluded grades are identical and non-empty.
    """
    curr_grades = current.extract_grades()
    prev_grades = previous.extract_grades()

    # Remove excluded IDs
    excluded = flow4_ids | escalated_ids
    for eid in excluded:
        curr_grades.pop(eid, None)
        prev_grades.pop(eid, None)

    # Empty = nothing to compare → not converged
    if not curr_grades:
        return False

    return curr_grades == prev_grades


# ---------------------------------------------------------------------------
# Escalation tracking
# ---------------------------------------------------------------------------


def count_finding_attempts(run_dir: Path, current_cycle: int) -> dict[str, int]:
    """Count how many prior cycles each finding has been attempted in.

    Parses ``fixes-{N}.md`` files for cycles 1..(current_cycle-1) and
    extracts the ``findings_addressed: [...]`` YAML field.

    Cycles rolled back by the verifier write ``.escalation-exempt-{N}.txt``
    sidecars listing finding IDs that should NOT count against the
    escalation counter. A rolled-back attempt never reached code that was
    committed, so letting it burn through ``max_fix_attempts`` would
    escalate findings the fixer was never given a fair chance to fix.

    Returns ``{normalized_id: attempt_count}``.
    """
    # Build exempt set: {(cycle, normalized_id), ...}
    exempt: set[tuple[int, str]] = set()
    if run_dir.exists():
        for sidecar in run_dir.glob(".escalation-exempt-*.txt"):
            m = re.match(r"\.escalation-exempt-(\d+)\.txt", sidecar.name)
            if not m:
                continue
            cycle_n = int(m.group(1))
            for line in sidecar.read_text(encoding="utf-8").splitlines():
                fid = line.strip()
                if fid:
                    exempt.add((cycle_n, normalize_id(fid)))

    counts: dict[str, int] = {}
    for cycle_i in range(1, current_cycle):
        fixes_path = run_dir / f"fixes-{cycle_i}.md"
        if not fixes_path.exists():
            continue
        text = fixes_path.read_text(encoding="utf-8")
        # Parse YAML frontmatter
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            data = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            continue
        addressed = data.get("findings_addressed", [])
        if isinstance(addressed, str):
            # Handle inline format: "A-1, A-2, B-1"
            addressed = [x.strip() for x in addressed.split(",") if x.strip()]
        if not isinstance(addressed, list):
            continue
        for raw_id in addressed:
            nid = normalize_id(str(raw_id))
            if (cycle_i, nid) in exempt:
                continue
            counts[nid] = counts.get(nid, 0) + 1

    return counts


def compute_escalated_findings(
    run_dir: Path, cycle: int, max_attempts: int
) -> set[str]:
    """Compute which findings have been attempted >= max_attempts times.

    A finding that has been fixed *max_attempts* times without passing is
    escalated — excluded from convergence and flagged in fixer prompts.
    """
    attempts = count_finding_attempts(run_dir, cycle)
    return {fid for fid, count in attempts.items() if count >= max_attempts}


def count_escalated_non_pass(
    merged: Scorecard, escalated_ids: set[str]
) -> int:
    """Count findings where the ID is escalated and grade is not PASS."""
    grades = merged.extract_grades()
    return sum(
        1 for fid, grade in grades.items()
        if fid in escalated_ids and grade != "PASS"
    )


# ---------------------------------------------------------------------------
# Flow 4 parsing
# ---------------------------------------------------------------------------


def parse_flow4_capabilities(matrix_path: Path) -> set[str]:
    """Parse ``test-matrix.md`` and extract Flow 4 capability IDs.

    Scans for ``### Flow 4 (Dynamic`` headers, then extracts capability IDs
    from markdown table rows (``| <ID> | ...``) until the next ``###`` or
    ``##`` header.
    """
    if not matrix_path.exists():
        return set()

    ids: set[str] = set()
    in_flow4 = False

    for line in matrix_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### Flow 4 (Dynamic"):
            in_flow4 = True
            continue
        if in_flow4 and (line.startswith("### ") or line.startswith("## ")):
            in_flow4 = False
            continue
        if in_flow4:
            parts = line.split("|")
            if len(parts) >= 3:
                candidate = parts[1].strip()
                if re.match(r"^[A-Z]\d+$", candidate):
                    ids.add(normalize_id(candidate))

    return ids


# ---------------------------------------------------------------------------
# Scope resolution
# ---------------------------------------------------------------------------


def resolve_scope_caps(
    only: list[str],
    phase: str,
    matrix_path: Path,
) -> list[str] | None:
    """Resolve which capability IDs are in scope.

    Returns a list of normalized IDs, or ``None`` if all are in scope.

    - If *only* is non-empty, those IDs (already normalized by Config) are
      returned directly.
    - If *phase* is ``"all"``, returns ``None`` (= everything).
    - Otherwise, looks up the phase in the test-matrix frontmatter.
    """
    if only:
        return [normalize_id(x) for x in only]

    if phase == "all":
        return None

    if not matrix_path.exists():
        return None

    text = matrix_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        data = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return None

    phases = data.get("phases", {})
    raw = phases.get(int(phase) if phase.isdigit() else phase)
    if raw is None:
        return None

    if isinstance(raw, list):
        return [normalize_id(str(x)) for x in raw]

    # String form: "A1,A2,B3"
    return [normalize_id(x.strip()) for x in str(raw).split(",") if x.strip()]


def parse_track_caps(track: str, matrix_path: Path) -> list[str]:
    """Parse capability IDs assigned to a specific track from test-matrix.md."""
    if not matrix_path.exists():
        return []

    text = matrix_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return []

    try:
        data = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return []

    tracks = data.get("tracks", {})
    raw = tracks.get(track)
    if raw is None:
        return []

    if isinstance(raw, list):
        return [normalize_id(str(x)) for x in raw]

    return [normalize_id(x.strip()) for x in str(raw).split(",") if x.strip()]
