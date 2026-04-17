# InsightIQ (formerly Phyllo) API Research

**Date:** 2026-03-07
**Status:** Research complete (with noted gaps where docs are behind auth/SPA rendering)

---

## 1. API Fundamentals

### Authentication
- **Method:** Basic Auth using `client_id` and `client_secret`
- **Header:** `Authorization: Basic <base64(client_id:client_secret)>`
- **Security requirement:** API calls MUST be made server-side only, never from frontend/app
- **SDK Token:** For Connect SDK flows, generate a short-lived token via `POST /v1/sdk-token` (valid 1 week / 604800 seconds)

### Base URLs
- **Sandbox:** `https://api.sandbox.insightiq.ai`
- **Production:** `https://api.insightiq.ai` (inferred from sandbox pattern)

### General API Design
- RESTful, JSON-encoded responses, JSON payloads over HTTPS
- Pagination: **offset-based** (`limit` + `offset` query parameters)
- Response envelope: `metadata` object contains `offset`, `limit`, `from_date`, `to_date`
- UUIDs used for all entity IDs (format: `8ba1ac32-0f3c-4cf0-8d89-79a183258f6a`)

### Products (specified when creating SDK tokens)
- `IDENTITY` - profile data
- `IDENTITY.AUDIENCE` - audience demographics
- `ENGAGEMENT` - content and engagement metrics
- `ENGAGEMENT.AUDIENCE` - engagement audience data
- `INCOME` - creator income data

---

## 2. Endpoint Schemas

### 2.1 Creator Discovery (Search)

**Endpoint:** Creator discovery search (exact path: likely `POST /v1/social/creators/profiles/search`)

**Database:** 450M+ creator profiles indexed
- 130M+ Instagram creators
- 100M+ TikTok creators
- 8M+ YouTube creators
- Minimum threshold: 2,000 followers (nano-influencers under 1K also available per comparison docs)

**Search Filters (50+ available):**
- `platform` / `work_platform_id` (string) - youtube, tiktok, instagram
- `niche` (string) - content category
- `followers_min` / `followers_max` (integer)
- Engagement rate range
- Location / geography
- Audience demographics (age, gender, country)
- Brand affinity
- Purchase intent
- Credibility score
- Hashtags, mentions, keywords
- Lookalike search (find similar creators to a given profile)
- Contact availability (email, phone)

**Response Schema (Creator Object):**
```json
{
  "creators": [
    {
      "id": "string (UUID)",
      "name": "string",
      "platform": "string",
      "niche": "string",
      "followers": "integer"
    }
  ]
}
```

**Note:** The Context7-indexed docs show a simplified schema. Based on marketing materials
and the 100+ profile attributes claim, the full creator profile object likely includes:

```
Creator Profile Object (reconstructed from all sources):
- id (string, UUID)
- name / full_name (string)
- platform / work_platform (object: {id, name, logo_url})
- platform_username (string)
- niche (string)
- followers / follower_count (integer)
- engagement_rate (number)
- average_likes (integer)
- average_views (integer)
- average_comments (integer)
- growth_rate (number)
- bio (string)
- profile_url (string)
- picture_url (string)
- location (string/object)
- gender (string)
- is_verified (boolean)
- account_type (string)
- contact_info (object: {email, phone, social_handles, links_in_bio})
- credibility_score (number)
- brand_affinity (array)
- content_topics / interests (array)
- reel_plays (integer, Instagram)
- paid_post_performance (object)
- sponsored_post_indicators (boolean)
```

### 2.2 Profile Analytics

**Endpoint:** `POST /v1/social/creators/profiles/analytics`
(documented at: `docs.insightiq.ai/.../create-a-v-1-social-creator-profile-analytics`)

**Purpose:** Get public analytics of a profile using username or link (no creator auth needed).

**Analytics data returned (from marketing/product docs):**
- Follower count and growth rate
- Engagement rate and trends
- Average likes, comments, shares, views
- Reel plays (Instagram)
- Paid post performance metrics
- Real vs. fake engagement scoring
- Audience quality assessment
- Content performance over time
- 100+ profile analysis attributes

### 2.3 Content / Posts

**Endpoint:** `GET /v1/publications/contents`

**Query Parameters:**
- `account_id` (string, required)
- `from_date` (string, YYYY-MM-DD, optional)
- `to_date` (string, YYYY-MM-DD, optional)
- `limit` (integer, default 10)
- `offset` (integer, default 0)

**Response Schema (fully documented):**
```json
{
  "data": [
    {
      "id": "UUID",
      "created_at": "ISO 8601 timestamp",
      "updated_at": "ISO 8601 timestamp",
      "user": {
        "id": "UUID",
        "name": "string"
      },
      "account": {
        "id": "UUID",
        "platform_username": "string"
      },
      "work_platform": {
        "id": "UUID",
        "name": "string (YouTube|Twitter|Instagram|TikTok)",
        "logo_url": "URL string"
      },
      "engagement": {
        "like_count": "integer|null",
        "dislike_count": "integer|null",
        "comment_count": "integer|null",
        "impression_organic_count": "integer|null",
        "reach_organic_count": "integer|null",
        "save_count": "integer|null",
        "view_count": "integer|null",
        "watch_time_in_hours": "number|null",
        "share_count": "integer|null",
        "impression_paid_count": "integer|null",
        "reach_paid_count": "integer|null"
      },
      "external_id": "string",
      "title": "string|null",
      "format": "string (VIDEO|TEXT|IMAGE|OTHER)",
      "type": "string (VIDEO|TWEET|POST|REEL|SHORT|STORY)",
      "url": "URL string",
      "media_url": "URL string|null",
      "description": "string|null",
      "visibility": "string (PUBLIC|PRIVATE)",
      "thumbnail_url": "URL string|null",
      "published_at": "ISO 8601 timestamp",
      "platform_profile_id": "string|null",
      "platform_profile_name": "string|null",
      "sponsored": "boolean|null",
      "collaboration": "boolean|null"
    }
  ],
  "metadata": {
    "offset": 0,
    "limit": 10,
    "from_date": "string|null",
    "to_date": "string|null"
  }
}
```

### 2.4 Audience Demographics

**Endpoint:** Audience APIs (under IDENTITY.AUDIENCE product)

**Data returned:**
- Country distribution (percentages)
- City distribution
- Age group distribution (e.g., "18-24": "30%", "25-34": "45%")
- Gender distribution
- Languages
- Interests / brand affinity
- Ethnicities (platform-dependent)
- Notable followers / likers
- Credibility score
- Audience overlap analysis
- Lookalike audiences

**Data freshness:** Refreshed once every **7 days** after initial account connection.

**Webhook events for audience data:**
- `PROFILES_AUDIENCE.ADDED` - first scan complete
- `PROFILES_AUDIENCE.UPDATED` - periodic refresh
```json
{
  "event": "PROFILES_AUDIENCE.UPDATED",
  "data": {
    "account_id": "UUID",
    "user_id": "UUID",
    "profile_id": "UUID",
    "last_updated_time": "ISO 8601"
  }
}
```

### 2.5 Other Notable Endpoints

- `GET /v1/work-platforms` - List supported platforms
- `POST /v1/sdk-token` - Generate SDK token for Connect flow
- Brand Safety API - GARM-standard content violation detection
- Sentiment Analysis API - Comment classification (positive/negative/neutral)
- Publishing API - Post content to Instagram, YouTube, TikTok

---

## 3. Data Freshness

### InsightIQ-specific
| Data Type | Refresh Frequency | Source |
|-----------|-------------------|--------|
| Audience demographics | Every 7 days (after account connection) | Official docs |
| Creator discovery index | Not publicly documented; likely weekly-biweekly based on industry norms | Inferred |
| Instagram Stories | 3-4 daily refreshes, 100% coverage | Marketing comparison page |
| Content items tracked | 80M+ items, continuous tracking | Marketing page |
| Public profile analytics | On-demand (fetched at request time using username/link) | Product docs |

### Industry Comparisons
| Provider | Index Size | Update Frequency |
|----------|-----------|-----------------|
| InsightIQ | 450M+ profiles | Not public; Stories 3-4x daily |
| Modash | 350M+ profiles | "Regular schedule"; Raw API for real-time |
| Influencers.club | Not stated | Full DB bi-weekly; real-time on-demand lookups |
| CreatorIQ | Not public | Weekly to bi-weekly (community consensus) |
| HypeAuditor | Not public | Weekly to bi-weekly (community consensus) |

---

## 4. Rate Limits

### InsightIQ
- **Specific rate limit numbers are NOT publicly documented.**
- The API uses standard HTTP rate limiting patterns (429 status code expected).
- The Phyllo docs reference "Respecting rate limits" as a guide topic.
- Given they handle 12M API calls/month, limits are likely in the range of 60-120 requests/minute for standard tiers.

### Comparable Platforms
| Platform | Rate Limit | Source |
|----------|-----------|--------|
| Modash | Credit-based (Discovery); request-based (Raw) | Modash docs |
| Phyllo (legacy) | Undocumented publicly; "respect rate limits" guide exists | Phyllo docs |

**Recommendation:** Implement exponential backoff with jitter. Start conservative (30 req/min), increase based on observed 429 responses.

---

## 5. Pricing Model

### InsightIQ Platform Pricing (SaaS Dashboard)
| Plan | Monthly | Annual (per month) | Search Results/mo | Profile Exports/mo | Analytics Reports/mo |
|------|---------|-------------------|-------------------|-------------------|---------------------|
| Starter | $199 | $83 | 3,000 | 200 | 50 |
| Performance | $299 | $150 | 7,500 | 500 | 100 |
| Growth | $899 | $599 | 37,500 | 2,500 | 500 |
| Enterprise | Custom | Custom | Custom | Custom | Custom |

**Key observations:**
- **API access is Enterprise-only** (not available on Starter/Performance/Growth)
- Pricing is quota-based (search results, exports, reports), NOT per-credit
- In-depth analytics reports are the most expensive action (50-500/month depending on tier)
- Free trial available (no credit card required)

### Cost Comparison with Competitors
| Platform | Annual Cost | Model |
|----------|-----------|-------|
| InsightIQ | $996-$7,188/yr (SaaS); custom (API) | Quota-based |
| Modash Discovery API | ~$16,200/yr (3,000 credits/mo) | Credit-based (0.01 credits per search result) |
| CreatorIQ | ~$30,000-$36,000/yr | Enterprise subscription |
| Upfluence | ~$5,736/yr minimum | Subscription |
| HypeAuditor | Custom (enterprise) | Custom |

---

## 6. Pagination

### InsightIQ Pattern: Offset-Based
```
GET /v1/publications/contents?account_id=XXX&limit=10&offset=0
```

**Response metadata:**
```json
{
  "metadata": {
    "offset": 0,
    "limit": 10,
    "from_date": null,
    "to_date": null
  }
}
```

**Implementation notes:**
- Default `limit`: 10
- Default `offset`: 0
- No cursor-based pagination observed in documentation
- No `has_more` or `next_cursor` field documented (must infer from result count < limit)
- Date range filtering (`from_date`/`to_date`) available on content endpoints

**Recommendation for client code:**
```python
def fetch_all(endpoint, params, limit=50):
    offset = 0
    all_results = []
    while True:
        params["limit"] = limit
        params["offset"] = offset
        resp = client.get(endpoint, params=params)
        data = resp.json()
        items = data.get("data") or data.get("creators") or []
        all_results.extend(items)
        if len(items) < limit:
            break
        offset += limit
    return all_results
```

---

## 7. Caching Best Practices for Creator Discovery APIs

### 7.1 Recommended TTL by Data Type

| Data Type | Recommended TTL | Rationale |
|-----------|----------------|-----------|
| Search results (full response) | 1-4 hours | Ranking may shift; new creators added |
| Creator profile (basic: name, bio, avatar) | 24 hours | Changes rarely |
| Follower count | 6-12 hours | Changes daily but small delta |
| Engagement rate | 24-48 hours | Computed over rolling window; relatively stable |
| Audience demographics | 7 days | InsightIQ refreshes every 7 days |
| Content/posts list | 4-12 hours | New content published daily |
| Content engagement metrics | 2-4 hours | Likes/views change rapidly for recent posts |
| Contact information | 7 days | Rarely changes |
| Analytics reports (in-depth) | 24-48 hours | Expensive to generate; data is point-in-time |

### 7.2 Entity-Level vs Response-Level Caching

**Recommendation: Hybrid approach (entity-level primary, response-level secondary)**

#### Response-Level Cache (Full JSON Blob)
```
Key: insightiq:search:<hash(query_params)>
TTL: 1-4 hours
```
**Pros:**
- Single cache lookup per request
- Perfect for identical repeated searches
- Simple implementation

**Cons:**
- Any underlying entity change invalidates entire response
- Poor reuse across different queries that return overlapping creators
- Wastes storage (same creator appears in many search results)

#### Entity-Level Cache (Individual Creator Records)
```
Key: creator:<platform>:<creator_id>
TTL: 24 hours (profile), 12 hours (metrics)
```
**Pros:**
- Granular invalidation (update one creator without flushing all searches)
- High reuse (creator appears in search results, profile views, comparison reports)
- Efficient storage (each creator stored once)
- Natural fit for historical snapshot tracking

**Cons:**
- Must assemble search response from multiple cache lookups
- More complex implementation
- Cache miss on one entity delays entire response

#### Recommended Hybrid Pattern
```
Layer 1 (hot): Response cache for search results
  - Key: search:<sha256(normalized_query)>
  - TTL: 1-2 hours
  - Serves identical repeated queries instantly

Layer 2 (warm): Entity cache for individual creators
  - Key: creator:<platform>:<id>
  - TTL: 24 hours (profile data), 12 hours (engagement metrics)
  - Populated on every search response
  - Used to serve profile detail pages without API call

Layer 3 (cold): Database for historical snapshots
  - Persisted entity data with timestamp
  - Enables trend analysis (follower growth, engagement over time)
  - Never expires; append-only
```

### 7.3 How Competitors Handle Data Freshness vs Cost

| Platform | Strategy | Details |
|----------|----------|---------|
| **Modash** | Dual API (Discovery + Raw) | Discovery = pre-analyzed, regularly refreshed snapshots. Raw = real-time, costs more. Caching baked into product design. |
| **Influencers.club** | Bi-weekly full refresh + streaming | Full DB updated every 2 weeks. On-demand lookups streamed in real-time. |
| **CreatorIQ** | Weekly-biweekly refresh | Enterprise focus; data freshness less critical than depth. |
| **InsightIQ** | Index + on-demand analytics | Discovery search hits pre-indexed data. Analytics reports fetched on-demand per profile. |

**Key insight:** ALL platforms use pre-indexed/cached data for discovery search. Real-time data is reserved for single-profile deep dives and costs significantly more.

### 7.4 Cache Invalidation Strategies

**1. TTL-Based (Primary)**
- Set appropriate TTLs per data type (see table above)
- Simplest to implement; covers 90% of use cases
- Accept brief staleness windows

**2. Event-Driven (For connected accounts)**
- InsightIQ provides webhooks: `PROFILES_AUDIENCE.ADDED`, `PROFILES_AUDIENCE.UPDATED`
- On webhook receipt, invalidate cached audience data for that profile
- Does NOT cover discovery/search data (only connected accounts)

**3. Lazy Refresh (Background)**
- For high-value profiles (e.g., creators in active campaigns)
- Background job refreshes cache before TTL expires
- Prevents cache miss latency for critical data

**4. User-Triggered Refresh**
- Allow users to "refresh" a creator profile on demand
- Counts as an API call; gate behind rate limiting
- Good UX for time-sensitive campaign decisions

### 7.5 Implementation Recommendations for a SaaS Platform

```
Architecture:
  Redis (Layer 1+2) --> PostgreSQL (Layer 3)

Redis Keys:
  insightiq:search:{query_hash}     -> full search response JSON (TTL: 2h)
  insightiq:creator:{platform}:{id} -> creator profile JSON (TTL: 24h)
  insightiq:analytics:{platform}:{id} -> analytics data (TTL: 24h)
  insightiq:audience:{profile_id}   -> audience demographics (TTL: 7d)
  insightiq:content:{account_id}    -> content list (TTL: 6h)

PostgreSQL Tables:
  creator_snapshots (id, platform, creator_id, data JSONB, fetched_at)
    -- append-only, one row per fetch
    -- enables: follower growth charts, engagement trend analysis
    -- partition by fetched_at month for query performance

Cost Optimization:
  1. Cache search results aggressively (cheapest TTL: 2h)
  2. Analytics reports are quota-limited; cache for 24-48h minimum
  3. Audience data only refreshes weekly server-side; cache for 7 days
  4. Use PostgreSQL snapshots to avoid re-fetching for trend analysis
  5. Track API quota usage: GET /account or equivalent health endpoint

Monitoring:
  - Cache hit ratio target: >80%
  - Track: API calls/day vs cached serves/day
  - Alert on: quota approaching limit (>80% consumed)
  - Log: cache miss reasons (expired vs evicted vs first-access)
```

---

## 8. Data Retention for Historical Trend Analysis

### Snapshot Strategy
```sql
CREATE TABLE creator_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL,          -- 'instagram', 'youtube', 'tiktok'
    creator_external_id TEXT NOT NULL,
    follower_count BIGINT,
    engagement_rate NUMERIC(8,5),
    average_views BIGINT,
    average_likes BIGINT,
    data JSONB NOT NULL,             -- full response for future-proofing
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (fetched_at);

-- One partition per month
CREATE TABLE creator_snapshots_2026_03
    PARTITION OF creator_snapshots
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- Index for time-series queries
CREATE INDEX idx_snapshots_creator_time
    ON creator_snapshots (platform, creator_external_id, fetched_at DESC);
```

### Snapshot Frequency
- Active campaign creators: daily snapshot
- Shortlisted creators: weekly snapshot
- General discovery results: snapshot on first fetch, then on user revisit
- Audience demographics: weekly (matches InsightIQ's 7-day refresh)

### Storage Estimation
- ~2KB per creator snapshot (compressed JSONB)
- 10,000 creators x daily snapshots x 30 days = ~600MB/month
- 10,000 creators x weekly snapshots x 12 months = ~120MB/year
- Very manageable; partition pruning keeps queries fast

---

## 9. Key Gotchas and Warnings

1. **API access requires Enterprise plan.** Starter/Performance/Growth plans only provide dashboard access. Budget for custom pricing negotiations.

2. **Null values are pervasive.** Many engagement fields return `null` depending on platform (e.g., `dislike_count` is null for non-YouTube, `watch_time_in_hours` is null for non-video). Always use defensive access: `.get("field")` with fallback, never assume field presence.

3. **work_platform is an object, not a string.** Contains `{id, name, logo_url}`. Don't compare by name string; use the UUID `id` for reliable platform identification.

4. **Pagination has no explicit `has_more`.** You must infer end-of-results when `len(results) < limit`. Always implement this guard to avoid infinite loops.

5. **Audience APIs require account connection.** Unlike discovery/search (which works on public data), audience demographics require the creator to connect their account via the Connect SDK. This is a fundamentally different data access model.

6. **InsightIQ is Phyllo rebranded.** Some documentation, SDKs, and community references still use "Phyllo" naming. The underlying API patterns are shared. Legacy Phyllo docs at `docs.getphyllo.com` may contain additional detail.

7. **Discovery search data is pre-indexed snapshots.** You are NOT getting real-time data from search endpoints. The data could be hours to days old. For real-time data, you need the profile analytics endpoint (which costs a report quota unit).

8. **Server-side only.** Never expose InsightIQ credentials to the frontend. All calls must originate from your backend.

---

## Sources

### Official InsightIQ Documentation
- [InsightIQ Developer Docs (Home)](https://docs.insightiq.ai/)
- [Getting Started with InsightIQ APIs](https://docs.insightiq.ai/docs/api-reference/introduction/getting-started-with-insightiq-APIs)
- [API References](https://docs.insightiq.ai/docs/api-reference/api/ref)
- [Creator Discovery FAQ](https://docs.insightiq.ai/docs/api-reference/FAQs/products/discovery)
- [Profile Analytics Endpoint](https://docs.insightiq.ai/docs/api-reference/api/ref/operations/create-a-v-1-social-creator-profile-analytics)
- [Content Fetch Endpoint](https://docs.insightiq.ai/docs/api-reference/api/ref/operations/create-a-v-1-social-creator-content-fetch)
- [Webhook Events](https://docs.insightiq.ai/docs/api-reference/API/webhook-events)
- [Enterprise Data Platform](https://docs.insightiq.ai/docs/api-reference/API/enterprise-data-platform)

### InsightIQ Marketing / Product
- [InsightIQ Pricing](https://www.insightiq.ai/pricing)
- [Social Data APIs Use Cases](https://www.insightiq.ai/use-cases/social-data)
- [Influencer Database Blog](https://www.insightiq.ai/blog/influencer-database)
- [InsightIQ vs Modash Comparison](https://www.insightiq.ai/compare/modash-alternative)

### Competitor / Industry References
- [Modash API Best Practices](https://help.modash.io/en/articles/10870210-modash-api-best-practices-for-developers)
- [Modash Discovery API](https://www.modash.io/influencer-marketing-api/discovery)
- [Modash API Docs](https://docs.modash.io/)
- [Best Influencer Marketing APIs 2026 (Influencers.club)](https://influencers.club/blog/influencer-marketing-apis/)
- [Phyllo API Alternatives (Modash blog)](https://www.modash.io/blog/phyllo-api-alternatives)
- [Phyllo Rate Limits Guide](https://docs.getphyllo.com/docs/api-reference/guides/respecting-rate-limits)

### Caching Best Practices
- [Redis Cache Optimization Strategies Guide](https://redis.io/blog/guide-to-cache-optimization-strategies/)
- [Influencer Platform API Integration Guide (InfluenceFlow)](https://influenceflow.io/resources/campaign-management-api-integration-complete-guide-for-developers-agencies-in-2026/)
