// Filterless moments-timeline frontend for /portal/<slug>.
//
// CSP forbids inline scripts, so all behavior lives in this file:
//   1. DOMContentLoaded -> fetch /v1/portal/<slug>/moments (REST page-load).
//   2. Connect EventSource('/v1/portal/<slug>/stream') for live updates.
//   3. New SSE moments prepend; hard cap 50 in DOM.
//   4. onerror -> auth-probe; 401 redirects, 200 shows "reconnecting".
//   5. textContent (NOT innerHTML) on user-controlled title/body strings.
//
// Plan: docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md
// Spec: §"Unit 7: Filterless moments-timeline frontend".

(function () {
  "use strict";

  // Hard cap on DOM rows. (R2) Keep in sync with plan §Unit 7 Approach.
  var TIMELINE_CAP = 50;

  // Kinds the client-side SSE filter accepts. Keep in sync with
  // portal.py portal_moments TIMELINE_ELIGIBLE_KINDS.
  var TIMELINE_ELIGIBLE_KINDS = {
    moment: true,
    session_start: true,
    session_end: true,
    review_required: true,
    review_approve: true,
    review_reject: true,
    sla_breach: true,
    render: true,
    promotion: true
  };

  var SLUG = (document.querySelector("main[data-slug]") || {}).dataset
    ? document.querySelector("main[data-slug]").dataset.slug
    : "";

  // State -------------------------------------------------------------------
  var state = {
    eventSource: null,
    lastEventId: null,           // newest event id rendered, used for ?since=
    seenEventIds: Object.create(null),
    totalKnownCount: 0,
    eligibleKindsFilter: TIMELINE_ELIGIBLE_KINDS
  };

  // DOM refs ----------------------------------------------------------------
  function $(id) { return document.getElementById(id); }

  function fmtUsd(n) {
    var v = Number(n) || 0;
    return "$" + v.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function fmtTime(iso) {
    if (!iso) return "--:--:--";
    var d = new Date(iso);
    if (isNaN(d.getTime())) return "--:--:--";
    return d.toISOString().slice(11, 19);
  }

  // Sanitize a CSS class fragment from raw kind/moment_kind. Mirrors the
  // server-side regex pattern (^[a-z_]+$) — strips anything else so a
  // poisoned kind can't break out of class attribute context.
  function safeClass(raw) {
    if (typeof raw !== "string") return "";
    return raw.replace(/[^a-z0-9_]/g, "");
  }

  // Build the session-tag string from metadata (R3.1).
  function sessionTagFrom(moment) {
    // Server already computes this as moment.session_tag — prefer it. Keep
    // metadata fallback for SSE frames that omit the convenience field.
    if (typeof moment.session_tag === "string" && moment.session_tag) {
      return moment.session_tag;
    }
    var meta = moment.metadata || {};
    var lane = typeof meta.lane === "string" ? meta.lane : "";
    if (!lane) return "";
    var variant = typeof meta.variant === "string" ? meta.variant : "";
    return variant ? lane + "·" + variant : lane;
  }

  // Title for a row. Server pre-redacts metadata.title; we still apply
  // textContent at insertion time (T4 belt-and-suspenders).
  function titleFor(moment) {
    var meta = moment.metadata || {};
    if (typeof meta.title === "string" && meta.title) return meta.title;
    // Fallback when a top-level event (e.g. session_start) has no title:
    // present the kind for readability rather than an empty row.
    var k = moment.kind || "";
    return k;
  }

  function eventIdFor(moment) {
    return moment.event_id || moment.id || null;
  }

  function sessionIdFor(moment) {
    if (typeof moment.session_id === "string" && moment.session_id) {
      return moment.session_id;
    }
    var meta = moment.metadata || {};
    if (typeof meta.session_id === "string" && meta.session_id) {
      return meta.session_id;
    }
    return null;
  }

  function timestampFor(moment) {
    return moment.ts || moment.timestamp || null;
  }

  // Build a row DOM node for a moment. Anchor wraps the entire row so a
  // single click navigates to drill-down (R4).
  function buildRow(moment) {
    var eventId = eventIdFor(moment);
    var sessionId = sessionIdFor(moment);
    var kind = moment.kind || "";
    var meta = moment.metadata || {};
    var momentKind = typeof meta.moment_kind === "string" ? meta.moment_kind : "";

    var a = document.createElement("a");

    // Drill-down link: only sessions with a session_id are linkable. For
    // sessionless moments (rare — cost milestones etc.), point at the
    // portal root so the row still has stable click semantics.
    if (sessionId) {
      a.href =
        "/portal/" + encodeURIComponent(SLUG) +
        "/transcript/" + encodeURIComponent(sessionId) +
        (eventId ? ("?event_id=" + encodeURIComponent(eventId)) : "");
    } else {
      a.href = "/portal/" + encodeURIComponent(SLUG);
    }
    var classes = ["log-line"];
    classes.push("k-" + safeClass(kind));
    if (momentKind) classes.push("k-mk-" + safeClass(momentKind));
    a.className = classes.join(" ");
    if (eventId) a.setAttribute("data-event-id", eventId);

    var ts = document.createElement("span");
    ts.className = "ts";
    ts.textContent = fmtTime(timestampFor(moment));
    a.appendChild(ts);

    var tag = document.createElement("span");
    tag.className = "session-tag";
    tag.textContent = sessionTagFrom(moment);
    a.appendChild(tag);

    // review_required rows get the "needs review" badge between
    // session-tag and title.
    if (kind === "review_required") {
      var badge = document.createElement("span");
      badge.className = "badge badge-action";
      badge.textContent = "needs review";
      a.appendChild(badge);
    } else {
      // Empty placeholder span to keep the grid columns aligned; the title
      // span has grid-column: 4 / 5 to land in the right place anyway, but
      // a placeholder simplifies the grid for browsers that auto-place.
      var spacer = document.createElement("span");
      spacer.className = "badge-spacer";
      a.appendChild(spacer);
    }

    var title = document.createElement("span");
    title.className = "title";
    // T4: textContent (NOT innerHTML).
    title.textContent = titleFor(moment);
    a.appendChild(title);

    return a;
  }

  // Render the full timeline from a fresh REST response. Replaces children
  // wholesale; sets state.lastEventId from the first (newest) row.
  function renderTimelineFromRest(payload) {
    var timeline = $("timeline");
    var moments = (payload && payload.moments) || [];
    timeline.innerHTML = "";  // Replace skeleton/empty state.

    if (moments.length === 0) {
      var empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent =
        "No moments yet. Activity will appear here as agents work for you.";
      timeline.appendChild(empty);
      state.lastEventId = null;
      return;
    }

    // REST returns newest-first per the endpoint contract. Append in
    // order (newest at the top of the DOM).
    for (var i = 0; i < moments.length; i++) {
      var m = moments[i];
      var id = eventIdFor(m);
      if (id) state.seenEventIds[id] = true;
      timeline.appendChild(buildRow(m));
    }

    state.lastEventId = eventIdFor(moments[0]);

    // partial-load row: render when has_more is true OR (rare) we got
    // exactly TIMELINE_CAP rows on first paint and the server flags more.
    if (payload && payload.has_more) {
      var partial = document.createElement("div");
      partial.className = "partial-load";
      // We don't know the total N without a count query; show a
      // conservative message that matches the plan literal.
      var oldest = payload.oldest_event_id || "";
      partial.textContent =
        "Showing newest " + TIMELINE_CAP +
        " moments — older history via ?before=" + oldest;
      timeline.appendChild(partial);
    }
  }

  // Prepend a single new moment from the SSE stream. Hard cap enforced
  // by evicting the oldest rendered .log-line.
  function prependLiveMoment(moment) {
    var timeline = $("timeline");
    var eventId = eventIdFor(moment);

    // Dedup against REST payload + earlier SSE frames.
    if (eventId && state.seenEventIds[eventId]) return;
    if (eventId) state.seenEventIds[eventId] = true;

    // Remove empty-state if present.
    var empty = timeline.querySelector(".empty-state");
    if (empty) empty.remove();

    var row = buildRow(moment);
    // Insert before the first existing row (newest stays on top).
    timeline.insertBefore(row, timeline.firstChild);

    state.lastEventId = eventId || state.lastEventId;

    // Hard cap: keep at most TIMELINE_CAP .log-line rows in the DOM.
    var rows = timeline.querySelectorAll("a.log-line");
    while (rows.length > TIMELINE_CAP) {
      var last = rows[rows.length - 1];
      if (last && last.parentNode) last.parentNode.removeChild(last);
      rows = timeline.querySelectorAll("a.log-line");
    }
  }

  // Cost-ledger header ----------------------------------------------------

  function renderCostLedger(rollup) {
    var card = $("cost-card");
    if (!rollup || typeof rollup !== "object") {
      // ledger-bridge-down state.
      card.classList.add("is-unavailable");
      card.innerHTML = "";
      var row = document.createElement("div");
      row.className = "cost-metric";
      var msg = document.createElement("span");
      msg.className = "cost-unavailable";
      msg.textContent = "cost data unavailable";
      row.appendChild(msg);
      card.appendChild(row);
      return;
    }
    // Populated / zero-spend share the same shape — both render through here.
    var today = $("cost-today");
    var week = $("cost-week");
    var month = $("cost-month");
    if (today) today.textContent = fmtUsd(rollup.today_usd);
    if (week) week.textContent = fmtUsd(rollup.week_usd);
    if (month) month.textContent = fmtUsd(rollup.month_usd);
  }

  // Auth-probe + EventSource error handling ------------------------------

  function showReconnecting(show) {
    var ind = $("reconnect-indicator");
    if (!ind) return;
    if (show) ind.classList.add("is-active");
    else ind.classList.remove("is-active");
  }

  function authProbe() {
    return fetch(
      "/v1/portal/" + encodeURIComponent(SLUG) + "/moments?limit=1",
      { credentials: "same-origin" }
    );
  }

  function backfillSinceLast() {
    if (!state.lastEventId) return Promise.resolve();
    var url = "/v1/portal/" + encodeURIComponent(SLUG) +
      "/moments?since=" + encodeURIComponent(state.lastEventId);
    return fetch(url, { credentials: "same-origin" })
      .then(function (r) {
        if (!r.ok) return null;
        return r.json();
      })
      .then(function (payload) {
        if (!payload || !payload.moments) return;
        // payload.moments is newest-first; prepend in reverse so the
        // newest of them lands on top.
        var batch = payload.moments.slice().reverse();
        for (var i = 0; i < batch.length; i++) {
          prependLiveMoment(batch[i]);
        }
      })
      .catch(function () { /* network blip; SSE will retry */ });
  }

  function handleEventSourceError() {
    // W3C EventSource exposes no HTTP status on error — auth-probe to
    // classify (R-Auth-4 + plan Approach step 4).
    authProbe()
      .then(function (r) {
        if (r.status === 401) {
          // Cookie expired or invalidated. Clear local UI + redirect.
          showReconnecting(false);
          window.location = "/login";
          return;
        }
        if (r.status === 200) {
          // Transient drop — EventSource auto-reconnects per spec.
          showReconnecting(true);
          // Backfill missed moments via ?since=<last_seen_event_id>.
          backfillSinceLast().then(function () {
            // Hide the indicator on a successful backfill; if SSE is still
            // flapping, the next onerror will re-show it.
            showReconnecting(false);
          });
          return;
        }
        // Other status — treat as transient, leave indicator on.
        showReconnecting(true);
      })
      .catch(function () {
        // Network error on the probe itself — same UI as transient drop.
        showReconnecting(true);
      });
  }

  function connectStream() {
    if (state.eventSource) state.eventSource.close();
    // EventSource sends same-origin cookies automatically; sb_session
    // (Unit 4) authenticates the SSE handshake.
    var es = new EventSource(
      "/v1/portal/" + encodeURIComponent(SLUG) + "/stream"
    );
    state.eventSource = es;

    es.onopen = function () {
      showReconnecting(false);
    };

    es.onerror = function () {
      handleEventSourceError();
    };

    es.onmessage = function (msgEvent) {
      var payload = null;
      try {
        payload = JSON.parse(msgEvent.data);
      } catch (_) {
        return; // swallow malformed frames
      }
      if (!payload || typeof payload !== "object") return;
      // Client-side filter: only timeline-eligible kinds (R-Live-2).
      var kind = payload.kind;
      if (!kind || !state.eligibleKindsFilter[kind]) return;
      prependLiveMoment(payload);
    };
  }

  // Initial load ----------------------------------------------------------

  function fetchMomentsRest() {
    return fetch(
      "/v1/portal/" + encodeURIComponent(SLUG) +
        "/moments?limit=" + TIMELINE_CAP,
      { credentials: "same-origin" }
    ).then(function (r) {
      if (r.status === 401) {
        window.location = "/login";
        return null;
      }
      if (!r.ok) {
        throw new Error("HTTP " + r.status);
      }
      return r.json();
    });
  }

  function fetchSummaryForCosts() {
    return fetch(
      "/v1/portal/" + encodeURIComponent(SLUG) + "/summary",
      { credentials: "same-origin" }
    ).then(function (r) {
      if (r.status === 401) {
        window.location = "/login";
        return null;
      }
      if (!r.ok) return null;
      return r.json();
    }).catch(function () {
      return null;
    });
  }

  function init() {
    if (!SLUG) return;

    // SC1: fetch moments + summary in parallel so the cost-ledger header
    // renders alongside the timeline (no serial waterfall).
    var pMoments = fetchMomentsRest();
    var pSummary = fetchSummaryForCosts();

    pMoments
      .then(function (payload) {
        if (payload) renderTimelineFromRest(payload);
        connectStream();
      })
      .catch(function (e) {
        var timeline = $("timeline");
        timeline.innerHTML = "";
        var err = document.createElement("div");
        err.className = "empty-state";
        err.textContent = "Could not load moments — " + (e.message || "error");
        timeline.appendChild(err);
      });

    pSummary.then(function (payload) {
      if (!payload) {
        renderCostLedger(null);
        return;
      }
      // portal_summary._cost_rollup ships under payload.cost.
      var cost = payload.cost;
      // Bridge-down: cost field missing/null/error -> render unavailable.
      if (!cost || typeof cost !== "object") {
        renderCostLedger(null);
        return;
      }
      renderCostLedger(cost);
    });

    var emailBox = $("user-email");
    if (emailBox) emailBox.textContent = "";

    var logout = $("logout");
    if (logout) {
      logout.addEventListener("click", function () {
        // Delete the cookie via the Unit 4 endpoint, then redirect.
        fetch("/v1/auth/cookie", {
          method: "DELETE",
          credentials: "same-origin"
        }).then(function () {
          window.location = "/login";
        }).catch(function () {
          window.location = "/login";
        });
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
