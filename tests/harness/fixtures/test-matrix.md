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

## Track A — Analysis Domain

### Flow 1 (Fixed — convergence reference)

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| A1 | "Search for fitness videos" | `search` | `search` | 60s | Results render. |

### Flow 4 (Dynamic — excluded from convergence)

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| A9 | "Search for YouTube tech review videos" | `search` | `search` | 60s | Results. |
| A10 | "Analyze the most interesting one" | `analyze_video` | `analysis` | 120s | Analysis. |
| A11 | "Deep content analysis" | `analyze_content` | `content_analysis` | 90s | Analysis. |

## Track B — Operations Domain

### Flow 1 (Fixed — convergence reference)

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| B1 | "Create a monitor" | `create_monitor` | `monitor` | 60s | Monitor renders. |

### Flow 4 (Dynamic — excluded from convergence)

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| B12 | "Show my account dashboard" | `account_analytics` | `account_dashboard` | 60s | Dashboard. |
| B13 | "Show the media library" | `manage_media` | `media_library` | 60s | Library. |

## Track C — Creative Domain

### Flow 1 (Fixed — convergence reference)

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| C1 | "Create a creative brief" | `generate_content` | `brief` | 90s | Brief renders. |

### Flow 4 (Dynamic — excluded from convergence)

| # | Prompt | Expected Tool | Expected Section | Timeout | Pass Criteria |
|---|--------|--------------|-----------------|---------|---------------|
| C8 | "What can you do?" | Agent responds | Text response | 60s | Capability overview. |
| C9 | "Search + fraud check" | `search` then `detect_fraud` | `search` then `fraud` | 120s | Multi-tool. |
