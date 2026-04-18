---
phases:
  1: [A1, A12, B1, B16, C7, C12]
  2: [A2, A3, A5, A6, B2, B3, B4, B5, C1, C2, C16]
  3: [A4, A7, A8, A9, A10, A11, B6, B7, B8, B9, B10, B11, B12, B13, B14, B15, C3, C4, C5, C6, C8, C9, C10, C11, C13, C14, C15]
tracks:
  a: [A1, A2, A3, A4, A8, A12]
  b: [A5, A6, A7, A9, A10, A11]
  c: [B1, B2, B3, B4, B5, B6, B7]
  d: [B8, B9, B10, B11, B12, B13, B14, B15, B16]
  e: [C1, C2, C3, C4, C5]
  f: [C6, C7, C8, C9, C10, C11, C12, C13, C14, C15, C16]
---

# QA Harness Test Matrix

All 23 agent capabilities + 34 canvas sections + 4 standalone dashboard pages, organized into 3 parallel evaluator tracks with natural user flows.

**Convergence rule**: Flow 1 per track uses fixed prompts — these are the reference queries for convergence measurement. Flow 4 uses dynamic/exploratory prompts excluded from convergence checks.

**Phase scoping**: The YAML frontmatter above maps phase number → list of capability IDs. Set the `PHASE` env var when running the harness (e.g. `PHASE=1 ./scripts/eval_fix_harness.sh`) to restrict the evaluator to that subset. `PHASE=all` runs the full matrix. Phase 1 is a smoke subset (UI-heavy, minimal external API use). Phase 2 adds core high-priority flows. Phase 3 is the long tail including deepfake (A4, currently blocked by missing API keys). Edit the YAML block to revise phase membership; IDs must match the `#` column in the tables below.

---

## Track A — Analysis Domain

### Flow 1 (Fixed — convergence reference)

One conversation. Send each prompt sequentially, waiting for SSE completion between them.

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| A1 | "Search for TikTok cooking videos" | `search` | `search` | 60s | Agent calls `search` and the search canvas section renders with at least 1 result. If the requested platform is unavailable, the agent must explain the limitation in chat text and suggest an alternative (e.g. `discover_creators` for TikTok). No console errors. |
| A2 | "Analyze the first video" | `analyze_video` | `analysis` | 120s | Analysis section renders with scores (brand safety, moderation). Video metadata displayed. Cost badge visible in telemetry. |
| A3 | "Check this video for fraud" | `detect_fraud` | `fraud` | 90s | Fraud report section renders with audience quality metrics. Risk level indicator present. |
| A4 | "Run deepfake detection on this video" | `detect_deepfake` | `deepfake` | 90s | Deepfake section renders with detection result (real/synthetic). Confidence score visible. |

### Flow 2

One conversation.

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| A5 | "Find cooking creators on TikTok" | `discover_creators` | `creator_search` | 60s | Creator search results with profile cards (avatar, handle, follower count). At least 1 creator. |
| A6 | "Evaluate the top creator for brand safety" | `evaluate_creators` | `evaluation` | 90s | Evaluation section with risk assessment, scores, recommendations. |
| A7 | "Show me this creator's profile and evolution" | `creator_profile` | `creator` | 90s | Creator profile section with platform stats, growth metrics. Evolution data if available. |

### Flow 3

One conversation.

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| A8 | "Search for 3 short Instagram fitness videos and analyze all of them" | `search` then `analyze_video` (batch) | `batch` or `analysis` | 180s | Multiple analyses queued/completed. Batch progress or multiple analysis sections visible. |

### Flow 4 (Dynamic — excluded from convergence)

One conversation. The evaluator picks videos dynamically.

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| A9 | "Search for YouTube tech review videos uploaded recently" | `search` | `search` | 60s | Results from YouTube. Platform filter working. |
| A10 | "Analyze the most interesting one and check for sponsored content" | `analyze_video` | `analysis` | 120s | Analysis with brand/sponsored content detection. |
| A11 | "Do a deep content analysis on this video — what makes it engaging?" | `analyze_content` | `content_analysis` | 90s | Content analysis section renders with engagement factors, creative patterns, or content breakdown. |

### Page Test: Library

No chat interaction. Navigate directly.

| # | Action | Route | Timeout | Pass Criteria |
|---|--------|-------|---------|---------------|
| A12 | Navigate to `/dashboard/library` | Library page | 30s | Page renders. Video cards visible (or empty state). Filter controls present (platform, date, type). Session groups and creator groups displayed if data exists. No console errors. |

---

## Track B — Operations Domain

### Flow 1 (Fixed — convergence reference)

One conversation.

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| B1 | "Create a new brand monitor for 'sustainable fashion' tracking TikTok and Instagram" | `manage_monitor` | `monitor` | 90s | Monitor section renders with created monitor. Name, platforms, keywords visible. |
| B2 | "Show me the latest mentions for this monitor" | `query_monitor` | `monitor_mentions` | 60s | Monitor mentions section renders. Mention cards with source, date, sentiment if available. |
| B3 | "Show analytics for this monitor" | `query_monitor` | `monitor_analytics` | 60s | Monitor analytics section with charts/metrics. Mention volume, sentiment trends. |

### Flow 2

One conversation.

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| B4 | "Run an SEO audit for freddy.example" | `seo_audit` | `search_optimization_report` | 120s | SEO report section renders with technical scores, keyword analysis. |
| B5 | "Check our AI search visibility — are we showing up in ChatGPT, Perplexity, and Gemini?" | `geo_check_visibility` | `geo_visibility` | 120s | GEO visibility section with per-engine results. Citation status per platform. |
| B6 | "Generate GEO-optimized content based on these findings" | `generate_content` or agent follow-up | `geo_optimized_content` or `brief` | 90s | Content section renders with optimized text or creative brief. |
| B7 | "Find competitor ads in the AI marketing space" | `competitor_ads` | `competitive_brief` | 90s | Competitor brief section with ad examples, positioning analysis. |

### Flow 3

One conversation.

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| B8 | "Show me the content calendar for this week" | agent navigates to publish tab | `content_calendar` | 60s | Calendar section renders. Date grid visible. May be empty if no scheduled content. |
| B9 | "Show the publish queue" | agent navigates | `publish_queue` | 60s | Publish queue section renders. Queue items or empty state. |
| B10 | "Show me comment inbox" | `manage_comments` | `comment_inbox` | 60s | Comment inbox section renders. Comment list or empty state. |
| B11 | "Evaluate our content against our brand safety policy" | `manage_policy` | `policy` | 90s | Policy evaluation section renders with compliance status or policy details. |

### Flow 4 (Dynamic — excluded from convergence)

One conversation.

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| B12 | "Show my account dashboard with recent activity" | `account_analytics` | `account_dashboard` | 60s | Account dashboard renders with activity metrics. |
| B13 | "Show the media library" | `manage_media` | `media_library` | 60s | Media library section renders. Grid/list of media or empty state. |
| B14 | "Preview the newsletter" | `manage_newsletter` | `newsletter_preview` | 60s | Newsletter preview section renders. |
| B15 | "Show me client management — list all clients" | `manage_client` | `client_management` | 60s | Client management section renders. Client list or empty state with create option. |

### Page Test: Monitoring

No chat interaction.

| # | Action | Route | Timeout | Pass Criteria |
|---|--------|-------|---------|---------------|
| B16 | Navigate to `/dashboard/monitoring` | Monitoring page | 30s | Page renders. Monitor cards visible (or empty state with create CTA). Freshness indicators if monitors exist. No console errors. |

---

## Track C — Platform Domain

### Flow 1 (Fixed — convergence reference)

One conversation.

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| C1 | "Create a creative brief for a summer fashion campaign targeting Gen Z on TikTok" | `generate_content` | `brief` | 90s | Creative brief section renders with campaign concept, target audience, content pillars. |
| C2 | "Now generate social media content based on this brief" | `generate_content` | `brief` or content output | 90s | Content generation output renders. Social post drafts or content variants visible. |
| C3 | "Show me the viral library — what's trending right now?" | `workspace` or navigation | `viral_library` | 60s | Viral library section renders with trending content cards. |

### Flow 2

One conversation.

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| C4 | "Start a new video project — a 30-second product demo for a fitness app" | `video_project` | `storyboard` | 90s | Storyboard section renders in studio tab. Project created with scenes/shots. |
| C5 | "Generate the video from this storyboard" | `video_generate` | `generation` or `storyboard` | 120s | Generation progress section renders. Progress indicators visible. May show editor when complete. |

### Flow 3

One conversation for C6 only. C7 is a direct page navigation (no chat).

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| C6 | "Show my usage and billing" | `check_usage` | `usage` | 30s | Usage card renders with credit balance, API calls, cost breakdown. |

### Page Test: Settings

No chat interaction. Navigate directly to the route. Do NOT type "Open settings" in the chat — the agent has no navigation tool; test the settings page by URL navigation.

| # | Action | Route | Timeout | Pass Criteria |
|---|--------|-------|---------|---------------|
| C7 | Navigate to `/dashboard/settings` | Settings page | 30s | Page renders. API keys section, model selection, billing visible. No console errors. |

### Flow 4 (Dynamic — excluded from convergence)

One session. Tests agent core behaviors.

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| C8 | "hmm what can you do?" | Agent responds with capabilities | Text response | 60s | Agent responds with a helpful capability overview. No tool call needed. Text renders in chat. No errors. |
| C9 | "Search for fitness videos on TikTok and also check if any of them are fraudulent" | `search` then `detect_fraud` | `search` then `fraud` | 120s | Multi-tool: agent calls search, then fraud. Both sections render in sequence. Canvas shows both results. |
| C10 | "What did we find in our workspace so far?" | `workspace` | `search` (workspace query) | 60s | Workspace query returns previously saved results from the current session. |
| C11 | Send a message that triggers a backend error (e.g., "Analyze video at invalid://url") | Error handling | Error message in chat | 60s | Error is handled gracefully. No crash. Error message shown in chat. No unhandled console errors. App remains usable (can send another message). |

### Page Test: Sessions + Conversation CRUD + Split View

No chat interaction for page test. For CRUD, use chat interactions.

| # | Action | Route | Timeout | Pass Criteria |
|---|--------|-------|---------|---------------|
| C12 | Navigate to `/dashboard/sessions` | Sessions page | 30s | Page renders. Session list visible (or empty state). Session cards show title, date, action count. No console errors. |
| C13 | Create new conversation (click new chat button from dashboard) | `/dashboard` | 30s | New conversation created. Chat input focused. URL updates to include conversation ID. |
| C14 | Send a message in new conversation, then rename it | `/dashboard/c/:id` | 60s | Message sends and renders. Rename updates sidebar title. |
| C15 | Delete the conversation | Sidebar action | 30s | Conversation removed from sidebar. Redirects to dashboard or next conversation. No orphaned state. |
| C16 | Test split-view collapse/restore (click canvas collapse button) | `/dashboard/c/:id` | 30s | Canvas panel collapses. Chat expands to full width. Restore button brings canvas back. No layout glitches. |

---

## Cross-Cutting Checks (Applied to Every Test)

After every capability test, the evaluator MUST:

1. **Console errors**: Run `playwright-cli console` and apply filtering rules from the evaluator base prompt.
2. **SSE completion**: Verify the chat input is re-enabled and streaming indicator is gone.
3. **Canvas rendering**: Verify the correct canvas section type is displayed (not a wrong section or blank).
4. **No crash**: App is still usable — can type in the chat input.

---

## Capability Coverage Summary

| Track | Capabilities Tested | Canvas Sections Hit | Pages Tested |
|-------|--------------------|--------------------|--------------|
| A | search, analyze_video, detect_fraud, detect_deepfake, discover_creators, evaluate_creators, creator_profile, analyze_content | search, analysis, fraud, deepfake, creator_search, evaluation, creator, batch, content_analysis | Library |
| B | manage_monitor, query_monitor, seo_audit, geo_check_visibility, competitor_ads, generate_content, manage_comments, account_analytics, manage_media, manage_newsletter, manage_policy, manage_client | monitor, monitor_mentions, monitor_analytics, search_optimization_report, geo_visibility, geo_optimized_content, competitive_brief, content_calendar, publish_queue, comment_inbox, account_dashboard, media_library, newsletter_preview, policy, client_management | Monitoring |
| C | generate_content, video_project, video_generate, check_usage, workspace, think (implicit) | brief, viral_library, storyboard, generation, usage | Sessions, Settings |

**Total**: 23 unique tools, 34 canvas section types, 4 standalone pages
