---
phases:
  1: [A1, A2, B1, B2, B3, B4, C1]
  2: [A3, A4, A5, A6, B5, B6, B7, C2, C3]
  3: [A7, A8, A9, A10, B8, B9, B10]
tracks:
  a: [A1, A2, A3, A4, A5, A6, A7, A8, A9, A10]
  b: [B1, B2, B3, B4, B5, B6, B7, B8, B9, B10]
  c: [C1, C2, C3]
flow4: [A9, A10, B9, B10]
---

# GoFreddy QA Harness Test Matrix

## Track A — CLI Domain

### Flow 1 (Fixed — convergence reference)

| # | Command | Pass Criteria |
|---|---------|---------------|
| A1 | `freddy client new --name "Harness QA" --slug harness-qa` | Exit 0. JSON with id, slug, name. |

### Flow 4 (Dynamic — excluded from convergence)

| # | Command | Pass Criteria |
|---|---------|---------------|
| A9 | `freddy scrape --url https://example.com` | Exit 0. Content output. |
| A10 | `freddy search_content --query "trends"` | Exit 0 or BLOCKED. |

## Track B — API Domain

### Flow 1 (Fixed — convergence reference)

| # | Method + Endpoint | Pass Criteria |
|---|-------------------|---------------|
| B1 | `POST /v1/sessions` | HTTP 201. JSON with id, status. |

### Flow 4 (Dynamic — excluded from convergence)

| # | Method + Endpoint | Pass Criteria |
|---|-------------------|---------------|
| B9 | `POST /v1/geo/audit` | HTTP 200 or BLOCKED. |
| B10 | `POST /v1/competitive/ads/search` | HTTP 200 or BLOCKED. |

## Track C — Frontend Domain

| # | Action | Route | Pass Criteria |
|---|--------|-------|---------------|
| C1 | Navigate to login | `/login` | Page renders. |
