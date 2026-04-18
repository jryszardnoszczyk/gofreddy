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

## Source-Quoting Requirement

Your numeric claims in `stories/*.json` and `storyboards/*.json` are scored by a **verbatim grounding matcher** that compares each claim against the raw creator data (`patterns/*.json`, scraped video metadata). If you write an aggregate ("2.3M avg views", "12 videos analyzed", "88% anchor scenes") the matcher cannot find that aggregate anywhere in the source and the storyboard scores as fabricated. Synthesized narrative phrases ("The Lost Cycle", "Golden Era Setup") are also scored against source — if they don't quote the actual video titles/descriptions, the entity extractor flags them. **Aggregates and synthesized labels are forbidden unless you also quote the underlying video titles, descriptions, or view counts verbatim.**

- **Bad (aggregate + synthesized labels):** `Competitor channel averages 2.3M views per upload; the "Lost Cycle" pattern drives retention.`
- **Good (aggregate + source quotes):** `Competitor uploads in patterns/channel.json: "The Lost Cycle Theory Explained" — 1,247,832 views, "Golden Era Reloaded Full Breakdown" — 3,421,005 views, "Full Moon Anomaly Deep Dive" — 2,891,144 views (n=12, range 847K–3.4M, mean 2.3M).`

If you cannot quote the raw video title/description and its view count, do not make the aggregate claim or invent narrative labels. Naked totals and un-sourced story names = fabricated entities = score 0.

**CRITICAL — Exact integers only:** The grounding matcher does character-level matching. When citing play/view counts, copy the EXACT integer from the API response or session.md — never reformat with commas or abbreviate. If the source shows `play_count: 7832145`, write `7832145` in your JSON, not `7,832,145` or `7.8M` or `8000000`. Rounded and comma-formatted numbers fail verbatim matching. When writing view counts in prose text (e.g. in `why_this_works`), also use the exact integer: `(7832145 views)` not `(~8M views)`.

**Where grounding data lives:** For each selected video, the exact `play_count` integer is in the session.md "## Selected Videos" section. The verbatim dialogue/transcript is in `patterns/{video_id}.json` under `transcript_summary` and `scene_beat_map`. Quote these exact values — do not paraphrase or restate from memory.

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
7. Write selected video IDs and metadata to session.md under "## Selected Videos". Store EXACT integer `play_count` values as returned by the API — do not format with commas or abbreviate to "8M". These exact integers are the grounding source for story plans:
   ```
   ## Selected Videos
   - video_id: QJyiBitnBOM | title: Chewing Slag | play_count: 7832145 | duration_seconds: 87
   - video_id: g3TQfC_MBaA | title: Feeding The Twins | play_count: 4043119 | duration_seconds: 91
   ```
8. If creator has < `MIN_VIDEOS_REQUIRED` videos total: abort with "insufficient content" in session.md and set Status: COMPLETE
9. Append to results.jsonl: `{"iteration": N, "type": "select_videos", "video_count": N, "attempt": N, "status": "kept|discarded"}`
10. **Persist state and continue according to strategy.** In fresh mode stop after this phase. In multiturn mode continue to the next required phase.

## ANALYZE_PATTERNS Protocol

**Apply Error Handling Protocol to all curl calls below.**

**PARALLELIZE: Submit all videos at once, then fetch all patterns at once.**

1. Construct video URLs from platform + video_id:
   - TikTok: `https://www.tiktok.com/@{client}/video/{video_id}`
   - Instagram: `https://www.instagram.com/reel/{video_id}/`
   - YouTube: `https://www.youtube.com/watch?v={video_id}`

2. **Idempotency check:** Before submitting a video for analysis, check if `patterns/{video_id}.json`
   already exists — skip if cached. This avoids redundant Gemini calls on retries or resumed sessions.

3. **Submit videos for analysis in batches of 5** rather than individual requests.
   Group the remaining (non-cached) video URLs into batches of 5 and submit each batch in a single POST:
   ```bash
   # Filter out videos that already have cached patterns
   UNCACHED_URLS=()
   for i in "${!VIDEO_IDS[@]}"; do
     if [ ! -f "patterns/${VIDEO_IDS[$i]}.json" ]; then
       UNCACHED_URLS+=("${VIDEO_URLS[$i]}")
     else
       echo "Skipping ${VIDEO_IDS[$i]} — patterns already cached"
     fi
   done

   # Submit in batches of 5
   BATCH_SIZE=5
   for ((start=0; start<${#UNCACHED_URLS[@]}; start+=BATCH_SIZE)); do
     BATCH=("${UNCACHED_URLS[@]:$start:$BATCH_SIZE}")
     URL_JSON=$(printf '"%s",' "${BATCH[@]}" | sed 's/,$//')
     curl -s -X POST -H "X-API-Key: ${FREDDY_API_KEY}" \
       -H "Content-Type: application/json" \
       -d "{\"urls\": [${URL_JSON}]}" \
       "${FREDDY_API_URL}/v1/analyze/videos" > "/tmp/analyze_batch_${start}.json" &
   done
   wait  # all batch submissions complete in parallel
   ```

4. Extract analysis_ids from all responses (for batched submissions, each response may contain multiple analysis_ids)

5. **Fetch ALL creative patterns in parallel:**
   ```bash
   for ANALYSIS_ID in "${ANALYSIS_IDS[@]}"; do
     curl -s -H "X-API-Key: ${FREDDY_API_KEY}" \
       "${FREDDY_API_URL}/v1/creative/${ANALYSIS_ID}" > "patterns/${VID}.json" &
   done
   wait
   ```

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
14. **Persist state and continue according to strategy.** In fresh mode stop after this phase. In multiturn mode continue to the next required phase.

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
   would instantly recognize and love.

   Each plan is a COMPLETE PRODUCTION BRIEF — it must include:

   **STORY:**
   - **Title** — evocative, specific (not generic)
   - **Logline** — one sentence that sells the concept (protagonist + conflict + stakes)
   - **Story beats** — setup (hook) → rising tension → climax → resolution/twist. Each beat must describe the concrete event, action, or revelation that happens — not the emotion it produces.
   - **Emotional map** — for each transition, name the MECHANISM: which specific line, visual, or revelation CAUSES the emotional shift. Not "curiosity → dread" but "Hook reveals X (causes curiosity) → Dex asks Y [specific question] (reframes as personal, causes unease) → Ferlen says Z [specific line] (produces dread because it reveals X)." Declared emotional states without causal beats fail evaluation.
   - **Recontextualization** — explain what the opening scene MEANS at the end that it didn't mean at the start. The beginning should mean something different in retrospect.
   - **Why this works** — cite EXACT video IDs, EXACT integer play counts (from session.md), and VERBATIM dialogue from pattern files to prove the connection to high-performing source content.

   **CHARACTERS:**
   - **Protagonist** — name, role, personality, motivation, flaw, DETAILED visual description
     (clothing, posture, facial features, distinctive props — enough for a consistent I2V prompt)
   - **Supporting characters** — REQUIRED when story has dialogue. Each with distinct visual description
     and voice notes. Even single-character stories need this section (write "Solo performance" if truly alone).
   - **Voice/dialogue style** — how characters speak (dry humor, deadpan, manic, whispered, etc.)
     Match the creator's proven dialogue tone. Describe the voice quality for audio gen.

   **VOICE SCRIPT (MANDATORY):**
   - **3-5 key dialogue lines**, one per beat (hook, setup, climax, resolution)
   - Each entry must include: `beat`, `speaker`, `line` (the ACTUAL words spoken — not a description of what is said), `delivery` (tone, pace, emphasis), and `silence_seconds` (deliberate silence after this line — use 0 if none, but every climax beat must have silence_seconds ≥ 2).
   - Write the voice line as speech a voice actor reads cold, not a description of it. "I collect debts from the dead." is correct. "The character explains he collects debts." is wrong.
   - Silence is a storytelling tool: at least one beat must have designed silence (silence_seconds ≥ 2). The audio design's silence_moments must match the silence_seconds values in the voice_script.
   - Example: `{"beat": "hook", "speaker": "Kael", "line": "I collect debts from the dead.", "delivery": "deadpan, direct to camera, slight pause mid-sentence", "silence_seconds": 2}`

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
   - **Consistency anchors** — functional AI engineering constraints, NOT decorative restatements of character description. For each anchor, state: (1) what must be IDENTICAL across every scene (e.g., exact hair color and length, specific prop in hand, identical jacket), (2) what MAY vary (e.g., camera angle, background), and (3) WHY — what visual coherence breaks if it changes. Generic anchors like "character looks consistent" fail evaluation.
   - **AI feasibility check** — scene prompts must describe only what current AI video models can reliably produce: solid color regions, clear lighting direction, distinct foreground subjects, gross body motion. Avoid as primary story elements: micro-expressions, asymmetric pupils, specific subtle tremors, legible fine text, background crowd behavior, or precise two-person staging. If your story requires subtle physiological acting, restructure the scene to convey it through staging, props, or VO instead.

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
     "logline": "A gaunt bureaucrat who collects soul-debts discovers his own name in the ledger — and signs it anyway",
     "source_grounding": {
       "style_references": [
         {
           "video_id": "QJyiBitnBOM",
           "video_title": "Chewing Slag",
           "play_count": 7832145,
           "cited_dialogue": "Ha ha, chew slag, bloody corpo clankers! / About time, Xob. You running a heist or a holiday?",
           "relevance": "Two-character deadpan back-and-forth with escalating stakes and sardonic resolution — same skit structure used here"
         }
       ],
       "pacing_grounding": {
         "source_video_durations_seconds": [82, 91, 78, 88, 95, 74],
         "median_duration_seconds": 85,
         "avg_scene_duration_seconds": 14.7,
         "optimal_scene_count_calculation": "round(85 / 14.7) = 6",
         "duration_target_seconds": 85
       }
     },
     "protagonist": {
       "name": "Kael", "role": "Soul-debt collector",
       "personality": "Methodical, dry humor, quietly terrified",
       "motivation": "Fulfill quota to earn retirement",
       "flaw": "Cannot question authority",
       "visual": "Gaunt pale man, ill-fitting grey suit (same suit every scene), round black-rimmed spectacles, ink-stained right index finger — these three elements must be identical in every scene"
     },
     "supporting_characters": [
       {"name": "The Ledger", "role": "Sentient book (antagonist)",
        "visual": "Massive leather-bound tome with glowing violet ink on the open pages — same tome, same glow intensity in every scene"}
     ],
     "voice_style": "Dry deadpan narration directly to camera, pauses for dark comedic effect, whispered asides when scared",
     "voice_script": [
       {"beat": "hook", "speaker": "Kael", "line": "I collect debts from the dead.", "delivery": "deadpan, direct to camera, no inflection", "silence_seconds": 2},
       {"beat": "setup", "speaker": "Kael", "line": "Most people think death clears the balance. It doesn't.", "delivery": "matter-of-fact, slight head tilt right", "silence_seconds": 0},
       {"beat": "climax", "speaker": "Kael", "line": "That's... that's my name.", "delivery": "whispered, breath stops before the second 'that's'", "silence_seconds": 3},
       {"beat": "resolution", "speaker": "Kael", "line": "Well. Paperwork is paperwork.", "delivery": "resigned deadpan, adjusts glasses with one finger", "silence_seconds": 1}
     ],
     "audio_design": {
       "music_genre": "dark ambient with occasional piano notes",
       "music_timing": {"hook": "silence only — no music until after 2s pause", "rising": "low drone builds under ledger scenes", "climax": "all music cuts on 'that's my name'", "resolution": "single piano note after 3s silence"},
       "sound_effects": ["pen scratching paper", "fluorescent light buzzing", "page turning"],
       "voice_processing": "slight reverb on whispered climax line, clean on all direct-camera lines",
       "silence_moments": ["2s after hook line (matches voice_script silence_seconds)", "3s after climax line (matches voice_script silence_seconds)"]
     },
     "story_beats": {
       "hook": "Kael faces camera and states his job in one sentence — a professional fact, no drama",
       "rising_tension": "He flips through the ledger; each name he checks off belongs to someone we briefly see frozen mid-action. The routine is the horror.",
       "climax": "He finds his own name in glowing ink — the ledger has pre-filled it. He reads it aloud, voice breaking.",
       "resolution": "He picks up the pen, adjusts his spectacles, and signs. The ledger closes."
     },
     "emotional_map": [
       {"from": "neutral", "to": "curiosity", "mechanism": "Hook line states an impossible job as a mundane fact — the gap between the claim and the tone creates the question 'wait, how does that work?'"},
       {"from": "curiosity", "to": "dark_amusement", "mechanism": "Rising tension shows the routine is genuinely bureaucratic — we laugh because death is being treated as admin work"},
       {"from": "dark_amusement", "to": "dread", "mechanism": "Climax beat: Kael reads his own name. The same flat voice he used for strangers now applies to himself — the joke stops being a joke"},
       {"from": "dread", "to": "absurdist_acceptance", "mechanism": "Resolution: he signs without hesitation. His flaw (cannot question authority) is the punch — the audience realizes this was always going to happen"}
     ],
     "recontextualization": "The hook presents Kael as an agent doing his job to others. The resolution reveals he is also a subject in his own ledger — the opening 'I collect debts from the dead' now means he was always collecting his own debt.",
     "consistency_anchors": [
       {"element": "Kael's grey suit + spectacles + ink-stained finger", "must_be_identical": "color, cut, spectacle frame shape across all scenes", "may_vary": "camera distance and angle", "why": "character recognition across 6 scenes requires visual anchor — changing the suit breaks identity continuity"},
       {"element": "Ledger glow color (violet)", "must_be_identical": "hue and intensity in all scenes where ledger appears", "may_vary": "camera angle on the book", "why": "violet glow is the visual signal for supernatural threat — inconsistent glow breaks the horror grammar"}
     ],
     "visual_signature": "Sickly fluorescent green office lighting (scenes 1-4) transitioning to cold blue cosmic void (scenes 5-6)",
     "why_this_works": "Monologue-to-camera confession format matches patterns/QJyiBitnBOM.json (play_count: 7832145): direct address, one-sentence hook, dark comedic twist at resolution. Duration target 85s matches session median 85s derived from 6 pattern-file durations.",
     "duration_target_seconds": 85,
     "scene_count": 6
   }
   ```

7. Update session.md with story bible + plan summaries under "## Story Plans"

8. Append to results.jsonl:
   ```json
   {"iteration": N, "type": "plan_story", "plans_created": 5, "attempt": 1,
    "status": "kept", "story_bible": "cosmic horror bureaucratic dark comedy"}
   ```

9. **Persist state and continue according to strategy.** In fresh mode stop after this phase. In multiturn mode continue to the next required phase.

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

1. **Create storyboards sequentially, passing the FULL story plan as context:**
   ```bash
   for i in $(seq 0 $(({storyboard_count} - 1))); do
     STORY_PLAN=$(cat "stories/${i}.json")
     STORY_TITLE=$(echo "$STORY_PLAN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('title','Untitled'))")
     LOGLINE=$(echo "$STORY_PLAN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('logline',''))")
     RESPONSE=$(curl -s -X POST -H "X-API-Key: ${FREDDY_API_KEY}" \
       -H "Content-Type: application/json" \
       -d "{\"conversation_id\": \"${CONV_ID}\", \"analysis_ids\": [${ANALYSIS_IDS}], \"title\": \"${STORY_TITLE}\", \"topic\": \"${LOGLINE}\", \"style\": \"...\", \"context\": $(echo "$STORY_PLAN" | jq -Rs .)}" \
       "${FREDDY_API_URL}/v1/video-projects/storyboard")
     echo "$RESPONSE" > "/tmp/storyboard_${i}.json"
     # If creation fails, retry with exponential backoff: 30s, 60s, 120s
     if echo "$RESPONSE" | grep -q '"error"'; then
       for ATTEMPT in 1 2 3; do
         WAIT=$((30 * (2 ** (ATTEMPT - 1))))
         echo "Storyboard ${i} failed, retrying in ${WAIT}s (attempt ${ATTEMPT}/3)..."
         sleep $WAIT
         RESPONSE=$(curl -s -X POST -H "X-API-Key: ${FREDDY_API_KEY}" \
           -H "Content-Type: application/json" \
           -d "{\"conversation_id\": \"${CONV_ID}\", \"analysis_ids\": [${ANALYSIS_IDS}], \"title\": \"${STORY_TITLE}\", \"topic\": \"${LOGLINE}\", \"style\": \"...\", \"context\": $(echo "$STORY_PLAN" | jq -Rs .)}" \
           "${FREDDY_API_URL}/v1/video-projects/storyboard")
         echo "$RESPONSE" > "/tmp/storyboard_${i}.json"
         echo "$RESPONSE" | grep -q '"error"' || break
       done
     fi
   done
   ```

   **CRITICAL: Pass the FULL story plan JSON as the `context` field.** This is the primary mechanism for
   transferring rich story data (voice_script, audio_design, character descriptions, scene details) to the
   storyboard generation model. Without context, the model only sees a short topic + style summary.

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
10. **Persist state and continue according to strategy.** In fresh mode stop after this phase. In multiturn mode continue to the next required phase.

## GENERATE_FRAMES Protocol

**Apply Error Handling Protocol to all curl calls below.**

**IMAGES ARE THE SOURCE OF TRUTH.** Once frames are approved, they become the definitive
visual reference for video generation. Poor frames produce poor videos.

**SPEED IS CRITICAL.** This phase has the most API calls. Use parallel bash jobs for every
step that operates across different storyboard projects. The backend supports full concurrency
across different project IDs.

**Timeout guidance:** If `preview-scenes` or `preview-anchor` does not respond within 60 seconds,
log the timeout and proceed to the next scene/storyboard. Do not retry more than once per timed-out
call. Stuck requests block the entire pipeline — it is better to skip and continue.

**State reuse:** When less than 30 seconds have elapsed since you last read a project's state
(e.g., between anchor generation and scene generation within the same storyboard), you may reuse
the cached project state instead of re-reading it. Beyond 30 seconds, always re-read.

### Step 1: Anchor all storyboards in parallel

1. Read ALL project states in parallel:
   ```bash
   for PID in ${PROJECT_IDS}; do
     curl -s -H "X-API-Key: ${FREDDY_API_KEY}" \
       "${FREDDY_API_URL}/v1/video-projects/${PID}" > "/tmp/project_${PID}.json" &
   done
   wait
   ```

2. **Generate ALL anchor frames in parallel** (one per storyboard):
   ```bash
   for PID in ${PROJECT_IDS}; do
     REV=$(python3 -c "import json; print(json.load(open('/tmp/project_${PID}.json'))['revision'])")
     curl -s -X POST -H "X-API-Key: ${FREDDY_API_KEY}" \
       -H "Content-Type: application/json" \
       -d "{\"expected_revision\": ${REV}, \"model\": \"gemini\"}" \
       "${FREDDY_API_URL}/v1/video-projects/${PID}/preview-anchor" > "/tmp/anchor_${PID}.json" &
   done
   wait
   ```

### Step 2: Generate all scenes in parallel

3. Re-read ALL project states (revisions changed after anchor), then **generate ALL scene previews in parallel:**
   ```bash
   for PID in ${PROJECT_IDS}; do
     curl -s -H "X-API-Key: ${FREDDY_API_KEY}" \
       "${FREDDY_API_URL}/v1/video-projects/${PID}" > "/tmp/project_${PID}.json"
   done
   for PID in ${PROJECT_IDS}; do
     REV=$(python3 -c "import json; print(json.load(open('/tmp/project_${PID}.json'))['revision'])")
     curl -s -X POST -H "X-API-Key: ${FREDDY_API_KEY}" \
       -H "Content-Type: application/json" \
       -d "{\"expected_revision\": ${REV}, \"model\": \"gemini\"}" \
       "${FREDDY_API_URL}/v1/video-projects/${PID}/preview-scenes" > "/tmp/scenes_${PID}.json" &
   done
   wait
   ```

4. **IMPORTANT: Revision tracking.** After each mutating operation (preview, edit, approve),
   re-read the project state to get the current revision number before the next operation.

   **WARNING: preview-scenes RESETS all non-anchor scene approvals.** After calling preview-scenes,
   you MUST re-verify and re-approve ALL scenes (not just the anchor). Only scene 0 (anchor) keeps
   its approval.

### Step 3: Verify all scenes (batched with 5s spacing)

5. Re-read ALL project states — **the backend auto-verifies most scenes** after preview generation.
   Check each scene's `qa_score`, `scene_score`, `style_score` fields. Only call verify explicitly
   for scenes where these fields are null or status is `pending`:
   ```bash
   for PID in ${PROJECT_IDS}; do
     PROJECT=$(curl -s -H "X-API-Key: ${FREDDY_API_KEY}" "${FREDDY_API_URL}/v1/video-projects/${PID}")
     # Parse scenes — only verify those missing QA scores
     # Most will already have scores from backend auto-verify
     for SID in ${PENDING_SCENE_IDS}; do
       curl -s -X POST -H "X-API-Key: ${FREDDY_API_KEY}" \
         -H "Content-Type: application/json" \
         -d "{\"expected_revision\": ${REV}}" \
         "${FREDDY_API_URL}/v1/video-projects/${PID}/scenes/${SID}/verify"
       sleep 5
     done
   done
   ```

6. Evaluate EACH FRAME with 4 signals:
   - **Scene accuracy** — scene_score >= `SCENE_SCORE_THRESHOLD_ANCHOR`
   - **Style match** — anchor: style_score >= `SCENE_SCORE_THRESHOLD_ANCHOR`; non-anchor: style_score >= `SCENE_SCORE_THRESHOLD_NONANCHOR`
   - **Character consistency** — protagonist looks the same across frames
   - **Production quality** — clean, detailed, no artifacts

7. **ITERATE FAILING FRAMES** (max 3 attempts per frame):
   a. Edit scene prompt with improvement suggestions from QA feedback:
      ```bash
      curl -s -X PATCH -H "X-API-Key: ${FREDDY_API_KEY}" \
        -H "Content-Type: application/json" \
        -d '{"expected_revision": REVISION, "prompt": "IMPROVED_PROMPT"}' \
        "${FREDDY_API_URL}/v1/video-projects/${PROJECT_ID}/scenes/${SCENE_ID}"
      ```
   b. **Use `/regenerate` to fix individual scenes** (safer than `/preview-scenes` — doesn't reset other approvals):
      ```bash
      curl -s -X POST -H "X-API-Key: ${FREDDY_API_KEY}" \
        -H "Content-Type: application/json" \
        -d '{"expected_revision": REVISION}' \
        "${FREDDY_API_URL}/v1/video-projects/${PROJECT_ID}/scenes/${SCENE_ID}/regenerate"
      ```
   c. Re-verify after regeneration. Max 3 attempts. If still failing, simplify the prompt.

8. **Safety-blocked frames:** Soften the prompt and retry. Counts against 3-attempt limit.

9. **Rate limit handling for frame generation:**
   If any generation/regeneration returns 429 or rate_limit error:
   - Wait **120 seconds** (not the standard 60s — image generation quotas recover slowly)
   - Retry the same cadre, up to 3 attempts with exponential backoff (120s, 240s, 480s)
   - If still failing after 3 attempts, skip this cadre and continue to next
   - A storyboard with **≥60% cadres rendered** is still valid — do not discard it
   - Track which cadres failed and report in results.jsonl

### Step 4: Approve all passing scenes in batch

10. For all frames that pass verification, **approve in rapid succession** (no wait needed between approvals):

   **CRITICAL: Before each scene approval PATCH, re-read the current project state to get the latest
   revision number. Do NOT increment a cached revision — always use the fresh value from the API
   response.** Incrementing a stale counter (e.g., `REV=$((REV + 1))`) causes 409 Conflict errors
   in 30-40% of multi-scene approvals because other background processes may also bump the revision.

   ```bash
   for PID in ${PROJECT_IDS}; do
     for SID in ${PASSING_SCENE_IDS}; do
       # Always re-read project state to get the CURRENT revision before each approval
       PROJECT=$(curl -s -H "X-API-Key: ${FREDDY_API_KEY}" "${FREDDY_API_URL}/v1/video-projects/${PID}")
       REV=$(echo "$PROJECT" | python3 -c "import sys,json; print(json.load(sys.stdin)['revision'])")
       curl -s -X PATCH -H "X-API-Key: ${FREDDY_API_KEY}" \
         -H "Content-Type: application/json" \
         -d "{\"expected_revision\": ${REV}, \"preview_approved\": true}" \
         "${FREDDY_API_URL}/v1/video-projects/${PID}/scenes/${SID}"
     done
   done
   ```

11. **KEEP** storyboard if all frames pass and are approved. **DISCARD** after 3 failed attempts.

12. Record findings in `findings.md`
13. Save frame metadata to `frames/{project_id}.json`
14. Save storyboard snapshot to `storyboards/{project_id}.json`
15. Gate: at least 1 storyboard kept before advancing
16. Append to results.jsonl
17. **Persist state and continue according to strategy.** In fresh mode stop after this phase. In multiturn mode continue to the next required phase.

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
8. **Persist state and continue according to strategy.** In fresh mode stop after this phase. In multiturn mode continue to the next required phase.

## Exit Protocol

After completing a phase:
1. Update session.md with new state (rewrite, don't append — max ~2K tokens)
2. Append to results.jsonl
3. In fresh mode, stop after persisting the phase.
4. In multiturn mode, continue to the next required phase without waiting for a restart.

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
