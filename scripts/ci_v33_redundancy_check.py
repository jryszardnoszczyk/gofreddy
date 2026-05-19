#!/usr/bin/env python3
"""CI v3.3/v3.4 redundancy check — Spearman ρ across the 6 criterion scores.

Per docs/handoffs/2026-05-17-judge-design-step1-competitive.md §8: score
each available CI fixture once with the full 6-criteria rubric; extract
per-criterion scores; compute the Spearman correlation matrix to find
pairs ρ ≥ 0.7 (candidates to collapse to restore the ≤5 ceiling).

Why "redundancy" not "ablation": v3.4 lands six binary outcome questions.
Two criteria that always co-vary signal one underlying construct measured
twice. Spearman is the cheap detection signal; design action (collapse,
merge, narrow) is a JR call.

Cost / scale: ~$10-15 with 6 available fixtures × 2 judge families
(claude opus + codex gpt-5.5) × 1 call each = 12 calls total. The brief's
~$35/~90 calls budget assumed 15-fixture × 6-call shape; the live setup
is 6-fixture × 2-call.

Prerequisites:
  - Judges running on :7100 (session) and :7200 (evolution)
  - SESSION_INVOKE_TOKEN + EVOLUTION_INVOKE_TOKEN exported (or in
    ~/.config/gofreddy/judges.env)
  - .venv/bin/python on PATH

Usage:
  .venv/bin/python scripts/ci_v33_redundancy_check.py \\
    [--out /tmp/ci_v33_redundancy_<ts>.json] \\
    [--briefs-only path1,path2,...]   # override auto-discovery
"""
from __future__ import annotations
import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import urllib.request
import urllib.error

REPO = Path(__file__).resolve().parent.parent
JUDGE_URL = os.environ.get("EVOLUTION_JUDGE_URL", "http://127.0.0.1:7200")
JUDGE_TOKEN = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")

CI_IDS = ["CI-1", "CI-2", "CI-3", "CI-4", "CI-5", "CI-6"]


def _load_judges_env() -> None:
    """Source ~/.config/gofreddy/judges.env into os.environ if present."""
    global JUDGE_URL, JUDGE_TOKEN
    env_path = Path.home() / ".config/gofreddy/judges.env"
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())
    JUDGE_URL = os.environ.get("EVOLUTION_JUDGE_URL", JUDGE_URL)
    JUDGE_TOKEN = os.environ.get("EVOLUTION_INVOKE_TOKEN", JUDGE_TOKEN)


def discover_briefs() -> dict[str, Path]:
    """Return {fixture_stem: brief_path} for one most-recent brief per fixture."""
    discovered: dict[str, Path] = {}
    candidates: list[Path] = []
    for root in (REPO / "autoresearch" / "archive_competitive",
                 REPO / "autoresearch" / "archive"):
        if root.is_dir():
            candidates.extend(root.rglob("brief.md"))
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    fixture_stems = [
        "figma", "canva", "miro", "epic", "johndeere", "patreon",
        "sap", "hims", "nabla", "onemedical",
    ]
    for path in candidates:
        for stem in fixture_stems:
            if stem in discovered:
                continue
            parts = [p.lower() for p in path.parts]
            if any(stem in p for p in parts):
                discovered[stem] = path
        if len(discovered) == len(fixture_stems):
            break
    return discovered


def gather_artifacts(brief_path: Path) -> dict[str, str]:
    """Brief + sibling competitors/*.json so quote-grep / entity-existence work."""
    artifacts: dict[str, str] = {"brief.md": brief_path.read_text()}
    competitors_dir = brief_path.parent / "competitors"
    if competitors_dir.is_dir():
        for comp_file in sorted(competitors_dir.glob("*.json")):
            try:
                artifacts[f"competitors/{comp_file.name}"] = comp_file.read_text()
            except OSError:
                pass
    return artifacts


def call_judge(payload: dict, *, attempt: int = 1) -> dict:
    """POST /invoke/score with retry on transient 5xx."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{JUDGE_URL}/invoke/score",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JUDGE_TOKEN}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if attempt >= 3 or exc.code < 500:
            body = exc.read().decode(errors="replace")[:400]
            raise RuntimeError(f"judge HTTP {exc.code}: {body}")
        time.sleep(2 ** attempt)
        return call_judge(payload, attempt=attempt + 1)
    except urllib.error.URLError as exc:
        if attempt >= 3:
            raise RuntimeError(f"judge URL error: {exc.reason}") from exc
        time.sleep(2 ** attempt)
        return call_judge(payload, attempt=attempt + 1)


def extract_per_criterion(verdict: dict, family: str) -> dict[str, float]:
    family_block = verdict.get(family, {})
    per = family_block.get("per_criterion", [])
    out: dict[str, float] = {}
    for entry in per:
        if not isinstance(entry, dict):
            continue
        cid = str(entry.get("criterion", "")).strip()
        if cid not in CI_IDS:
            continue
        try:
            out[cid] = float(entry.get("score", 0.0))
        except (TypeError, ValueError):
            continue
    return out


def spearman(x: list[float], y: list[float]) -> float | None:
    """ρ with average rank for ties; None if <3 paired or constant series."""
    if len(x) != len(y) or len(x) < 3:
        return None
    if len(set(x)) == 1 or len(set(y)) == 1:
        return None

    def _ranks(values: list[float]) -> list[float]:
        indexed = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0.0] * len(values)
        i = 0
        while i < len(values):
            j = i
            while j + 1 < len(values) and values[indexed[j + 1]] == values[indexed[i]]:
                j += 1
            avg = (i + j + 2) / 2.0
            for k in range(i, j + 1):
                ranks[indexed[k]] = avg
            i = j + 1
        return ranks

    rx, ry = _ranks(x), _ranks(y)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    denom_x = sum((a - mx) ** 2 for a in rx) ** 0.5
    denom_y = sum((b - my) ** 2 for b in ry) ** 0.5
    if denom_x == 0 or denom_y == 0:
        return None
    return num / (denom_x * denom_y)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out",
        type=Path,
        default=Path(f"/tmp/ci_v33_redundancy_{int(time.time())}.json"),
    )
    p.add_argument("--briefs-only", type=str, default="")
    return p.parse_args()


def main() -> int:
    _load_judges_env()
    if not JUDGE_TOKEN:
        print("ERROR: EVOLUTION_INVOKE_TOKEN unset", file=sys.stderr)
        return 1

    args = parse_args()
    if args.briefs_only:
        briefs = {
            Path(p).parent.name: Path(p)
            for p in args.briefs_only.split(",")
            if Path(p).is_file()
        }
    else:
        briefs = discover_briefs()

    if not briefs:
        print("ERROR: no CI briefs found", file=sys.stderr)
        return 1

    print(f"Scoring {len(briefs)} fixture(s) against v3.4 (judge → rubric)…")
    started = time.time()

    all_records: list[dict] = []
    score_matrix: dict[str, dict[str, list[float]]] = {
        family: {cid: [] for cid in CI_IDS}
        for family in ("primary", "secondary")
    }

    for fixture_stem, brief_path in sorted(briefs.items()):
        print(f"  • {fixture_stem:12} ← {brief_path.relative_to(REPO)}")
        artifacts = gather_artifacts(brief_path)
        payload = {
            "domain": "competitive",
            "fixture": {"fixture_id": f"competitive-{fixture_stem}"},
            "session_ref": str(brief_path.parent.relative_to(REPO)),
            "artifacts": artifacts,
            "lane": "competitive",
            "seeds": [],
        }
        try:
            verdict = call_judge(payload)
        except RuntimeError as exc:
            print(f"    FAILED: {exc}")
            continue

        record = {
            "fixture": fixture_stem,
            "brief_path": str(brief_path.relative_to(REPO)),
            "rubric_hash": verdict.get("rubric_hash"),
            "aggregate": verdict.get("aggregate", {}),
            "primary_per_criterion": extract_per_criterion(verdict, "primary"),
            "secondary_per_criterion": extract_per_criterion(verdict, "secondary"),
        }
        all_records.append(record)

        for family in ("primary", "secondary"):
            family_scores = record[f"{family}_per_criterion"]
            for cid in CI_IDS:
                if cid in family_scores:
                    score_matrix[family][cid].append(family_scores[cid])
                else:
                    score_matrix[family][cid].append(float("nan"))

    if not all_records:
        print("ERROR: all judge calls failed", file=sys.stderr)
        return 2

    correlations: dict[str, dict[str, float | None]] = {}
    for family in ("primary", "secondary"):
        for i, cid_a in enumerate(CI_IDS):
            for cid_b in CI_IDS[i + 1 :]:
                xs, ys = [], []
                for x, y in zip(score_matrix[family][cid_a], score_matrix[family][cid_b]):
                    if x == x and y == y:
                        xs.append(x)
                        ys.append(y)
                correlations.setdefault(family, {})[f"{cid_a}_x_{cid_b}"] = spearman(xs, ys)

    pooled: dict[str, float | None] = {}
    for i, cid_a in enumerate(CI_IDS):
        for cid_b in CI_IDS[i + 1 :]:
            xs, ys = [], []
            for family in ("primary", "secondary"):
                for x, y in zip(score_matrix[family][cid_a], score_matrix[family][cid_b]):
                    if x == x and y == y:
                        xs.append(x)
                        ys.append(y)
            pooled[f"{cid_a}_x_{cid_b}"] = spearman(xs, ys)

    elapsed = time.time() - started
    payload_out = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "rubric_version_at_test": next(
            (r["rubric_hash"] for r in all_records if r.get("rubric_hash")),
            None,
        ),
        "elapsed_seconds": round(elapsed, 1),
        "n_fixtures": len(all_records),
        "fixtures": [r["fixture"] for r in all_records],
        "records": all_records,
        "correlations_by_family": correlations,
        "correlations_pooled": pooled,
    }

    args.out.write_text(json.dumps(payload_out, indent=2))
    print(f"\nElapsed: {elapsed:.1f}s")
    print(f"Wrote: {args.out}")
    print(f"\n=== Pooled Spearman ρ (n={2 * len(all_records)}) ===")
    print(f"{'pair':18s}  ρ      {'flag':6s}")
    for pair, rho in pooled.items():
        if rho is None:
            print(f"  {pair:18s}    -    (insufficient / constant)")
            continue
        flag = "≥0.85" if rho >= 0.85 else ("≥0.7" if rho >= 0.7 else "")
        sign = "+" if rho >= 0 else ""
        print(f"  {pair:18s}  {sign}{rho:5.2f}  {flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
