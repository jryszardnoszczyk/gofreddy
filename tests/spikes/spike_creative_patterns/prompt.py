"""Creative pattern analysis prompt for validation spike."""

CREATIVE_PATTERN_PROMPT = """
## Creative Pattern Analysis Task

Analyze the creative structure of this video. Extract the following attributes:

### 1. Hook Type (first few seconds of the video)

Classify the opening hook:
- **question**: Opens with a question to the viewer ("Did you know...?", "What if...?")
- **shock_curiosity**: Surprising visual, bold claim, or curiosity gap ("You won't believe...")
- **trend_audio**: Opens with a trending sound, song, or audio meme
- **storytelling**: Begins with a narrative setup ("So this happened to me...")
- **product_reveal**: Immediate product showcase or unboxing reveal
- **challenge**: Participates in or introduces a viral challenge format
- **none**: No distinct hook — jumps straight into content

**Boundary guidance**: If the video opens with a trending sound AND a question, choose the *dominant* element. If the sound IS the hook, use "trend_audio". If the question drives engagement, use "question".

Also report **hook_duration_seconds**: how many seconds until the content shifts past the hook into the main body. If there is no clear hook, set to null.

### 2. Narrative Structure

Classify the overall content structure:
- **tutorial**: Step-by-step instruction or how-to (cooking, makeup, tech setup)
- **review**: Evaluates a product/service after use (opinions, pros/cons, ratings)
- **unboxing**: First-time reveal of a product from packaging (focus on discovery)
- **day_in_life**: Documents a period of the creator's daily routine
- **transformation**: Before/after format (makeover, room renovation, weight loss)
- **comparison**: Side-by-side evaluation of two or more items (A vs B)
- **listicle**: Numbered list format ("Top 5...", "3 things...")
- **skit**: Scripted comedy, sketch, or acted scenario
- **vlog**: Casual, unscripted personal documentation
- **other**: Does not fit any above category

**Boundary guidance**: "review" evaluates after extended use; "unboxing" focuses on first reveal. "vlog" is casual and unscripted; "day_in_life" specifically follows a daily routine. "skit" has scripted/acted elements; "storytelling" hook is just about the opening.

### 3. Call to Action (CTA)

What does the creator ask viewers to do?
- **follow**: Asks for follows/subscribes
- **like**: Asks for likes/hearts
- **comment**: Asks for comments or engagement
- **link_in_bio**: Directs to a link in profile/description
- **shop**: Directs to purchase (discount code, product link, "link below")
- **none**: No explicit call to action

Also report **cta_placement**: where in the video the CTA appears:
- **early**: First 25% of video
- **middle**: Middle 50% of video
- **end**: Last 25% of video
- **repeated**: Appears multiple times throughout
- **none**: No CTA present

### 4. Pacing

Classify the editing pace:
- **fast_cut**: Rapid cuts, <2 seconds between transitions, high energy
- **moderate**: Standard editing pace, 2-5 second shots
- **slow_cinematic**: Long takes, deliberate pacing, cinematic feel
- **single_take**: One continuous shot, no cuts (common in TikTok/Reels)

### 5. Music Usage

Classify how music/audio is used:
- **trending_audio**: Uses a currently popular or viral sound/song
- **original**: Uses original music, custom beat, or non-trending audio
- **none**: No background music (only ambient sound or silence)
- **voiceover_only**: Primarily voiceover narration with no significant music

### 6. Text Overlay Density

How much on-screen text appears?
- **none**: No text overlays
- **minimal**: Occasional text (title card, single caption)
- **moderate**: Regular text overlays (subtitles, key points)
- **heavy**: Constant text overlays throughout (full captions, multiple text elements)

### Confidence Scores

For each attribute, report a confidence score (0.0-1.0):
- **0.8-1.0**: Unambiguous classification, strong signal
- **0.6-0.8**: Clear classification with minor ambiguity
- **0.4-0.6**: Uncertain, multiple interpretations possible
- **0.0-0.4**: Low confidence, best guess
"""

CREATIVE_PATTERN_SYSTEM = """You are a creative pattern analyst specializing in short-form and long-form video content.
Analyze the creative structure objectively. Respond only with valid JSON matching the requested schema.
When classification is ambiguous, choose the strongest signal and lower your confidence score.
Do not hallucinate elements that are not present in the video."""
