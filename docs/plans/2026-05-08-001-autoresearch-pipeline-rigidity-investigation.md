# Autoresearch pipeline rigidity investigation

**Date:** 2026-05-08
**Scope:** Why the v009 GEO evolution run on 2026-05-07 routed every fixture's agent around 9+ tool failures.
**Evidence base:** `autoresearch/archive/v009/sessions/geo/{nubank,mayoclinic,semrush}/` (results.jsonl, findings.md, session_summary.json, logs/iteration_*.log.err); `autoresearch/archive/v009/programs/`; `autoresearch/archive/v009/scripts/`; `autoresearch/archive/v009/workflows/`; `cli/freddy/`; `autoresearch/harness/prompt_builder_entrypoint.py`; `judges/evolution/agents/variant_scorer.py`; `autoresearch/evaluate_variant.py`.
**Method:** Four parallel investigation streams (CLI bugs, allowlist, prompt/gate alignment, scorer health), then synthesis.

---

## TL;DR

Five hypotheses, four-stream investigation. Headline findings:

| H | Claim | Verdict | Action shape |
|---|---|---|---|
| **H1** | Pipeline forces agent into freddy-CLI workflow even though it's capable as a general investigator | **partially true** | Fix sandbox + cache layer first; the prompt is already permissive |
| **H2** | Structural gate ([INTRO]/[FAQ]) runs after the fact, contract not in the prompt | **true** | Trivial autogen-block fix; one-line per gate item |
| **H3** | `prompt_builder_entrypoint` allowlist is overzealous | **partially true (already patched tactically)** | Tactical fix landed `c120815`; structural fix still pending |
| **H4** | Scoring code can't tell degraded sessions from clean ones | **true** | Three places drop the signal — log first, gate later |
| **H5** | Anti-fabrication discipline is prompt-only, mutable by a meta-agent | **true** | GEO lane has zero structural fabrication checks; competitive lane already shows the pattern |

The same architectural shape underlies H2 and H5: **the prompt is the spec, the validator is downstream of the prompt, and the two are not co-generated.** A meta-agent can mutate either side without test failure.

The same operational shape underlies H1 and the three CLI bugs: **the codex sandbox blocks loopback (no `network_access = true`), the fixture cache key for visibility omits keywords, and the sitemap command added a DNS-resolve SSRF guard that fails-closed offline.** Three independent code paths, one sandbox config knob, one cache-key bug, one error-handling regression — none of which the prompt's "fall back to curl" line can rescue, because curl itself is blocked.

The **three immediate bug fixes** (§3) and the **operator quick wins** (§5.1) are sufficient to make a re-run of v009 produce clean signal. The architectural changes in §4 are about preventing the same shape from recurring.

---

## 1. Context

The autoresearch system runs evolution loops where a Codex CLI agent (gpt-5.5) drives multi-phase sessions per fixture. On 2026-05-07 a v009 evolution run executed three GEO fixtures (mayoclinic, nubank, semrush). All three sessions completed and produced kept artifacts. Forensic review of the run logs surfaced 9+ distinct tool failures *per fixture*, with the same failure patterns repeating across all three. The agent adapted gracefully each time — but spent most of its iteration budget routing around broken tooling rather than improving the deliverable.

The user's research brief asks five hypotheses about whether the architecture is forcing the agent into rigid workflows when it should treat it as a general-purpose investigator with optional shortcuts.

This report is structured:

- §2 — verdicts on H1–H5 with file:line citations and quoted evidence.
- §3 — root causes and proposed minimal fixes for the three concrete bugs.
- §4 — architectural recommendation (the shape, not a sketch of code).
- §5 — operator quick wins (this week) vs. deeper changes (separate plan).
- §6 — file:line evidence index for fast cross-reference.

Throughout: where a sub-investigation produced a longer treatment, I cite back to the report under `.tmp/investigation-*.md` so the deeper material is preserved.

---

## 2. Hypothesis verdicts

### H1 — "Pipeline treats agent as workflow-runner; should treat it as general investigator"

**Verdict: PARTIALLY TRUE.**

The prompt itself is unusually permissive. `autoresearch/archive/v009/programs/geo-session.md:5` opens with:

> "Work however you'd naturally work: scrape pages, analyze competitors, audit infrastructure, optimize content, iterate on quality, compile findings. **There is no turn budget. There is no prescribed workflow. There are no retry caps. Use whatever tools and approach you need.**"

And the Tool Call Resilience section at line 192-195 explicitly authorizes general-purpose fallbacks:

> "**`freddy` transient failure**... Retry once, then fall back to `curl -sL` for sitemap/page fetches and persist a minimal cached page JSON. If `freddy visibility` keeps failing, switch to `CQ-DATA` qualitative-positioning mode rather than fabricating citation counts."

So at the *prompt* layer, freddy commands are already framed as shortcuts with declared fallbacks. The agent is invited to be general.

But the *operational* layer makes those fallbacks fail in three independent ways:

1. **Sandbox network policy.** `~/.codex/config.toml` has no `[sandbox_workspace_write] network_access = true`. Apple Seatbelt blocks all outbound sockets, including loopback (127.0.0.1:8000 — the local Freddy backend the prompt directs the agent to use). When the agent fell back to `curl -sL https://nubank.com.br/sitemap.xml` per the prompt's instructions, curl exited with `Could not resolve host` because DNS UDP/53 is also blocked. The agent dutifully fell from "use freddy" to "use curl" to "qualitative mode" — but the only one of those that worked was the last, and even that depended on cached fixture data smuggled in earlier (`investigation-freddy-cli-bugs.md` §Bug 3).

2. **Cache layer is keyed to the freddy command shape, not the agent's intent.** When the agent tried `freddy visibility --keywords "<8 keywords>" --brand nubank --country BR`, the cache lookup matched on `sha1("nubank")[:12]` only and silently served the brand-only fixture (`cli/freddy/commands/visibility.py:25-28`; full trace under §3.2 below). The fall-back path the agent expected — "if visibility fails, qualitative mode" — never fired because visibility *appeared* to succeed with stale data. A general investigator using curl would have hit the live API or hit DNS-blocked failure, both of which produce clearer signal than a silent cache hit on the wrong shape.

3. **Cached artifacts are pre-positioned only for the freddy command shape.** The `~/.local/share/gofreddy/fixture-cache/search-v1/geo-nubank-br-conta/v1.0/` directory contains pre-primed `freddy-scrape_page_*.json` and `freddy-visibility_*.json` files keyed by the freddy command — there is no equivalent corpus indexed by URL or keyword for a curl-first agent to pull from. The first fixture step succeeded (`logs/iteration_001.log.err:514-516` — `freddy scrape https://nubank.com.br/conta/`) only because that exact freddy invocation had a cache entry. A general investigator without the freddy mediation would face the same DNS-blocked curl and have nothing to fall through to.

So the verdict is partially true. The prompt is general-purpose but the operations stack is freddy-shaped. The agent gets the worst of both worlds: prompted to be general, sandboxed to be specific.

The *structural* fix is not "make freddy optional" — the freddy CLI's value is exactly that it manages cache + retry + provider selection on top of paid AI engine APIs (Cloro, DataForSEO, PageSpeed) the agent should not be calling directly. The fix is to make sure the operations stack matches the prompt's stated permissiveness:

- Enable `network_access = true` in the codex sandbox so the prompt-level "curl fallback" actually works (§5.1).
- Make freddy errors legible enough that the agent's branching on `connection_error` vs `invalid_url` vs `sandbox_network_blocked` actually reflects reality (§3 bugs).
- Pre-position cached fixtures under URL-keyed fallbacks so a curl-first agent can match the same data the freddy-first agent gets.

§4 develops the full architecture.

### H2 — "Structural gate runs too late; contract is not in the prompt"

**Verdict: TRUE.**

`autoresearch/archive/v009/workflows/session_eval_geo.py:80-89` enforces:

```python
if "[FAQ]" not in text and "## FAQ" not in text.upper() and "## Frequently Asked" not in text:
    failures.append("No FAQ block found. FIX: add a [FAQ] block with 5-7 self-contained Q&A pairs. ...")
if "[INTRO]" not in text:
    failures.append("No [INTRO] block found. FIX: add an [INTRO] block with a 40-60 word answer-first opening ...")
```

The literal `[INTRO]` requirement has **no fallback** (no `## Intro`, no `## Introduction`, nothing else). The `[FAQ]` token has three accepted forms.

The prompt does not specify these markers. `grep -rn "\[INTRO\]\|\[FAQ\]" autoresearch/archive/v009/programs/` returns zero hits. The closest the prompt gets is CQ-1 ("Answer-first intro") and CQ-2 ("FAQ with 5-7 self-contained answers") — semantic prose, not bracket tokens.

Worse: the autogen STRUCTURAL block at `geo-session.md:213-218` claims to enumerate the gates and lists only 2 of 6 actual checks:

| Gate | Source of truth | Listed in autogen block? |
|---|---|---|
| Optimized file present | `session_eval_geo.py:66-68` | yes |
| JSON-LD parses | (elsewhere in the lane) | yes |
| `gap_allocation.json` exists ≥10 bytes | `session_eval_geo.py:71-77` | **no** |
| `[FAQ]` / `## FAQ` / `## Frequently Asked` | `session_eval_geo.py:80-84` | **no** |
| `[INTRO]` literal | `session_eval_geo.py:86-89` | **no** |
| ≥ 300 words | `session_eval_geo.py:91-95` | **no** |

The agent reads the autogen block as a complete enumeration, trusts it, and gets surprised by the rest of the gate.

The forensic statement is the agent's own commentary at `nubank/logs/iteration_004.log.err:2436`:

> "The evaluator rejected the artifact on structural labels, not content quality: it expects explicit `[INTRO]` and `[FAQ]` blocks. I'm adding those labels around the existing answer-first intro and FAQ without changing the evidence base."

All three v009 GEO fixtures showed the same pattern: iter-1 fails on missing `[INTRO]` (and nubank also `[FAQ]`), then attempt-2 passes after wrapping the existing prose in literal bracket tokens. The delta is **purely cosmetic** — no claim, evidence, or content changed.

This is a contract-shape mismatch. The prompt teaches semantic intent ("answer-first intro"); the validator demands an ASCII token. Both are real, both are load-bearing (the same bracket convention is also assumed by `scripts/build_geo_report.py:73-84` which counts these markers when compiling the final report) — but the agent only sees one half of the contract.

**Fix shape:** complete the autogen STRUCTURAL block with the full enumeration (concrete proposed prose in §3.4 below). The fix should land in the autogen renderer (the lane registry's structural-gate spec needs to teach itself to enumerate every literal-token check), not as a hand-edit between the AUTOGEN sentinels — the comment at `geo-session.md:212` warns hand-edits are clobbered on every variant clone. Optional tightening: drop the `## FAQ` / `## Frequently Asked` fallbacks from the gate so all markers have one accepted form, removing the trap where INTRO has one form but FAQ has three.

(Full treatment: `.tmp/investigation-prompt-vs-gate.md` Investigation 1.)

### H3 — "`prompt_builder_entrypoint` allowlist is overzealous"

**Verdict: PARTIALLY TRUE — already patched tactically. Structural fix still pending.**

The exact bug v009 hit was diagnosed and patched on 2026-05-07 in commit `c120815` (~4 hours after the v009 archive logs were written). That commit added `urllib` and `ipaddress` to `_ALLOWED_PREFIXES` in `autoresearch/harness/prompt_builder_entrypoint.py`. All five tests in `tests/autoresearch/test_prompt_builder_isolation.py` pass on current HEAD (Python 3.13.3). v010+ runs will produce inner-critique scores correctly.

But the *design* of the allowlist is the wrong shape. From `prompt_builder_entrypoint.py:58-91`:

```python
_ALLOWED_PREFIXES: tuple[str, ...] = (
    "autoresearch",
    "json", "sys", "math", "pathlib",
    "os", "posixpath", "ntpath", "genericpath", "stat",
    # ... 80+ entries ...
    # Python 3.13's `runpy` ... transitively imports `urllib.parse`
    "urllib", "ipaddress",
)
```

The threat model (per the file's docstring at lines 1-37): a rogue package on `PYTHONPATH` (planted by a malicious variant under its own worktree) that redefines `autoresearch.harness.session_evaluator.build_critique_prompt` to return a softer prompt. Defense lives in three layers:

1. `python3 -I` (isolated mode) — drops ambient `PYTHONPATH`, user site-packages, `PYTHON*` env vars. The subprocess only sees stdlib + the explicitly injected `REPO_ROOT`. **This is the layer that does the actual security work.**
2. The 80-prefix allowlist snapshot at startup — catches modules whose names imply pollution.
3. L1 hash-check on the next evolve cycle.

Layer 1 already defeats the documented threat. Layer 2's marginal security against a `python -I`-isolated subprocess is essentially zero — but it is coupled to CPython's internal stdlib import graph, which is **not a stable API**. A point release that adds an import to `runpy`/`importlib`/`encodings` breaks the allowlist. The 80-prefix list is itself evidence of this drift: most of those entries were not added with security intent, they were added because a CPython release pulled in a new stdlib import.

The cost: when the allowlist breaks, *every* fixture's external critique fails simultaneously (9/9 in the 2026-05-07 validation per the `c120815` commit message), wasting hours of compute. The diagnostic value (loud "something unexpected in the import graph") is net-negative once you measure compute lost to false positives.

**Recommended structural fix** (proposed by the deeper investigation under `.tmp/investigation-prompt-builder-allowlist.md` §8): replace the 80-prefix allowlist with a single check that the loaded `autoresearch` package resolves to the explicitly injected `REPO_ROOT`:

```python
def _enforce_no_rogue_autoresearch() -> None:
    import autoresearch
    expected = os.environ.get("AUTORESEARCH_EXPECTED_REPO_ROOT")
    if expected and not autoresearch.__file__.startswith(expected):
        sys.stderr.write(...)
        raise SystemExit(2)
```

This is a hash-of-source check on the one package the threat model actually cares about. Stdlib drift becomes irrelevant. If keeping the allowlist is preferred (defense in depth, audit trail, etc.), at minimum add a CI test that snapshots `sys.modules` across Python 3.12/3.13/3.14 and fails if any module loaded post-bootstrap is missing — this would have caught the urllib/ipaddress drift before it shipped to a real validation run.

### H4 — "Degraded mode pattern propagates noise; scorer doesn't penalize"

**Verdict: TRUE.**

The variant scorer treats degraded sessions at parity with clean ones. Three independent code paths drop the signal before the scorer sees it:

1. `autoresearch/archive/v009/scripts/summarize_session.py:89-95` — status-bucket map omits `completed_degraded`:
   ```python
   bucket = ("productive" if s in ("complete", "completed", "kept", "done", "pass")
             else "blocked" if s == "blocked"
             else "failed" if s in ("failed", "error", "fail")
             else "skipped" if s == "skipped"
             else "uncategorized")
   ```
   The agent's `"completed_degraded"` token (used in nubank iter 3) is in **no list** and lands in `"uncategorized"`, treated as benign noise.

2. `summarize_session.py:102-107` — the error counter only reads a structured `error` field that the agent never wrote. Agents wrote failures into free-text `notes`. Result: nubank's `session_summary.json:15` shows `"errors": []` despite 9+ infrastructure failures across the iteration log.

3. `autoresearch/evaluate_variant.py:995-1062` — `_extract_inner_pass_rate`'s `_KEEP_TOKENS = {"kept","keep","pass","ok","approved","verified","complete","done"}` excludes `completed_degraded` (silently dropped) but includes `completed` (counted as a clean keep). nubank's `inner_pass_rate=1.0`, identical to a clean run.

`grep -rn "degraded\|tool_failure\|tool_health\|connection_error" judges/ autoresearch/evaluate_variant.py autoresearch/lane_runtime.py autoresearch/lane_registry.py autoresearch/evolve.py autoresearch/frontier.py --exclude-dir=archive` returns zero matches in production scoring/promotion code. The only hits in `evolve.py` refer to "silently-degraded inner-critique" — a *separate* concern about meta-agent tooling, not session degradation.

The LLM judge does see `findings.md` and `results.jsonl` as raw text in the artifacts payload (`autoresearch/evaluate_variant.py:1158-1200` ships up to 800K bytes), but the scorer prompt at `judges/evolution/prompts/scorer.md:1-36` instructs it to "Score only what is in front of you" against an 8-criterion **content-quality** rubric — no infrastructure, no tool health, no degradation. Whether the LLM penalizes the failures it can read in the artifacts is per-call non-deterministic noise.

Empirical confirmation from `autoresearch/archive/v009/sessions/geo/nubank/session_summary.json:14-22`:

```json
"iterations": {"total": 5, "productive": 4, "blocked": 0, "failed": 0, "skipped": 0, "uncategorized": 1},
"errors": [],
"status": "COMPLETE"
```

Reads like a clean session. The full failure narrative lives in `findings.md` under `## Disproved` — visible to a careful operator, invisible to the scorer.

**Fix shape:** three options, in increasing depth:

- **A (visibility-first, recommended):** compute `tool_error_rate` in `summarize_session.py` and append it to `metrics/<domain>.jsonl`. Surface in operator dashboard. No gate, no multiplier — just stop being silent. ~15 lines.
- **B (gradient-friendly):** multiply `tool_health_score = max(0.0, 1 - 2 * tool_error_rate)` into per-fixture composite scores. Variants that stop calling broken tools out-score variants that retry 9× and fall back. ~30 lines.
- **C (hard gate):** reject sessions with `tool_error_rate > 0.5` via `structural_passed=false`. Cleanest signal, lowest cost — but loses the partial-credit distinction.

Recommendation: A first (cheap, gets baseline data on what threshold separates clean from degraded), then evaluate B vs C empirically.

(Full treatment: `.tmp/investigation-scorer-degraded-inputs.md`.)

### H5 — "Anti-fabrication discipline is enforced by prompt, not by code"

**Verdict: TRUE.**

`geo-session.md` contains thorough anti-fabrication prose:

- Line 42 (CQ-DATA): "Never include specific citation counts unless from measured data with `method: 'measured'`; use qualitative positioning when data unavailable"
- Line 167-170 (Data Grounding): "findings must trace to specific source files" with Bad/Good examples
- Line 192: "If `freddy visibility` keeps failing, switch to `CQ-DATA` qualitative-positioning mode rather than fabricating citation counts."
- Line 193: "mark every numeric or competitive claim as `[FILL: needs live data]` so it's unmistakably a degraded fallback, not fabricated measured data"
- Line 195: "Log every fallback in `findings.md` under `## Disproved`"
- Line 203 (Hard Rule 5): "Never fabricate API responses"

The discipline is thoroughly described — and thoroughly prose-only.

The only structural anti-fabrication check in the v009 GEO archive is `scripts/summarize_session.py:25-33`:

```python
_BAD_SRC = ("same_runtime_", "archive_", "cached_", "fallback_", "prior_")
def _validate_session_sources(results):
    for r in results:
        src = str(r.get("source", "")).lower()
        if src.startswith(_BAD_SRC) or "_cache" in src or "_archive" in src:
            print(f"FATAL: fabricated source {src!r} ...", file=sys.stderr)
            sys.exit(1)
```

This is a **session-replay anti-fraud** check — it catches an agent that puts `"source": "cached_..."` in `results.jsonl`, i.e. copying artifacts from a prior run instead of generating fresh ones. It does NOT look at the optimized `.md` content for unsourced claims, missing citations, or invented numbers. It guards the audit trail, not the deliverable.

`scripts/build_geo_report.py:79` counts `[FILL]` markers but does not gate on them. `workflows/session_eval_geo.py` has no citation/source/`[FILL]`/`unverified` keywords anywhere.

The competitive lane has the exemplar GEO has not adopted — `workflows/session_eval_competitive.py:81-83`:

```python
citation_patterns = count_regex(text, r"(?:source:|data from|according to|per\s|via\s|\[.*?\]\(http)")
if citation_patterns < 2:
    failures.append(f"Only {citation_patterns} data source citations (need 2+)")
```

This is the only real structural citation check in the v009 archive — and it's not in GEO.

**Implication:** a meta-agent that mutates `geo-session.md` to weaken the anti-fabrication language ("verifiable" → "plausible") or to remove the CQ-DATA rule would face zero test failures. The discipline lives in plain English with no structural anchor.

**Fix shape:** three structural guarantees, in increasing depth (per `.tmp/investigation-prompt-vs-gate.md` §2.6):

- **G1 — Citation density gate (cheap, port competitive's pattern).** Add to `session_eval_geo.structural_gate`: count occurrences of citation patterns in the optimized `.md`. Failures DISCARD the artifact. Catches "wall of confident prose with no anchors" without requiring an LLM.
- **G2 — `[FILL: ...]` discipline when data was unavailable.** When `results.jsonl` shows degraded data steps (using H4's new `tool_error_rate` signal), require the optimized artifact to contain at least one `[FILL: ...]` marker. Promotes `build_geo_report.py:79`'s count into a gate.
- **G3 — Per-claim provenance manifest.** Sidecar `optimized/{slug}.claims.json` binding numeric assertions to source files. Strongest, longest to implement. A meta-agent cannot weaken anti-fabrication without breaking the manifest contract that downstream tests pin.

G1 alone would catch the easy case (page has 0 source citations) without LLM judgment, in the same code path that catches "no FAQ block".

---

## 3. Specific bugs to fix immediately

### 3.1 Bug — `freddy sitemap` rejects valid URL shapes with `invalid_url`

**Symptom.** Agent submitted `https://nubank.com.br/conta/` and the bare domain `https://nubank.com.br`. Both rejected with `{"error": {"code": "invalid_url", "message": "URL validation failed"}}`. Same shape ran through `freddy scrape` and succeeded (cache hit). The agent reasonably interpreted the asymmetry as a URL-shape contract problem and tried alternate shapes, all failing identically.

**Root cause.** `cli/freddy/commands/sitemap.py:84-91` performs a local SSRF guard via DNS resolution that no peer command does:

```python
# SSRF guard — match /v1/geo/detect and /v1/geo/scrape so the three
# URL-taking commands reject private/blackhole IPs identically and in <1s
# instead of hanging the full FETCH_TIMEOUT window per sub-fetch.
if resolve_and_validate is not None:
    try:
        asyncio.run(resolve_and_validate(url))
    except ValueError:
        emit_error("invalid_url", "URL validation failed")
```

`resolve_and_validate` (in `src/common/url_validation.py:86-91`) calls `socket.getaddrinfo(hostname, ...)`. Inside the codex `workspace-write` sandbox, `getaddrinfo` raises `socket.gaierror` because DNS is blocked. The validator catches it and re-raises as `ValueError("DNS resolution failed for ...")` — and `sitemap` unconditionally maps any `ValueError` to `invalid_url`.

This was added in PR #37 (commit `dedb25d`). Before that, sitemap deferred DNS to the backend. Peer commands `freddy scrape` and `freddy detect` (`commands/scrape.py:27-32`, `commands/detect.py:33-38`) do *not* call `resolve_and_validate` locally; they only do `urlparse` + plaintext-port check, then defer DNS to the backend. That asymmetry is why the same URL passed scrape but failed sitemap.

A secondary defect: the error code `invalid_url` conflates "malformed URL string" with "DNS unreachable". The agent has no way to tell which.

**Proposed minimal fix.**

1. **Make the local guard fail-open under DNS errors instead of fail-closed.** The intent of the guard (per its comment) is to reject *private/blackhole IPs in <1s* — not to enforce reachability. If `getaddrinfo` cannot complete (offline / sandboxed / DNS server down), the guard should let the call proceed to `SitemapParser.parse(url)`, which has its own httpx error handling. Surface a distinguishing exception class from `url_validation.py` (`DNSResolutionFailed` vs `BlockedIPRange`); catch only the latter and emit `invalid_url`.
2. **Split the error code.** Replace the single `invalid_url` envelope with `invalid_url` (URL shape rejected) vs `dns_error` (resolution failed) vs `blocked_ip` (resolved to a blocked range). The agent prompt can then teach a different recovery path for each.

**Suggested test.** Monkeypatch `resolve_and_validate` to raise `DNSResolutionFailed`; assert that `sitemap_command` does not emit `invalid_url` (either falls through to `SitemapParser`, or emits a distinct `dns_error` code).

### 3.2 Bug — `freddy visibility --keywords` silently drops the keyword filter

**Most damaging of the three bugs.** A less-disciplined agent could read brand-only response data as keyword-level evidence and fabricate keyword-specific citation counts.

**Symptom.** Agent invoked `freddy visibility --brand "nubank" --keywords "conta digital gratuita,conta digital com rendimento,..." --country BR` (8 account-related keywords). The CLI returned `"keywords": ["nubank"]` — the brand-only default. Second attempt with `--keywords=...` syntax returned the *byte-identical* payload (`logs/iteration_002.log.err:369-371` vs `:411-413`). The dropped keywords were not logged anywhere — no warning, no stderr.

**Root cause.** The CLI parses `--keywords` correctly. The bug is in the **fixture cache layer**: the cache key for `freddy visibility` is `sha1(brand)[:12]` only — keywords, country, and platforms are not part of the key. From `cli/freddy/commands/visibility.py:25-28`:

```python
cached = try_read_cache("freddy-visibility", "visibility", brand)
if cached is not None:
    typer.echo(json.dumps(cached))
    return
```

The third argument (`arg`) is the cache key; cache lookup is `artifact_filename(source, data_type, arg, shape_flags=None)` (`cli/freddy/fixture/cache.py:46-50`). Verified empirically:

```
$ python3 -c "import hashlib; print(hashlib.sha1(b'nubank').hexdigest()[:12])"
86f6f1cf1d8d
$ ls ~/.local/share/gofreddy/fixture-cache/search-v1/geo-nubank-br-conta/v1.0/
... freddy-visibility_visibility__86f6f1cf1d8d.json
```

The cached artifact was written by an earlier `freddy fixture refresh` that ran `freddy visibility --brand nubank` with NO `--keywords`, so the saved payload contains `"keywords": ["nubank"]`. Every subsequent in-session `freddy visibility --brand nubank ...` short-circuits on the cache and returns that pre-frozen brand-only payload before ever touching `api_request`.

The fixture-source manifest confirms the design defect at `cli/freddy/fixture/sources.json:38-45`: `arg_for_cache_key` reads from `client` (the brand) only — `keywords` and `country` are passed during refresh but excluded from the cache key. Regression introduced in commit `423f2a0`/`b084dfd` (PR #4, fixture infrastructure).

For comparison, peer commands DO use `shape_flags` correctly. From `cli/freddy/commands/detect.py:40-42`:

```python
cached = try_read_cache(
    "freddy-detect", "page", url, shape_flags={"full": "1" if full else "0"},
)
```

**Proposed minimal fix.**

1. **Pass `shape_flags` from `visibility_command` into `try_read_cache`** so keywords + country participate in the cache key:
   - `shape_flags={"keywords": ",".join(sorted(keyword_list)), "country": country}`
   - Pre-sort the keyword list before joining so a mere reorder still hits when intent matches.
2. **Update `cli/freddy/fixture/sources.json` `freddy-visibility` entry** to declare the new shape_flags so `freddy fixture refresh` rebuilds artifacts under the right keys.
3. **Add a stderr warning** at the cache-hit path in `cache_integration.try_read_cache` when the *invocation* args contain flags not represented in the cache key — defense in depth so the next analogous bug gets a loud signal.

A one-line interim fix that does not touch the fixture-refresh tooling: add a guard before the cache lookup that simply skips the cache when `keywords is not None and keywords != brand`. That at least prevents the "agent passes 8 keywords, gets brand-only payload" case from looking successful — the call falls through to a live fetch, which under the sandbox surfaces as an honest `connection_error` rather than a silent wrong answer.

**Suggested test.** Prime the fixture cache with a `freddy visibility --brand nubank` (no keywords) artifact, then invoke `visibility_command(brand="nubank", keywords="a,b,c")`, assert the response was *not* served from the brand-only cache.

### 3.3 Bug — `freddy detect/--full`, `freddy seo optimize`, competitor visibility all fail with `connection_error`

**Symptom.** After cached responses for already-primed args were exhausted, the agent tried `freddy detect https://nubank.com.br/conta/ --full`, `freddy seo optimize ...`, and `freddy visibility --brand "Banco Inter"` (and PicPay, Mercado Pago). All returned `{"error": {"code": "connection_error", "message": "Could not connect to API server"}}`. Direct `curl -sL https://nubank.com.br/sitemap.xml` failed with `Could not resolve host` — confirming this was a sandbox network issue, not a backend issue.

**Root cause.** The codex `workspace-write` sandbox uses Apple Seatbelt with `network_access = false` by default. There is no `[sandbox_workspace_write] network_access = true` in `~/.codex/config.toml` (verified). With Seatbelt's `network-outbound` denied, **all** outbound sockets are blocked — including DNS UDP/53 *and* TCP to loopback `127.0.0.1:8000`. Concretely:

- `freddy scrape <new-url>` → cache miss → `httpx.Client.post("http://127.0.0.1:8000/v1/geo/scrape")` → `httpx.ConnectError` → caught at `cli/freddy/api.py:224-226`:
  ```python
  except httpx.ConnectError:
      _emit_error(CLIError(code="connection_error", message="Could not connect to API server"))
      raise SystemExit(1)
  ```
- `freddy detect --full` → cache miss → same path → same error.
- `freddy visibility --brand "Banco Inter"` → cache miss (no Inter fixture) → live-fetch fallback → same error.
- `curl https://nubank.com.br/sitemap.xml` → fails at DNS → exit 6.

The reason iter-1's `freddy scrape https://nubank.com.br/conta/` succeeded inside the same sandbox: it served from the holdout cache. No socket needed. Every subsequent unprimed URL had no cache entry → tried network → blocked.

The autoresearch run-bootstrap correctly normalizes `FREDDY_API_URL` to `127.0.0.1:8000` (`autoresearch/archive/v009/run.py:141-148`); the loopback rewrite is sound — but Seatbelt blocks loopback all the same.

A secondary CLI defect amplifies the confusion: the message "Could not connect to API server" misleads. From the agent's perspective the API server is fine — what's broken is the agent process's network egress. Conflating the two sent the agent down a "retry the API" path instead of a "fall back to qualitative mode" path.

**Proposed minimal fix.** The actionable fix is **operator-side, not code-side**:

1. **Add `[sandbox_workspace_write] network_access = true` to `~/.codex/config.toml`.** This is the documented codex knob that enables outbound network egress under workspace-write. With network on, the sandbox can resolve external domains and reach the backend at 127.0.0.1:8000. JR's existing `personal-machine-agent-autonomy` memory already endorses this direction.
2. **Document the requirement in `autoresearch/archive/v009/run.py` startup checks.** Grep `~/.codex/config.toml` for `network_access = true` under `[sandbox_workspace_write]` AND assert `AUTORESEARCH_SESSION_SANDBOX` resolves to a mode that permits 127.0.0.1; abort with a clear remediation message if the sandbox would block loopback.

CLI-side improvements that make the *next* such failure observable:

3. **Distinguish "backend unreachable" from "agent has no network".** In `api.py`, when `httpx.ConnectError` fires for a 127.0.0.1 base_url, attempt a 100ms TCP-connect probe to the same address; if that also fails, emit `sandbox_network_blocked` instead of `connection_error` with a message naming the codex/Seatbelt likely cause.
4. **Refresh the agent prompt** with the new error code and an explicit mapping: `sandbox_network_blocked` ⇒ "stop all live `freddy` calls, switch to CQ-DATA qualitative mode, emit `[FILL: needs live data]` markers."

**Suggested test.** Startup smoke-test in `autoresearch/archive/v009/run.py` (or `harness/agent.py`) that, when `AUTORESEARCH_SESSION_SANDBOX != "danger-full-access"`, opens a TCP socket to `FREDDY_API_URL` from a freshly-spawned codex subprocess and aborts the run with a clear "sandbox blocks loopback — set `[sandbox_workspace_write] network_access = true`" message instead of letting iteration 1 fail mysteriously.

### 3.4 Side fix — autogen STRUCTURAL block must enumerate all gates

Closes H2 directly. Replace the autogen block at `geo-session.md:213-218` with the full enumeration. Concrete proposed prose (the autogen renderer in the lane registry should produce something like this):

> The structural validator for **geo** enforces these gates — all must pass before the artifact is scored: at least one non-empty file under `optimized/`; every `<script type="application/ld+json">` block parses as valid JSON; `gap_allocation.json` exists at the session root with at least one allocation; the artifact contains a literal `[INTRO]` marker on its own (around the 40-60-word answer-first intro from CQ-1); the artifact contains a `[FAQ]` marker, or a `## FAQ` heading, or a `## Frequently Asked` heading (around the 5-7 Q&A block from CQ-2); the artifact is at least 300 words. **The literal `[INTRO]` bracket form is required — `## Intro` / `## Introduction` will fail.** The same convention applies to `[HOWTO]`, `[SCHEMA]`, `[TECHFIX]`, `[PRUNE]`, and `[FILL]` markers, which are read by `scripts/build_geo_report.py` when compiling the final report.

The fix should land in the autogen renderer (the lane registry's structural-gate spec needs to teach itself to enumerate the literal-token checks), not as a hand-edit between the AUTOGEN sentinels — the comment at line 212 warns hand-edits are clobbered on every variant clone.

---

## 4. Architectural recommendation

### 4.1 The shape of the problem

The brief asks: should freddy * commands become optional shortcuts, with general-purpose agent fallback? Implicit theory: a more generative agent driving curl + AI APIs directly would route around freddy's bugs.

The investigation rejects that framing. The fallbacks the prompt already describes (`curl -sL`, qualitative mode) failed not because the agent didn't try — it tried — but because:

- The sandbox blocks curl as hard as it blocks freddy (§3.3).
- The prompt-level "fall back to qualitative" path's only protection against silent fabrication is plain-English rules with zero structural enforcement (H5).
- Even when freddy's calls succeeded, the cache layer served stale data without warning (§3.2), making the agent think tools worked when they didn't.

The architecture problem is not "the agent is too constrained." The architecture problem is **a multi-layer alignment gap between four contracts that should be co-generated and aren't**:

| Contract | Lives in | Says | When it drifts |
|---|---|---|---|
| **Prompt** | `programs/<lane>-session.md` | What the agent should do, what tools to use, what fallbacks to apply | A meta-agent edits the prompt and weakens it |
| **Sandbox policy** | `~/.codex/config.toml` + `AUTORESEARCH_SESSION_SANDBOX` | What the agent is *allowed* to do (network, fs, exec) | Operator changes config without updating prompt |
| **Tool surfaces** | `cli/freddy/`, fixture cache, `prompt_builder_entrypoint` allowlist | What freddy actually accepts/rejects/caches | Code drift (PR #37 SSRF guard, PR #4 cache key, Python 3.13 stdlib drift) |
| **Validator** | `workflows/session_eval_<lane>.py` + `scripts/summarize_session.py` + `judges/.../variant_scorer.py` | What constitutes a passing artifact | New gate added to code, not propagated to prompt |

Each contract has its own owner, its own change cadence, its own test surface. None of them is co-generated from a single source of truth. The v009 GEO failures are all instances of two of these contracts disagreeing:

- H2 / Bug 3.4: prompt vs validator (validator demands `[INTRO]`, prompt teaches "answer-first intro").
- H4: validator vs scorer (validator passes the artifact, summarizer flattens degradation, scorer reads only the summary).
- H5: prompt vs validator (prompt forbids fabrication, validator doesn't check).
- §3.2 visibility cache bug: agent's intent vs cache layer (agent passes keywords, cache ignores them).
- §3.3 sandbox: prompt's curl fallback vs sandbox network policy (prompt says fall back to curl, Seatbelt blocks curl).
- H3: stdlib import graph vs allowlist snapshot (Python 3.13's runpy adds urllib, allowlist doesn't know).

### 4.2 The fix shape — co-generation, not generality

The recommendation is **shrink the prompt-vs-validator delta until a meta-agent that mutates one without the other gets a test failure**. Five concrete moves, in increasing depth:

**M1 — Autogen the validator's full enumeration into the prompt.** The autogen STRUCTURAL block is the right idea executed wrong. It only stamps a curated subset of the gate. The lane registry's `structural_gate` spec needs to teach itself to enumerate every literal-token check, every word-count threshold, every required sidecar — and the autogen renderer needs to walk the gate function and surface its requirements. This is the H2 / Bug 3.4 fix, generalized.

**M2 — Make the sandbox policy a startup invariant, not an undocumented prerequisite.** When `autoresearch/archive/v00N/run.py` boots, it should grep `~/.codex/config.toml`, parse the active sandbox profile, and abort with a clear remediation if the configured network policy doesn't match the prompt's stated fallback paths (e.g., if the prompt says "fall back to `curl -sL`" but the sandbox blocks DNS, that's an invariant violation). The codex sandbox knob is documented; nothing checks it.

**M3 — Promote anti-fabrication prose to structural gates.** G1 from H5 (port competitive's citation-density regex into GEO) is ~10 lines of code. G2 ("if results.jsonl shows degraded data, require ≥1 `[FILL: ]` marker") closes the loop with H4: the same `tool_error_rate` signal that gates the score also gates the artifact's fabrication discipline. G3 is bigger but encapsulates the strongest contract.

**M4 — Surface degradation in the scorer's input.** Compute `tool_error_rate` in `summarize_session.py`. Append to `metrics/<domain>.jsonl`. Surface in the scorer's artifacts payload as a top-level field, not buried in `findings.md`. Update the scorer prompt to make tool health one of the things it explicitly considers — or add a multiplicative `tool_health_score` so the LLM doesn't have to. The H4 fix.

**M5 — Reduce the allowlist's scope.** Replace the 80-prefix allowlist with a single check that `autoresearch.__file__` resolves under `REPO_ROOT`. Stdlib drift becomes irrelevant. The H3 fix's structural form.

Notably absent: "make freddy commands optional with general-purpose fallback." That direction is wrong because:

- Freddy mediates paid AI engine APIs (Cloro for visibility, DataForSEO for SEO, PageSpeed). A general-purpose agent calling those directly has no rate-limit, no cache, no provider-rotation, no per-fixture cost cap. Freddy is value-add infrastructure, not a guard rail.
- The cached fixtures the autoresearch system depends on are pre-positioned under freddy command keys. Removing freddy means re-engineering fixture provisioning.
- The prompt already authorizes general-purpose fallbacks in non-freddy paths. The problem isn't freddy being mandatory; it's freddy's failures being illegible and the fallback paths not actually working in the sandbox.

### 4.3 Migration path

Three phases:

**Phase 1 (this week, all operator-side or 1-2 line code changes):**
- §5.1.1 — turn on `network_access = true` in codex config.
- §5.1.2 — apply the Bug 3.2 visibility cache-key one-liner so silent stale-data hits surface as honest connection errors.
- §3.4 — autogen the full STRUCTURAL block. One-paragraph patch in lane registry's renderer.
- §5.1.3 — log `tool_error_rate` to `metrics/<domain>.jsonl` (H4 option A).

After Phase 1, re-run v009 (or run v010). If the run is clean, you have baseline data on (a) what the sandbox-on world looks like, (b) what `tool_error_rate` distribution looks like on a healthy run, (c) whether the autogen prompt fix removes the iter-1 structural failure.

**Phase 2 (next sprint, ~1-2 weeks):**
- §3.1 — sitemap fail-open under DNS errors + split error codes.
- §3.3 — `sandbox_network_blocked` vs `connection_error` distinction in CLI, prompt update.
- M3.G1 — port competitive's citation-density regex into GEO structural gate.
- M5 — replace allowlist with `autoresearch.__file__` check + CI test for stdlib drift.

**Phase 3 (next month, plan-level work):**
- M1 — generalize the autogen STRUCTURAL block to walk the gate function and enumerate every check, across all lanes, on every variant clone.
- M3.G2 + M4 — wire `tool_error_rate` into validator (require `[FILL]` markers when degraded) and into scorer (gate or multiplier).
- M3.G3 — per-claim provenance manifest.

Phase 3 is what merits a separate plan document; Phases 1 and 2 are this report's deliverable.

---

## 5. Quick wins this week vs. deeper changes

### 5.1 Quick wins (operator can ship today)

#### 5.1.1 Turn on the codex sandbox network

Add to `~/.codex/config.toml`:

```toml
[sandbox_workspace_write]
network_access = true
```

This is the single largest quick win. It eliminates Bug 3.3 entirely, restores the prompt-level `curl -sL` fallback, allows the local Freddy backend at 127.0.0.1:8000 to be reachable, and turns the sandbox from "blocks all loopback silently" into "blocks nothing in loopback, applies file-write rules per workspace-write profile" — which is what JR's `personal-machine-agent-autonomy` memory already endorses for personal hardware.

Acceptance: after the change, `codex exec "curl -s http://127.0.0.1:8000/health"` from inside an autoresearch run should return `{"status":"ok"}`.

#### 5.1.2 Apply the visibility cache-key fix

The full fix involves `shape_flags` plumbing through `cli/freddy/fixture/sources.json` and a refresh of cached artifacts. The interim one-line guard (in `cli/freddy/commands/visibility.py` before the cache lookup):

```python
# Skip cache when invocation has filter args not in the cache key.
if keywords or country != _DEFAULT_COUNTRY:
    cached = None
else:
    cached = try_read_cache("freddy-visibility", "visibility", brand)
```

This converts the silent-stale-data failure into an honest live-fetch attempt, which (with §5.1.1 applied) succeeds, or (without §5.1.1) fails with `connection_error` — either of which is correctly observable. Permanent fix per §3.2 follows in Phase 2.

#### 5.1.3 Log `tool_error_rate` to metrics

Smallest H4 fix. In `autoresearch/archive/v009/scripts/summarize_session.py`, after the existing iteration counters, compute:

```python
tool_error_count = sum(
    1 for r in results
    if (r.get("status") or "").endswith("_degraded")
       or any(p in (r.get("notes") or "").lower()
              for p in ("connection_error", "could not resolve host", "freddy", "prompt_builder"))
)
tool_error_rate = tool_error_count / max(1, len(results))
```

Append to `metrics/<domain>.jsonl`. No gate, no multiplier. Just stop being silent.

#### 5.1.4 Autogen the STRUCTURAL block enumeration

The §3.4 fix lands in the lane registry's structural-gate-rendering code. It's a one-paragraph extension of whatever currently writes between the `<!-- AUTOGEN:STRUCTURAL:START -->` sentinels. The first time it runs, every lane's `programs/<lane>-session.md` gets the full enumeration on the next variant clone — which is exactly when the agent reads it.

Verification: re-run a v010 GEO fixture and confirm iter-1 emits an artifact with `[INTRO]`/`[FAQ]` markers on the first attempt. (Today, every iter-1 fails on this.)

### 5.2 Deeper changes (warrant a separate plan)

The Phase 3 list above. In particular:

- **M3.G3 — per-claim provenance manifest.** Real engineering effort. Requires defining the claims schema, updating the optimize prompt to emit the sidecar, updating the validator to parse it, deciding what counts as a "claim" worth binding. Estimated 2-3 weeks of design + implementation. Justifiable when the operator wants the strongest fabrication guarantee — which is presumably before any automated promotion of variants is enabled.

- **M1 — generalized autogen for prompt/validator co-generation.** The lane registry currently has a structural-gate spec that's terse and hand-curated. To autogen the full enumeration, the gate function itself needs to be specified declaratively (or instrumented) so the renderer can walk it. Probably a refactor of `lane_registry.py` and the lane-specific `session_eval_*.py` files. Estimated 1-2 weeks. Pays back across all five lanes.

- **M5 — allowlist replacement plus stdlib-drift CI.** The allowlist replacement is small (~30 lines) but the CI test that snapshots `sys.modules` across Python 3.12/3.13/3.14 needs supported worker images. If the operator only runs on one Python version, the CI test is overkill and the simple replacement suffices. If multiple versions are in play (laptop + Pi + CI workers), the test is load-bearing.

### 5.3 Triage by what they unblock

- **Re-running v009 cleanly:** Phase 1 quick wins (5.1.1 + 5.1.4 sufficient, 5.1.2 + 5.1.3 desirable).
- **Trusting v010+ scores in promotion logic:** Phase 1 + at least M3.G1 (citation density gate). Without it, the gradient signal is contaminated by the H4 issue.
- **Enabling automated meta-agent prompt mutations:** Phase 1 + Phase 2 + M3.G2 (or G3). Without structural anti-fabrication enforcement, a meta-agent that weakens the prompt has no test to fail it.
- **Stdlib upgrades on operator machines:** M5 makes Python 3.14 transitions a non-event.

---

## 6. File:line evidence index

For fast cross-reference. Investigation reports under `.tmp/investigation-*.md` carry the longer-form evidence; this is the spine.

### v009 forensic surface
- `autoresearch/archive/v009/sessions/geo/nubank/results.jsonl` — 6-line agent log. iter 3 has the only `completed_degraded` token; iter 4a is the failed `structural_gate`; iter 4b is the `kept` retry.
- `autoresearch/archive/v009/sessions/geo/nubank/findings.md` — `## Disproved` block lists 8 [API]/[INFRA] failures.
- `autoresearch/archive/v009/sessions/geo/nubank/session_summary.json:14-22` — `errors: []` despite the disproved block. Empirical confirmation of H4.
- `autoresearch/archive/v009/sessions/geo/nubank/logs/iteration_001.log.err:489-490, :518-519` — sitemap `invalid_url` rejections (Bug 3.1).
- `autoresearch/archive/v009/sessions/geo/nubank/logs/iteration_002.log.err:369-371, :411-413` — visibility silent-keyword-drop, byte-identical responses (Bug 3.2).
- `autoresearch/archive/v009/sessions/geo/nubank/logs/iteration_002.log.err:421-431` — `connection_error` for `freddy detect/--full` etc. (Bug 3.3).
- `autoresearch/archive/v009/sessions/geo/nubank/logs/iteration_004.log.err:2436` — agent's own forensic statement on H2.

### Prompt and contract
- `autoresearch/archive/v009/programs/geo-session.md:5` — "There is no prescribed workflow." (H1)
- `autoresearch/archive/v009/programs/geo-session.md:24-25` — CQ-1, CQ-2 semantic prose. (H2)
- `autoresearch/archive/v009/programs/geo-session.md:42, 167-170, 192-193, 195, 203` — anti-fabrication prose. (H5)
- `autoresearch/archive/v009/programs/geo-session.md:105-113` — freddy command surface table.
- `autoresearch/archive/v009/programs/geo-session.md:188-195` — Tool Call Resilience block.
- `autoresearch/archive/v009/programs/geo-session.md:213-218` — autogen STRUCTURAL block (lists 2 of 6 gates). (H2)

### Validator and scoring
- `autoresearch/archive/v009/workflows/session_eval_geo.py:64-96` — `structural_gate(...)`, FAQ + INTRO + 300-word checks. (H2)
- `autoresearch/archive/v009/workflows/session_eval_competitive.py:81-83` — citation density regex (the exemplar GEO has not adopted). (H5)
- `autoresearch/archive/v009/scripts/build_geo_report.py:73-84` — `_extract_blocks` reads the same `[INTRO]/[FAQ]/[HOWTO]/[SCHEMA]/[TECHFIX]/[PRUNE]/[FILL]` convention.
- `autoresearch/archive/v009/scripts/summarize_session.py:25-33` — `_validate_session_sources` (session-replay anti-fraud, NOT deliverable check). (H5)
- `autoresearch/archive/v009/scripts/summarize_session.py:51` — drops structural_gate rows. (H4)
- `autoresearch/archive/v009/scripts/summarize_session.py:89-95` — status-bucket map omits `completed_degraded`. (H4)
- `autoresearch/archive/v009/scripts/summarize_session.py:102-107` — error counter only reads structured `error` field. (H4)
- `autoresearch/evaluate_variant.py:995-1062` — `_extract_inner_pass_rate`, `_KEEP_TOKENS` excludes `completed_degraded`. (H4)
- `autoresearch/evaluate_variant.py:1082` — `_outer_pass_from_score` gates only on `structural_passed`.
- `autoresearch/evaluate_variant.py:1158-1200` — artifact materialization for the LLM judge.
- `judges/evolution/agents/variant_scorer.py:103-153` — `score_variant`. (H4)
- `judges/evolution/prompts/scorer.md:1-36` — scorer prompt (no tool-health language). (H4)
- `autoresearch/lane_registry.py:131-138` — geo structural gate spec.

### CLI and tool surface
- `cli/freddy/commands/sitemap.py:84-91` — local SSRF guard. (Bug 3.1)
- `src/common/url_validation.py:86-91` — `resolve_and_validate` (DNS lookup). (Bug 3.1)
- `cli/freddy/commands/visibility.py:25-28` — cache lookup keyed on brand only. (Bug 3.2)
- `cli/freddy/commands/detect.py:40-42` — peer command using `shape_flags` correctly.
- `cli/freddy/fixture/cache.py:46-50` — `artifact_filename`.
- `cli/freddy/fixture/sources.json:38-45` — visibility manifest, no shape_flags. (Bug 3.2)
- `cli/freddy/api.py:224-226` — `httpx.ConnectError` → `connection_error` envelope. (Bug 3.3)
- `autoresearch/archive/v009/run.py:141-148` — `FREDDY_API_URL` 127.0.0.1 normalization.

### Allowlist
- `autoresearch/harness/prompt_builder_entrypoint.py:1-37` — docstring with threat model.
- `autoresearch/harness/prompt_builder_entrypoint.py:58-91` — `_ALLOWED_PREFIXES` (80+ entries).
- `autoresearch/harness/prompt_builder_entrypoint.py:172-199` — `_is_allowed`.
- `autoresearch/harness/prompt_builder_entrypoint.py:202-229` — `_enforce_allowlist`.
- `tests/autoresearch/test_prompt_builder_isolation.py` — 5 tests (none catch stdlib drift).
- Commit `c120815` (2026-05-07 20:37 CEST) — tactical fix.

### Cached fixture artifacts
- `~/.local/share/gofreddy/fixture-cache/search-v1/geo-nubank-br-conta/v1.0/freddy-visibility_visibility__86f6f1cf1d8d.json` — the brand-only payload that masquerades as keyword-filtered.

### Codex sandbox config
- `~/.codex/config.toml` — should have `[sandbox_workspace_write] network_access = true`. Currently does not.

---

## 7. Methodology notes and caveats

The four parallel investigation streams ran independently and converged on the same architectural shape (prompt-vs-validator alignment, prompt-vs-sandbox alignment) without coordinating their language. That convergence is a strong signal — the same pattern is independently visible across CLI, allowlist, validator, and scorer.

Specific caveats:

- The H3 (allowlist) fix already shipped on `main` in `c120815`. The structural critique stands; the user will want to decide whether the deeper M5 fix is worth the scope or whether the tactical patch suffices.
- The H4 verdict is "TRUE" specifically for the programmatic scoring path. The LLM judges *can* see degradation in `findings.md`, but the prompt does not direct them to and the rubric does not score on it. Whether they sometimes penalize is unmeasured; the system's gradient signal cannot rely on that variance.
- Bug 3.3 (sandbox network) is the only one that's strictly operator-side. The CLI improvements for that bug (sandbox_network_blocked vs connection_error) are pure clarity wins and not strictly necessary if the operator just turns on `network_access = true`.
- The freddy CLI bugs (3.1, 3.2) would surface offline (no internet, no sandbox) for any user. They are not sandbox-specific. The sandbox just made them simultaneously visible.

The investigation deliberately did not propose code edits. All proposed fixes are described in prose with file:line references. The user's brief explicitly requested "do not commit unless I explicitly tell you to."

---

## 8. Next-step prompts for the user

If the user wants to act on this report:

- **"Apply the §5.1 quick wins."** Clear scope, all four are 1-line code changes or operator config edits. Re-run v009 GEO after to confirm iter-1 passes structural on the first attempt and `tool_error_rate` shows up in metrics.
- **"Open a separate plan for Phase 3."** §5.2 contents become the next planning doc — most natural to scope around M1 (autogen renderer), M3.G3 (claims manifest), and M5 (allowlist replacement) as three independent work items.
- **"Investigate further before shipping."** I have unread evidence in the mayoclinic and semrush logs that I only summarized. The detailed investigation reports under `.tmp/investigation-*.md` carry per-fixture evidence I can pull forward on request.
