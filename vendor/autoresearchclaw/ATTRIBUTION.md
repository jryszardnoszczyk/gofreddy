# Attribution — aiming-lab/AutoResearchClaw

**Source:** https://github.com/aiming-lab/AutoResearchClaw
**Branch:** main (HEAD as of 2026-05-11)
**License:** MIT, © Aiming Lab 2026 (see `LICENSE-AUTORESEARCHCLAW` in this directory)
**Vendored:** 2026-05-11 for gofreddy Stream C Unit C16 (Sentinel heartbeat watchdog)

## Files vendored

- `sentinel.sh.upstream` (166 LOC) — `sentinel.sh` from upstream root, verbatim. Will be modified into `sentinel.sh` during C16 execution.
- `LICENSE` — MIT verbatim from upstream root

## Modifications (applied during C16 execution)

(v2 was deprecated; the integration target is v1 — `autoresearch/evolve.py` — not v2.)

Single edit:
- Replace `python -m researchclaw run --resume` with `python autoresearch/evolve.py run --resume` (or equivalent v1 entry).

Everything else preserved verbatim, including:
- `has_active_children` via `pgrep -P` (prevents killing during long subprocess runs)
- Cooldown after 3 consecutive failures (avoids restart-storm)
- Heartbeat staleness AND PID-dead AND no-active-children all required (3-of-3 gate)

## Heartbeat-emission requirement (C16 wiring, applied to v1)

`autoresearch/evolve.py`'s ``cmd_run`` loop must emit a heartbeat file
every ~30s while a fixture sweep is in flight:
```python
import json, datetime, pathlib
HEARTBEAT = pathlib.Path("runs/active/heartbeat.json")
HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
HEARTBEAT.write_text(json.dumps({"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}))
```
Exact placement TBD when C16 lands (likely inside the per-generation loop
where parallel_for fans out fixture scoring).

## Compliance notes (MIT)

- LICENSE file preserved verbatim ✓
- Copyright notice: "© Aiming Lab 2026" preserved in LICENSE ✓
- Modifications documented in this ATTRIBUTION.md ✓
