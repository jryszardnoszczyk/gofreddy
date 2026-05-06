#!/usr/bin/env bash
# fetch_api.sh — single source of truth for ~75 free public API calls.
#
# Master plan §4.6. Invoked by Stage 1b Sonnet pre-discovery and by Stage 2
# agents through `Bash cli/scripts/fetch_api.sh <url> [extra-curl-args...]`.
#
# Behavior:
#   - Exponential backoff: 3 retries at 2s / 4s / 8s on transient failures
#     (HTTP 5xx, 429, network errors).
#   - Auth header injection from env vars based on URL host.
#   - Mandatory User-Agent: GoFreddy-Audit/1.0 (contact: jryszardn@gmail.com)
#   - Pagination follow: --paginate flag walks RFC 5988 Link headers
#     (GitHub-style next links) up to a max page count.
#   - Per-host pacing: configurable sleep between successive requests to the
#     same host within a single audit (default 100ms, raised for SEC EDGAR
#     and crt.sh per their published guidance).
#   - JSON output to stdout. Errors to stderr with HTTP status + URL.
#
# Usage:
#   fetch_api.sh <url>
#   fetch_api.sh --paginate <url>
#   fetch_api.sh --max-pages 5 <url>
#   fetch_api.sh --pace-ms 1000 <url>
#   fetch_api.sh -- <url> [raw curl args...]
#
# Exit codes:
#   0  success
#   1  generic / curl error
#   2  HTTP 4xx after exhausted retries (don't retry — payload returned anyway)
#   3  HTTP 5xx / 429 after exhausted retries
#   4  bad usage

set -euo pipefail

USER_AGENT="GoFreddy-Audit/1.0 (contact: jryszardn@gmail.com)"
MAX_RETRIES=3
PAGINATE=false
MAX_PAGES=10
PACE_MS=100

usage() {
    cat <<EOF >&2
Usage: $0 [options] <url> [-- raw-curl-args...]

Options:
  --paginate         Follow RFC 5988 Link rel="next" header up to --max-pages
  --max-pages N      Cap on pagination follow (default 10)
  --pace-ms MS       Inter-request sleep ms (default 100)
  --max-retries N    Retry budget for transient failures (default 3)
  -h, --help         Show this help

Auth env vars (auto-injected by host):
  api.github.com               → \$GITHUB_TOKEN
  api.producthunt.com          → \$PRODUCTHUNT_TOKEN
  reddit.com / oauth.reddit.com → \$REDDIT_BEARER
  data.sec.gov                 → User-Agent contact (already set)
  api.brave.com                → \$BRAVE_API_KEY (X-Subscription-Token header)
  serpapi.com                  → \$SERPAPI_KEY (api_key query param)
EOF
}

if [[ $# -eq 0 ]]; then usage; exit 4; fi

EXTRA_CURL_ARGS=()
URL=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        --paginate) PAGINATE=true; shift ;;
        --max-pages) MAX_PAGES="$2"; shift 2 ;;
        --pace-ms) PACE_MS="$2"; shift 2 ;;
        --max-retries) MAX_RETRIES="$2"; shift 2 ;;
        --) shift; EXTRA_CURL_ARGS=("$@"); break ;;
        -*) echo "fetch_api.sh: unknown option: $1" >&2; usage; exit 4 ;;
        *)
            if [[ -z "$URL" ]]; then URL="$1"; shift
            else EXTRA_CURL_ARGS+=("$1"); shift; fi ;;
    esac
done

if [[ -z "$URL" ]]; then echo "fetch_api.sh: missing URL" >&2; usage; exit 4; fi

# --- per-host overrides + auth injection ---------------------------------

inject_auth() {
    local url="$1"
    local -n out_headers=$2  # nameref to caller's array
    local host
    host=$(printf '%s\n' "$url" | sed -E 's#^https?://([^/]+).*#\1#' | tr 'A-Z' 'a-z')

    case "$host" in
        api.github.com|api.github.io)
            [[ -n "${GITHUB_TOKEN:-}" ]] && out_headers+=("-H" "Authorization: Bearer ${GITHUB_TOKEN}")
            out_headers+=("-H" "Accept: application/vnd.github+json")
            out_headers+=("-H" "X-GitHub-Api-Version: 2022-11-28")
            ;;
        api.producthunt.com)
            [[ -n "${PRODUCTHUNT_TOKEN:-}" ]] && out_headers+=("-H" "Authorization: Bearer ${PRODUCTHUNT_TOKEN}")
            ;;
        oauth.reddit.com|www.reddit.com|reddit.com)
            [[ -n "${REDDIT_BEARER:-}" ]] && out_headers+=("-H" "Authorization: Bearer ${REDDIT_BEARER}")
            ;;
        data.sec.gov|www.sec.gov)
            # SEC requires identifiable contact in UA — already set via USER_AGENT.
            : ;;
        api.search.brave.com)
            [[ -n "${BRAVE_API_KEY:-}" ]] && out_headers+=("-H" "X-Subscription-Token: ${BRAVE_API_KEY}")
            out_headers+=("-H" "Accept: application/json")
            ;;
        api.huggingface.co|huggingface.co)
            [[ -n "${HUGGINGFACE_TOKEN:-}" ]] && out_headers+=("-H" "Authorization: Bearer ${HUGGINGFACE_TOKEN}")
            ;;
        api.mailinator.com)
            [[ -n "${MAILINATOR_API_TOKEN:-}" ]] && out_headers+=("-H" "Authorization: Bearer ${MAILINATOR_API_TOKEN}")
            ;;
    esac
}

per_host_pace() {
    # SEC EDGAR: 10/sec hard limit → 100ms is fine, but be polite.
    # crt.sh: ~1/sec advised.
    local url="$1"
    local host
    host=$(printf '%s\n' "$url" | sed -E 's#^https?://([^/]+).*#\1#' | tr 'A-Z' 'a-z')
    case "$host" in
        crt.sh) printf '%s\n' "1000" ;;
        data.sec.gov) printf '%s\n' "120" ;;
        *) printf '%s\n' "$PACE_MS" ;;
    esac
}

# --- single-request curl with retry --------------------------------------
# Sets shell globals BODY_FILE + HEADERS_FILE; returns 0 on 2xx, 2 on
# non-retriable 4xx (with body still written), 3 on exhausted-retry 5xx/429.

fetch_once() {
    local url="$1"
    local headers=()
    inject_auth "$url" headers

    local pace
    pace=$(per_host_pace "$url")
    sleep "$(awk -v ms="$pace" 'BEGIN{printf "%.3f", ms/1000}')"

    BODY_FILE=$(mktemp)
    HEADERS_FILE=$(mktemp)

    local attempt=0
    while [[ $attempt -lt $MAX_RETRIES ]]; do
        attempt=$((attempt + 1))
        : > "$BODY_FILE"
        : > "$HEADERS_FILE"
        local http_status
        http_status=$(curl --silent --show-error --location \
            --user-agent "$USER_AGENT" \
            --max-time 30 \
            --connect-timeout 10 \
            --dump-header "$HEADERS_FILE" \
            --output "$BODY_FILE" \
            --write-out '%{http_code}' \
            "${headers[@]}" \
            ${EXTRA_CURL_ARGS[@]:+"${EXTRA_CURL_ARGS[@]}"} \
            "$url" 2>/dev/null) || http_status="000"

        if [[ "$http_status" =~ ^2 ]]; then
            return 0
        fi
        # Don't retry 4xx (except 429 — rate-limited).
        if [[ "$http_status" =~ ^4 && "$http_status" != "429" ]]; then
            echo "fetch_api.sh: HTTP $http_status (no retry) for $url" >&2
            return 2
        fi
        # Transient — exponential backoff: 2s, 4s, 8s.
        local sleep_s=$((2 ** attempt))
        echo "fetch_api.sh: HTTP $http_status (attempt $attempt/$MAX_RETRIES), sleeping ${sleep_s}s..." >&2
        sleep "$sleep_s"
    done

    echo "fetch_api.sh: exhausted $MAX_RETRIES retries for $url" >&2
    return 3
}

# --- pagination (RFC 5988 Link rel="next") -------------------------------

extract_next_link() {
    # Parse "Link: <url1>; rel=\"next\", <url2>; rel=\"last\"" → url1.
    # Reads from stdin.
    awk -F',' '
        /^[Ll]ink:/ {
            for (i=1; i<=NF; i++) {
                if ($i ~ /rel="next"/) {
                    if (match($i, /<[^>]+>/)) {
                        print substr($i, RSTART+1, RLENGTH-2)
                        exit
                    }
                }
            }
        }
    '
}

main() {
    local current_url="$URL"
    local pages=0
    local rc=0

    while [[ $pages -lt $MAX_PAGES ]]; do
        pages=$((pages + 1))
        rc=0
        fetch_once "$current_url" || rc=$?
        if [[ $rc -ne 0 ]]; then
            cat "$BODY_FILE" 2>/dev/null || true
            rm -f "$BODY_FILE" "$HEADERS_FILE"
            return $rc
        fi
        cat "$BODY_FILE"
        local next_url=""
        if [[ "$PAGINATE" == "true" ]]; then
            next_url=$(extract_next_link < "$HEADERS_FILE")
        fi
        rm -f "$BODY_FILE" "$HEADERS_FILE"
        if [[ "$PAGINATE" != "true" || -z "$next_url" ]]; then
            return 0
        fi
        current_url="$next_url"
    done
    return 0
}

main
exit $?
