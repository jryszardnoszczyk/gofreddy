"""Modified brand detection prompt with timestamp_end for validation spike.

Based on BRAND_DETECTION_PROMPT from src/prompts.py:461-555.
Only change: added timestamp_end to output requirements (item 5).
"""

SPIKE_BRAND_DETECTION_PROMPT = """
## Brand Detection and Sentiment Analysis Task

Analyze this video to identify ALL brand mentions and products.

### Detection Sources (prioritized by reliability)

1. **SPEECH** (Highest reliability - 95%+)
   - Brand names mentioned verbally
   - Product names spoken
   - Company names referenced

2. **TEXT_OVERLAY** (High reliability - 90%+)
   - On-screen text showing brand names
   - Captions mentioning brands
   - Product labels visible
   - Hashtags (#Nike, brand hashtags)

3. **VISUAL_LOGO** (Moderate reliability - 65-80%)
   - Logos visible on products
   - Brand signage in background
   - Logo on clothing/accessories
   NOTE: Visual logo detection has lower accuracy. Include with appropriate confidence.

4. **HASHTAG**
   - Brand-related hashtags visible in text

### Sentiment Analysis Per Brand

For EACH brand mentioned, analyze sentiment:

1. **POSITIVE**: Endorsement, recommendation, positive experience
   - "I love my new Nike shoes"
   - "This product changed my life"
   - Enthusiastic tone, positive adjectives

2. **NEUTRAL**: Factual mention, no opinion
   - "These are Nike shoes"
   - Just showing/naming without opinion
   - News-style reporting

3. **NEGATIVE**: Criticism, complaint, negative experience
   - "I had issues with this product"
   - "Don't buy this"
   - Disappointed tone, negative adjectives

4. **MIXED**: Conflicting sentiments
   - "I love the design but hate the price"

### Context Classification

For each brand, identify the context:
- **ENDORSEMENT**: Positive promotion (paid or organic)
- **COMPARISON**: Compared to other products
- **BACKGROUND**: Incidental appearance, not focus
- **CRITICISM**: Negative feedback
- **SPONSORED**: Appears to be paid partnership
- **REVIEW**: Product review/unboxing

### Output Requirements

For EACH detected brand:
1. **brand_name**: Exact brand name (normalize: "Apple Inc." -> "Apple")
2. **detection_source**: speech, text_overlay, visual_logo, hashtag
3. **confidence**:
   - 0.9+: Clear verbal mention OR visible text
   - 0.7-0.9: Recognizable product without explicit mention
   - 0.5-0.7: Partial/uncertain detection
4. **timestamp_start**: When brand first appears (M:SS format, optional)
5. **timestamp_end**: When brand disappears or mention ends (M:SS format, optional). \
For speech mentions, this is when the speaker finishes saying the brand name or stops \
discussing the brand. For visual detections, this is when the logo/product leaves the \
frame or is no longer visible. If the brand is continuously visible for a segment, \
capture the full start-to-end range.
6. **sentiment**: positive / neutral / negative / mixed
7. **context**: endorsement / comparison / background / criticism / sponsored / review
8. **evidence**: Exact quote or description supporting detection
9. **is_competitor**: true if this brand competes with the primary/featured brand

### Competitor Detection

Flag brands as competitors using is_competitor=true when:
- Brand is in same product category as prominently featured brand
- Brand is compared directly to the primary brand

### Sponsored Content Signals

Set has_sponsorship_signals=true if:
- Verbal disclosure ("sponsored by", "paid partnership")
- FTC hashtags (#ad, #sponsored)
- Prominent product placement with endorsement context
- "Link in bio" or discount code mentions

### IMPORTANT

- List ALL brands detected, including background appearances
- For visual-only detections with <70% confidence, still include but note uncertainty
- When multiple detection sources confirm same brand, use highest confidence
- Normalize brand names (lowercase variations -> canonical name)
- For timestamp_end: if you cannot determine when a brand disappears, leave it null
"""

SPIKE_BRAND_DETECTION_SYSTEM = """
You are a brand detection and sentiment analyst. Respond only with valid JSON matching the requested schema.
Focus on accuracy: if uncertain about a brand name, lower confidence rather than guess.
For visual logo detection, be conservative - only report when clearly recognizable.
For timestamp_end: report the actual moment the brand is no longer visible or mentioned. \
If uncertain, leave null rather than guess."""
