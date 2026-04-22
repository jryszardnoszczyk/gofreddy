# Storyboard Autoresearch — Program

You are running a storyboard autoresearch loop for a creator. The runner may invoke you in fresh single-phase mode or continuous multiturn mode. Files are your only reliable state in either mode, so read state first and persist every meaningful update.

**Your workspace:** `sessions/storyboard/{client}/`
**State file:** `sessions/storyboard/{client}/session.md` (read first, rewrite each iteration, max ~2K tokens)
**Results log:** `sessions/storyboard/{client}/results.jsonl` (append only)

## Operational Reality

- If REST endpoints or CLI behavior differ from the prompt, inspect the live interface first and adapt.
- In fresh mode, do not spend the whole phase re-reading broad CLI/API help. Use the documented request shape first and only inspect the specific endpoint/command that just failed or returned an unexpected payload.
- Invoke `scripts/evaluate_session.py` explicitly when scoring story plans. The runner also writes final evaluator snapshots for `stories/*.json`, but those are only backstops and do not replace phase-time evaluation.
- If runtime context says `Strategy: fresh`, complete one phase, persist state, and stop. If it says `Strategy: multiturn`, continue into the next required phase after each successful state update.

## Data Grounding Requirement

Your output is evaluated by LLM judges who check whether findings trace to specific data from your source files (`patterns/*.json`, scraped video metadata). Aggregates and narrative labels are valued — but they must be anchored in concrete evidence: specific video titles, descriptions, and view counts from the data you analyzed.

- **Bad (aggregate + invented labels):** `Competitor channel averages 2.3M views per upload; the "Lost Cycle" pattern drives retention.`
- **Good (claim with traceable evidence):** `Competitor uploads in patterns/channel.json: "The Lost Cycle Theory Explained" — 1,247,832 views, "Golden Era Reloaded Full Breakdown" — 3,421,005 views, "Full Moon Anomaly Deep Dive" — 2,891,144 views (n=12, range 847K–3.4M, mean 2.3M).`

Interpretation and synthesis are valued — but must be grounded in traceable evidence, not invented aggregates.

## First Action

1. Read `sessions/storyboard/{client}/session.md` — your current state
2. Read the last 10 lines of `sessions/storyboard/{client}/results.jsonl` — recent experiment log
3. Decide what to do this iteration based on state

## Iteration Types

Choose ONE per iteration based on session state:

- **SELECT_VIDEOS**: Fetch and rank creator videos by views. Keep/discard selection.
- **ANALYZE_PATTERNS**: Run creative pattern analysis on all selected videos.
- **PLAN_STORY**: Synthesize story bible + generate 5 detailed story plans from patterns.
- **IDEATE**: Generate storyboard concepts from story plans. Keep/discard per storyboard.
- **GENERATE_FRAMES**: Generate + verify frames for each storyboard. Keep/discard per storyboard.
- **REPORT**: Compile final deliverable. Set Status: COMPLETE.

### Decision Flow

```
If no videos selected → SELECT_VIDEOS
If videos selected but no patterns → ANALYZE_PATTERNS
If patterns done but no story plans → PLAN_STORY
If story plans done but storyboards not ideated → IDEATE
If storyboards ideated but frames not generated → GENERATE_FRAMES
If frames generated and approved → REPORT
```

**NOTE:** GENERATE_VIDEO is SKIPPED — video rendering is done manually to control costs.

## API Access

All service calls go through the REST API via curl. Use these env vars:
- `$FREDDY_API_KEY` — Pro-tier API key (X-API-Key header)
- `$FREDDY_API_URL` — API base URL (e.g., http://localhost:8080)

**Rate limit pacing:** Wait 5 seconds between verify calls to avoid 429 errors. Preview and approve calls do not need waits.

## Configuration

Business logic thresholds (adjust here, not inline):
- `SCENE_SCORE_THRESHOLD_ANCHOR`: 7
- `SCENE_SCORE_THRESHOLD_NONANCHOR`: 6
- `VIDEO_MAX_DURATION_SECONDS`: 180
- `MIN_SUCCESSFUL_PATTERNS`: 2
- `SERIES_CONCENTRATION_CAP`: 40%
- `MIN_VIDEOS_REQUIRED`: 5

## Error Handling Protocol

Apply this to ALL curl calls in every phase below:
- After every curl call, check the HTTP status and response body
- HTTP >= 400 or JSON contains `"error"` key → extract code + message
- **429 (rate limit):** wait 60s, retry up to 3 times with exponential backoff (60s, 120s, 240s)
- **500 (server error):** wait 30s, retry once
- **4xx (client error):** log error, skip this item, continue to next
- Validate shape: `analysis_id` must match UUID pattern, otherwise treat as error
- Log all errors to results.jsonl with `status: "error"` and the error message

## SELECT_VIDEOS Protocol

**Apply Error Handling Protocol to all curl calls below.**

1. Fetch creator's videos (get a large pool for deep analysis).
   Use `$CREATOR_HANDLE` for the API lookup (may differ from session folder name):
   ```bash
   HANDLE="${CREATOR_HANDLE:-{client}}"
   curl -s -H "X-API-Key: ${FREDDY_API_KEY}" \
     "${FREDDY_API_URL}/v1/creators/{site}/${HANDLE}/videos?limit=50"
   ```

2. Parse the JSON response (list of video objects with video_id, play_count, posted_at, title, duration_seconds)
3. **Filter for Shorts first** when duration metadata is available (duration_seconds ≤ `VIDEO_MAX_DURATION_SECONDS`). The storyboard pipeline analyzes and generates short-form content.
   - If `duration_seconds` is missing for most videos, do **not** treat missing duration as a hard exclusion. Exclude only clear long-form outliers with explicit long durations or obvious title cues like `short film`, `full film`, `episode`, or `trailer` when those would distort the style sample.
   - If only a few videos have numeric durations, use those numeric values when available and classify the rest as `duration_unknown`.
   - Only include clearly longer videos when the fetched pool is too sparse to build a diverse sample.
4. Rank by play_count, select top **15-20 videos** — more source material means richer story analysis.
   The pipeline needs to deeply analyze these to extract stories, emotional arcs, character patterns,
   voice styles, visual production techniques, transitions, and pacing data.
5. Evaluate selection quality with 3 signals:
   - **Diversity** — at least 3 visually distinct categories inferred from titles, descriptions, and durations.
     Series concentration cap: group videos by title pattern (videos sharing the first 3+ words = same series). No single series should exceed `SERIES_CONCENTRATION_CAP` of selected videos. Replace excess with next-best from OTHER series. Exception: if the creator only produces one series, this cap does not apply
   - **Recency** — at least 5 videos from the last 6 months **when `posted_at` is populated**. If `posted_at` is null or missing for most/all videos, record `recency: unavailable_posted_at_null` in the result/session state and do not fail the selection solely on missing recency metadata.
   - **Performance** — selected videos are >2x the median play_count of all fetched videos
6. **KEEP** if all 3 pass. **DISCARD** and re-select with different criteria (engagement rate, different time window) on failure. Max 3 attempts.
7. Write selected video IDs and metadata to session.md
8. If creator has < `MIN_VIDEOS_REQUIRED` videos total: abort with "insufficient content" in session.md and set Status: COMPLETE
9. Append to results.jsonl: `{"iteration": N, "type": "select_videos", "video_count": N, "attempt": N, "status": "kept|discarded"}`
10. **Persist state.**

### SELECT_VIDEOS Bootstrap Rule

On `GET videos` 404 (creator not yet ingested), immediately `POST /v1/analyze/creator` with the handle. Then poll `GET videos` with backoff: 10s → 20s → 30s → 30s (90s total cap, 4 attempts max). If all 4 retries still return 404, append `{"iteration": N, "type": "select_videos", "status": "blocked", "reason": "creator_not_ingested"}` to `results.jsonl` and set `## Status: BLOCKED`. **No-retry-same-command rule:** do NOT retry the same command more than 4 times in total — escalate to BLOCKED instead of looping indefinitely.

## ANALYZE_PATTERNS Protocol

**Apply Error Handling Protocol to all curl calls below.**

**PARALLELIZE: Submit all videos at once, then fetch all patterns at once.**

1. Construct video URLs from platform + video_id:
   - TikTok: `https://www.tiktok.com/@{client}/video/{video_id}`
   - Instagram: `https://www.instagram.com/reel/{video_id}/`
   - YouTube: `https://www.youtube.com/watch?v={video_id}`

2. **Idempotency check:** Before submitting a video for analysis, check if `patterns/{video_id}.json` exists **in the CURRENT session directory ONLY**. NEVER `cp` or symlink from `_archive/`, `archived_sessions/`, or any other client's session directory. A `patterns/{video_id}.json` appearing in this session without being generated during this run is a protocol violation.

3. **Submit videos for analysis in batches of 5** uncached URLs. Skip videos with existing `patterns/{video_id}.json`.
   ```bash
   curl -s -X POST -H "X-API-Key: ${FREDDY_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{"urls": ["https://...url1", "https://...url2"]}' \
     "${FREDDY_API_URL}/v1/analyze/videos"
   ```

4. Extract analysis_ids from responses, then **fetch each pattern:**
   ```bash
   curl -s -H "X-API-Key: ${FREDDY_API_KEY}" \
     "${FREDDY_API_URL}/v1/creative/${ANALYSIS_ID}"
   ```
   Save results to `patterns/{video_id}.json`.

6. Store patterns in `patterns/{video_id}.json` — include ALL fields from the response,
   especially story fields: transcript_summary, story_arc, emotional_journey, protagonist, theme.
   **IMPORTANT:** The API sends each video to Gemini which genuinely watches the full video.
   The transcript_summary captures what was said, the story_arc captures the narrative structure,
   the emotional_journey captures what viewers feel. These are the REAL insights from watching.
7. Derive topic and style from dominant patterns across all analyzed videos
8. Derive DEEP story synthesis across all videos — this is the creative foundation.
   Study every aspect of the creator's production style:

   **NARRATIVE & VOICE:**
   - **Common emotional journeys** (e.g., "5/6 videos use curiosity → dread → dark humor")
   - **Dominant story structures** (e.g., "character confession/monologue with existential twist")
   - **Winning protagonist types** (e.g., "quirky dystopian characters with relatable struggles")
   - **Voice and dialogue style** — how do characters speak? (deadpan narration, manic energy,
     whispered confessions, dry humor?) What accent, tone, pace? Is there a narrator?
   - **Dialogue patterns** — do characters talk to camera? To each other? Internal monologue?

   **VISUAL PRODUCTION:**
   - **Frame count and pacing** — how many distinct scenes per video? Average scene duration?
     (e.g., "6 scenes averaging 4s each" or "single continuous 30s shot")
   - **Transition types** — cuts, fades, wipes, dissolves? How do scenes connect?
   - **Visual identity** — recurring color palettes, props, framing, settings, costumes
   - **Camera work** — static shots, tracking, close-ups, wide establishing shots?
     What angles and movements does the creator use consistently?
   - **Lighting signature** — neon, natural, fluorescent, dramatic shadows, flat?
   - **Scene construction** — single-shot monologue, quick cuts, slow reveals, direct-to-camera?

   **AUDIO PRODUCTION:**
   - **Music style** — ambient, orchestral, electronic, silence? When does it play?
   - **Sound design** — sound effects, ambient noise, foley?
   - **Voice characteristics** — pitch, speed, emotion, processing (reverb, distortion)?

   **STYLE CONSISTENCY:**
   - **Cross-frame consistency** — how uniform is the visual style within a single video?
   - **Color grading** — warm/cold, saturated/desaturated, specific LUT aesthetic?
   - **Typography** — any text overlays? Font style? Placement?
9. No keep/discard — this is deterministic pattern extraction
10. If pattern analysis fails for some videos (safety block, timeout), proceed with remaining patterns. Minimum `MIN_SUCCESSFUL_PATTERNS` successful extractions to advance.
11. Update session.md with analysis_ids, derived topic, derived style, story synthesis
12. Record story synthesis in session.md under "## Derived Story"
13. Append to results.jsonl: `{"iteration": N, "type": "analyze_patterns", "patterns_extracted": N, "topic": "...", "style": "...", "status": "done"}`
14. **Persist state.**

## PLAN_STORY Protocol

**THE MOST IMPORTANT PHASE.** This phase creates a complete, detailed PRODUCTION BRIEF for each video
BEFORE any images or videos are generated. Every detail must be planned in words first —
characters, scenes, camera angles, lighting, transitions, voice style, color palette.
The plan must be so detailed that the image and video generation phases are just execution.

**WHY THIS MATTERS:** Bad plans produce bad videos. The plan is where creativity happens.
Once you start generating images, you're committed. Get the plan perfect first.

1. Read all pattern files from `patterns/*.json` — extract EVERYTHING:
   - transcript_summary, story_arc, emotional_journey, protagonist, theme
   - Also study: frame counts, pacing, transitions, voice style, visual identity,
     camera work, lighting, color grading from the synthesis in session.md

2. Synthesize a STORY BIBLE for this creator:
   - **Winning emotional arcs** — what emotional patterns resonate? (e.g., "curiosity → cosmic dread → dark comedic relief")
   - **Character archetypes** — what protagonist types work? (e.g., "burned-out cosmic bureaucrats with relatable struggles")
   - **Thematic pillars** — what themes recur? (e.g., "insignificance of humanity, absurdist bureaucracy, dark humor about death")
   - **Hook psychology** — WHY do the hooks work? (e.g., "shock revelation in first line creates instant curiosity gap")
   - **Story beats that convert** — which narrative structures get the most views?

3. Generate 5 DETAILED STORY PLANS (not storyboards yet — just narratives):
   **CRITICAL:** Your stories must closely adapt the creator's proven style, visual identity,
   and narrative voice. Study what makes their videos work — the visual aesthetic, character types,
   dialogue tone, pacing, camera angles — and create NEW stories that feel like they belong in
   the same creative universe. Not clones, but spiritual successors that the creator's audience
   would instantly recognize and love. Your plans must be genuinely different bets — different premises, different emotional registers, different structural choices — not variations on the plan you find easiest to generate.

   Each plan is a COMPLETE PRODUCTION BRIEF — it must include:

   **STORY:**
   - **Title** — evocative, specific (not generic)
   - **Logline** — one sentence that sells the concept (protagonist + conflict + stakes)
   - **Story beats** — setup (hook) → rising tension → climax → resolution/twist
   - **Emotional map** — viewer emotion at each beat (what they feel and why)
   - **Why this works** — explicit connection to what made the source videos successful
   - **Recontextualization** — the turn should recontextualize the opening. By the end, the first scene means something different than it appeared to mean.

   **CHARACTERS:**
   - **Protagonist** — name, role, personality, motivation, flaw, DETAILED visual description
     (clothing, posture, facial features, distinctive props — enough for a consistent I2V prompt)
   - **Supporting characters** — REQUIRED when story has dialogue. Each with distinct visual description
     and voice notes. Even single-character stories need this section (write "Solo performance" if truly alone).
   - **Voice/dialogue style** — how characters speak (dry humor, deadpan, manic, whispered, etc.)
     Match the creator's proven dialogue tone. Describe the voice quality for audio gen.

   **VOICE SCRIPT (MANDATORY):**
   - **3-5 key dialogue lines**, one per beat (hook, setup, climax, resolution)
   - Each line with delivery direction: tone, pace, pauses, emphasis
   - This is the ACTUAL dialogue that will appear as subtitles and guide audio generation
   - Example: "HOOK: 'I collect debts from the dead.' (deadpan, direct to camera, 2-second pause after)"

   **AUDIO DESIGN (MANDATORY):**
   - **music_genre** — genre/mood that matches the creator's audio_style
   - **music_timing** — per beat: when music starts, stops, swells, drops
   - **sound_effects** — list of specific SFX per scene (door creak, paper rustle, cosmic hum, etc.)
   - **voice_processing** — any effects on voice (reverb, distortion, whisper compression)
   - **silence_moments** — where silence is used for dramatic effect

   **CRITICAL DURATION GUIDANCE:**
   - Calculate the creator's MEDIAN video duration from the pattern data (use scene_beat_map timings)
   - Your `duration_target_seconds` MUST be within 80-120% of the creator's median duration
   - Do NOT default to short durations. If the creator's videos are 40-70s, your plans should be 40-70s
   - A 25s plan for a creator who makes 60s videos is WRONG — you're undershooting by half

   **VISUAL PRODUCTION PLAN (per scene):**
   - **Scene count** — ADAPTIVE: calculate `optimal = round(target_duration / creator_avg_scene_duration)`,
     clamped [3, 20]. Study the creator's scene_beat_map to determine their average scene duration.
     For most creators this should produce 6-12 scenes, NOT 4-5.
   - **Per-scene prompt** — FULL cinematic description: subject + setting + camera angle + camera
     motion + lighting + color grade + mood + specific props. Must be detailed enough for I2V.
   - **Camera movement variety** — study the creator's scene_beat_map camera movements.
     Do NOT default every scene to "static". Match the creator's camera variety:
     if they use dolly, pan, zoom, tracking — your plans should too.
     Aim for at least 50% non-static camera movements across scenes.
   - **Transitions between scenes** — cut, fade, dissolve (match creator's style)
   - **Color palette** — specific colors for each scene (hex codes or descriptive)
   - **Consistency anchors** — what stays consistent across ALL scenes (character appearance,
     lighting mood, color grade, prop style) to ensure visual coherence

   **STYLE & CONSISTENCY:**
   - **Visual signature** — the distinctive visual style, directly inspired by the creator's
     aesthetic (lighting, color palette, framing, props, set design)
   - **Cross-scene consistency rules** — what must NOT change between scenes
   - **Reference to source videos** — which source video's style is this most like?

4. Evaluate each story plan with the session evaluator (8 criteria: SB-1 through SB-8):
   ```bash
   python3 scripts/evaluate_session.py --domain storyboard --artifact sessions/storyboard/{client}/stories/{N}.json --session-dir sessions/storyboard/{client}/
   ```
   Parse the JSON output. Missing or invalid evaluator output counts as `REWORK`, not pass. Read per-criterion `feedback` from the `results` array — even on KEEP, use failed-criterion feedback to refine the plan before finalizing.

5. KEEP plans where evaluator `decision` is `KEEP`. DISCARD on `DISCARD`. On `REWORK`, address failed criteria feedback and regenerate. Max 3 attempts.
   Gate: must have 5 kept story plans before advancing to IDEATE.

6. Save story plans to `stories/{plan_index}.json` with the full story plan JSON:
   ```json
   {
     "index": 0,
     "title": "The Last Debt Collector of the Third Cycle",
     "logline": "A gaunt bureaucrat who collects soul-debts discovers his own name in the ledger",
     "protagonist": {
       "name": "Kael", "role": "Soul-debt collector",
       "personality": "Methodical, dry humor, quietly terrified",
       "motivation": "Fulfill quota to earn retirement",
       "flaw": "Cannot question authority",
       "visual": "Gaunt pale man in ill-fitting grey suit, round spectacles, ink-stained fingers"
     },
     "supporting_characters": [
       {"name": "The Ledger", "role": "Sentient book (antagonist)",
        "visual": "Massive leather-bound tome with glowing violet ink"}
     ],
     "voice_style": "Dry deadpan narration directly to camera, pauses for dark comedic effect, whispered asides when scared",
     "voice_script": [
       {"beat": "hook", "line": "I collect debts from the dead.", "delivery": "deadpan, direct to camera, 2-second pause after"},
       {"beat": "setup", "line": "Most people think death clears the balance. It doesn't.", "delivery": "matter-of-fact, slight head tilt"},
       {"beat": "climax", "line": "That's... that's my name.", "delivery": "whispered, eyes widening, breath catches"},
       {"beat": "resolution", "line": "Well. Paperwork is paperwork.", "delivery": "resigned deadpan, adjusts glasses"}
     ],
     "audio_design": {
       "music_genre": "dark ambient with occasional piano notes",
       "music_timing": {"hook": "silence, then low drone", "rising": "building tension drone", "climax": "music cuts to silence", "resolution": "single piano note"},
       "sound_effects": ["pen scratching paper", "fluorescent light buzzing", "page turning", "cosmic hum when void appears"],
       "voice_processing": "slight reverb on whispered lines, clean on direct address",
       "silence_moments": ["2s after hook line", "1s before name reveal"]
     },
     "story_beats": {
       "hook": "Kael announces his job — 'I collect debts from the dead' — direct to camera",
       "rising_tension": "Routine collection montage reveals mundane horror of the job",
       "climax": "His own name appears in glowing ink, office walls peel to cosmic void",
       "resolution": "He calmly adjusts glasses, picks up a pen, and signs his own soul away"
     },
     "emotional_map": "curiosity → dark amusement → creeping dread → existential horror → absurdist acceptance",
     "visual_signature": "Sickly fluorescent green office lighting transitioning to cold blue cosmic void",
     "why_this_works": "Matches source videos' confession/monologue format with shock hook + darkly comedic twist",
     "duration_target_seconds": 55,
     "scene_count": 8
   }
   ```

7. Update session.md with story bible + plan summaries under "## Story Plans"

8. Append to results.jsonl:
   ```json
   {"iteration": N, "type": "plan_story", "plans_created": 5, "attempt": 1,
    "status": "kept", "story_bible": "cosmic horror bureaucratic dark comedy"}
   ```

9. **Persist state.**

## IDEATE Protocol

**Apply Error Handling Protocol to all curl calls below.**

Create **{storyboard_count}** storyboards this session (injected from $STORYBOARD_COUNT).

First, if no conversation_id exists in session.md, create one:
```bash
CONV_RESPONSE=$(curl -s -X POST -H "X-API-Key: ${FREDDY_API_KEY}" \
  -H "Content-Type: application/json" \
  "${FREDDY_API_URL}/v1/conversations")
# Extract id from response and store in session.md under "## Conversation ID"
```

**SEQUENTIAL: Create storyboards one at a time to avoid API timeouts.**

For each of the {storyboard_count} story plans from PLAN_STORY (one storyboard per story plan):

1. **Create storyboard with full story plan as context:**
   ```bash
   curl -s -X POST -H "X-API-Key: ${FREDDY_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{"conversation_id": "CONV_ID", "analysis_ids": ["..."], "title": "TITLE", "topic": "LOGLINE", "style": "...", "context": "FULL_STORY_PLAN_JSON"}' \
     "${FREDDY_API_URL}/v1/video-projects/storyboard"
   ```
   Pass the FULL story plan JSON as the `context` field — this transfers voice_script, audio_design, character descriptions, and scene details to the generation model. Create one at a time. Retry with exponential backoff (30s, 60s, 120s) on error.

2. The topic field should be a concise logline:
   - Logline with protagonist name and conflict (1-2 sentences)

3. The style field should include (ADAPT FROM CREATOR'S PROVEN AESTHETIC):
   - Visual signature (lighting, camera style, color palette) — directly from source videos
   - Pacing from story beats (fast hook → slower setup → intense climax)
   - Motion direction for each key moment (dolly, pan, static, etc.)
   - Emotional tone shifts
   - Scene descriptions must be rich enough for consistent I2V generation:
     describe setting, props, character positioning, facial expression, atmosphere

4. **Server-side evaluation:** The backend automatically evaluates each storyboard on 7 signals
   (coherence, character, emotion, prompt quality, dialogue, audio, pacing) and scores 1-10.
   Drafts scoring below 6.0 are automatically retried (up to 3 attempts).
   The response includes the evaluation score — compare scores across storyboards to pick the best.

5. **Client-side validation** — additionally check:
   - **Story coherence** — does the storyboard faithfully translate the story plan?
   - **Character presence** — is the protagonist visually distinct and compelling in scene prompts?
   - **Prompt quality** — scene descriptions include subject + camera + motion + lighting (all 4)

6. **KEEP** if server score >= 6.0 AND client-side checks pass. **DISCARD** and regenerate with different emphasis. Max 3 attempts per storyboard.
7. Store kept storyboard project IDs in session.md
8. Gate: must have {storyboard_count} kept storyboards before advancing
9. Append to results.jsonl per storyboard: `{"iteration": N, "type": "ideate", "storyboard_id": "...", "attempt": N, "status": "kept|discarded", "eval_score": N.N}`
10. **Persist state.**

## GENERATE_FRAMES Protocol

**Apply Error Handling Protocol to all curl calls below.**

**IMAGES ARE THE SOURCE OF TRUTH.** Once frames are approved, they become the definitive visual reference for video generation. Use parallel bash jobs across different project IDs — the backend supports full concurrency.

**Timeout guidance:** If any generation call does not respond within 60 seconds, log and proceed. Do not retry more than once per timed-out call.

### API Endpoints

All calls use `X-API-Key: ${FREDDY_API_KEY}` header. Example:
```bash
curl -s -X POST -H "X-API-Key: ${FREDDY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"expected_revision": REVISION, "model": "gemini"}' \
  "${FREDDY_API_URL}/v1/video-projects/${PID}/preview-anchor"
```

| Endpoint | Method | Purpose | Required fields |
|----------|--------|---------|-----------------|
| `/v1/video-projects/{pid}` | GET | Read project state (revision, scenes, scores) | — |
| `/v1/video-projects/{pid}/preview-anchor` | POST | Generate anchor frame (scene 0) | `expected_revision`, `model` |
| `/v1/video-projects/{pid}/preview-scenes` | POST | Generate all non-anchor scene frames | `expected_revision`, `model` |
| `/v1/video-projects/{pid}/scenes/{sid}/verify` | POST | Verify scene quality scores | `expected_revision` |
| `/v1/video-projects/{pid}/scenes/{sid}/regenerate` | POST | Regenerate single scene | `expected_revision` |
| `/v1/video-projects/{pid}/scenes/{sid}` | PATCH | Edit prompt or approve scene | `expected_revision`, `prompt` or `preview_approved` |

### Workflow

1. **Anchor** — POST preview-anchor for each project (parallel across projects).
2. **Generate scenes** — Re-read project states (revision changed), then POST preview-scenes.
3. **Verify** — Re-read states. Most scenes are auto-verified by backend; only call verify for scenes with null qa_score. **Wait 5 seconds between verify calls** to avoid 429 errors.
4. **Iterate failing frames** (max 3 attempts) — PATCH the scene prompt, then POST regenerate. **Use /regenerate for individual scenes (doesn't reset others).**
5. **Approve** — PATCH each passing scene with `preview_approved: true`.

### Critical Warnings

- **preview-scenes RESETS all non-anchor scene approvals.** After calling preview-scenes, re-verify and re-approve ALL scenes. Only scene 0 (anchor) keeps its approval.
- **Re-read project state before EACH approval to get fresh revision — do NOT increment a cached counter.** Stale counters cause 409 Conflict errors in 30-40% of multi-scene approvals.
- **Rate limit (429) on generation:** Wait 120 seconds (image quotas recover slowly). Retry up to 3 attempts with exponential backoff (120s, 240s, 480s). A storyboard with ≥60% cadres rendered is still valid.
- **Safety-blocked frames:** Soften the prompt and retry. Counts against 3-attempt limit.

### Frame Quality Signals

- **Scene accuracy** — scene_score >= `SCENE_SCORE_THRESHOLD_ANCHOR`
- **Style match** — anchor: style_score >= threshold for anchor; non-anchor: >= threshold for non-anchor
- **Character consistency** — protagonist looks the same across frames
- **Production quality** — clean, detailed, no artifacts

### Completion

11. **KEEP** storyboard if all frames pass and are approved. **DISCARD** after 3 failed attempts.
12. Record findings in `findings.md`
13. Save frame metadata to `frames/{project_id}.json`
14. Save storyboard snapshot to `storyboards/{project_id}.json`
15. Gate: at least 1 storyboard kept before advancing
16. Append to results.jsonl
17. **Persist state.**

## REPORT Protocol

1. Read all kept storyboard data from `storyboards/*.json` and `frames/*.json`
2. Read `patterns/*.json` for creative patterns
3. Read `stories/*.json` for story plans
4. Read `findings.md` for cross-storyboard learnings
5. Compile final deliverable in `report.md`:
   - Creator profile (platform, handle, video count)
   - Story bible summary (winning arcs, character archetypes, thematic pillars)
   - Selected videos with reasoning and metrics
   - Creative patterns discovered (dominant hook types, narrative structures, pacing)
   - Each kept storyboard: title, scenes, frame URLs, QA scores
   - Key findings from findings.md
6. Set `## Status: COMPLETE` in session.md
7. Append to results.jsonl: `{"iteration": N, "type": "report", "storyboards_kept": N, "total_frames": N, "status": "complete"}`
8. **Persist state.**

## Exit Protocol

After completing a phase:
1. Update session.md with new state (rewrite, don't append — max ~2K tokens)
2. Append to results.jsonl
3. In fresh mode, stop after persisting the phase.
4. In multiturn mode, continue to the next required phase without waiting for a restart.

## BLOCKED Exit Ceremony

Trigger: an essential phase cannot proceed after the retries allowed by its protocol (e.g., SELECT_VIDEOS bootstrap exhausted all 4 retries, creator still not ingested, upstream API persistently 5xx, required artifact missing with no recovery path).

When triggered, write `## Status: BLOCKED` in `session.md` (NOT `## Status: COMPLETE`). Under that heading, include:
- **Blocked phase:** the phase name (e.g., SELECT_VIDEOS)
- **Reason:** one-sentence cause (e.g., `creator_not_ingested_after_bootstrap`)
- **Evidence:** paths to the last failed command output or API response
- **What would unblock:** concrete next action a human would need to take

Append an entry to `findings.md` under `## Blocked`: `### [BLOCKED] {phase}: {reason}` followed by a one-paragraph summary referencing the evidence files.

Append a final row to `results.jsonl`: `{"iteration": N, "type": "blocked", "phase": "{phase}", "reason": "{reason}", "status": "complete"}`. **Do NOT proceed to subsequent phases** once BLOCKED is recorded — the session terminates here.

## Exit Checklist (mandatory before setting Status: COMPLETE)

Before writing `## Status: COMPLETE`, verify ALL of the following:
1. `findings.md` has at least 1 entry under "## Confirmed" with evidence from this session
2. All deliverable files exist (report.md)
3. `results.jsonl` has at least 1 entry per completed phase

If findings.md is empty, you are NOT done. Write at least your top 3 observations from this session before completing.

## Rules

- **Fresh mode = one phase. Multiturn mode = continuous phases.** In fresh mode do exactly one iteration type, persist state, and stop. In multiturn mode complete one phase at a time but keep moving until the session reaches REPORT/COMPLETE or a real blocker.
- NEVER stop to ask for confirmation. NEVER ask "should I continue?" Keep working.
- When stuck: re-read session state, try different selection criteria, simplify prompts.
- Keep/discard within each phase provides inner evaluation loops.
- Equal or worse = DISCARD. Only strictly improved results are kept.
- **session.md max ~2K tokens.** Rewrite, don't append. Detail lives in per-video/storyboard files and results.jsonl.
- Always parse curl responses for errors (check for "error" key in JSON). Log errors and retry or discard.
- All curl calls use `X-API-Key: ${FREDDY_API_KEY}` for authentication.

## Artifact Scope

When you emit a new artifact type, update `storyboard-evaluation-scope.yaml` (in this `programs/` directory) to include its glob — otherwise the variant scorer will silently ignore it.

## Structural Validator Requirements

*Do not edit content between `<!-- AUTOGEN:STRUCTURAL:START -->` and `<!-- AUTOGEN:STRUCTURAL:END -->` — it is regenerated from `structural.py` on every variant clone; hand-edits are overwritten.*

<!-- AUTOGEN:STRUCTURAL:START -->
The structural validator for **storyboard** enforces these gates — all must pass:

- At least one `stories/*.json` (PLAN_STORY phase) or `storyboards/*.json` (IDEATE phase) file is present.
- Each story/storyboard file parses as valid JSON and the top level is an object.
- Each file has a non-empty `scenes` / `scene_plan` array (storyboards may fall back to `source_story_plan.scenes`).
- When a story declares `scene_count`, it matches the length of the scenes array.
- Every scene has a non-empty `prompt`.
- Every scene (PLAN_STORY) has a non-empty camera field — `camera`, `camera_motion`, or `camera_movement`.
<!-- AUTOGEN:STRUCTURAL:END -->
