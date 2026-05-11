# Lane: storyboard — AI video storyboard generation

**What this lane does:** evolves the prose at `lanes/storyboard.md` so each session produces `stories/<id>.json` (PLAN_STORY phase) or `storyboards/<id>.json` (IDEATE phase) — structured scene plans for AI-generated video content.

**Baseline you're trying to beat:**
- v006 search-v1 composite is contaminated by a window of broken-backend runs (3 of 4 fixtures had `struct=fail`) — DO NOT promote off the v006 search-v1 score. Storyboard baselines must be re-established post-backend-stabilization. The `app.state.video_storage` alias fix shipped 2026-05-08 (`76a7d18`) closed the 500-on-`/v1/creative` issue; storyboard sessions now reach iter > 2 with `deliverables > 0`.

---

## Deliverable contract

The session writes `stories/*.json` AND/OR `storyboards/*.json` under `sessions/storyboard/<client>/`. Each session MUST satisfy ALL of:

1. At least one `stories/*.json` (PLAN_STORY phase) OR `storyboards/*.json` (IDEATE phase) file is present.
2. Each story/storyboard file parses as valid JSON and the top level is a JSON object.
3. Each file has a non-empty `scenes` / `scene_plan` array (storyboards may fall back to `source_story_plan.scenes`).
4. When a story declares `scene_count`, it matches the length of the scenes array.
5. Every scene has a non-empty `prompt`.
6. Every scene (PLAN_STORY) has a non-empty camera field — `camera`, `camera_motion`, OR `camera_movement`.

Any failure → `checks_failed`.

---

## The 8 SB judges (your fitness function)

Composite = geometric mean across SB-1 .. SB-8. Cinematic-quality rubrics emphasising:
- Per-scene camera vocabulary (motion verbs, framing, lens hints).
- Scene-to-scene continuity (subject, lighting, motion direction).
- Prompt quality (specific subjects, named styles, no AI-tell prose).
- Story arc (setup / development / resolution structure detectable across scenes).

---

## Render judges (NOT all five)

Storyboard skips **RND-3** (PDF print-readiness — cinematic dark-mode theme is meant for screen, not paper). Render rubric set: `(RND-1, RND-2, RND-4, RND-5)`.

---

## What you CANNOT edit

- `autoresearch/archive/v006/workflows/storyboard.py`
- `autoresearch/archive/v006/workflows/session_eval_storyboard.py`

Plus the universal rules.

---

## Mutation surfaces that worked

- Adding "every scene MUST have one camera-motion verb from {pan, dolly, truck, tilt, push, pull, orbit, crane}" — improves SB-2 dramatically.
- Forcing scene_count to match the actual scenes array length (matches structural gate).
- The `image_preview_service` wire (FakeImagePreviewService + LocalDevPreviewStorage) was a substrate fix, not a prose mutation — preserved via U2 invocation of v006/run.py.

## Mutation surfaces that have regressed

- Demanding 12+ scenes per story — fixture timeouts at high scene counts.
- Stripping the `[CAMERA]` annotation — structural gate fails on `scene_has_camera`.

---

## Fixture coverage

- Search-v1: `storyboard-*` fixture_ids in `eval_suites/search-v1.json` (4 baseline fixtures: TechReview + 3 others).
- Holdout-v1: per-lane fixtures in `~/.config/gofreddy/holdouts/holdout-v1.json`.

**Reminder:** the preview-anchor 422→200 transition (commit `a009055`) was a substrate fix in `src/api/main.py`, not a v2 lane mutation. v2 wraps v006/run.py which already has the fix.

---

## Recent history pointers

- `git log --oneline lanes/storyboard.md`
- Last ~10 rows of `lanes/storyboard/results.tsv`
- `alerts.jsonl` filtered by `lane=storyboard`
