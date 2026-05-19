// Drill-down transcript page interactions.
//
// CSP forbids inline scripts, so all behavior lives here:
//   1. ?event_id=<id> anchor → scroll to + highlight on DOMContentLoaded
//   2. Click on .agent-reasoning.collapsed → toggle .expanded
//   3. Click on .tool-call-row → toggle .expanded (reveals full args + result)
//
// Plan: docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md
// Spec: §"Unit 6: Transcript drill-down route + renderer".

(function () {
  "use strict";

  function getQueryParam(name) {
    var qs = window.location.search.replace(/^\?/, "");
    var pairs = qs.split("&");
    for (var i = 0; i < pairs.length; i++) {
      var kv = pairs[i].split("=");
      if (decodeURIComponent(kv[0]) === name) {
        return decodeURIComponent((kv[1] || "").replace(/\+/g, " "));
      }
    }
    return null;
  }

  function scrollToAnchor(eventId) {
    if (!eventId) return;
    var el = document.getElementById("evt_" + eventId);
    if (!el) return;
    // Smooth-scroll only on fresh load — repeated hits inside same SPA-ish
    // session would be jarring. Drill-down is a static page so this is fine.
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.classList.add("evt-highlight");
    // Remove highlight after a beat so it doesn't burn-in.
    window.setTimeout(function () {
      el.classList.remove("evt-highlight");
    }, 2400);
  }

  function bindReasoningToggles() {
    var reasonRows = document.querySelectorAll(".agent-reasoning");
    for (var i = 0; i < reasonRows.length; i++) {
      reasonRows[i].addEventListener("click", function (ev) {
        // Don't toggle if user clicked an anchor inside the body.
        var tag = (ev.target && ev.target.tagName) || "";
        if (tag === "A") return;
        this.classList.toggle("expanded");
        this.classList.toggle("collapsed");
      });
    }
  }

  function bindToolToggles() {
    var toolRows = document.querySelectorAll(".tool-call-row, .tool-result-row");
    for (var i = 0; i < toolRows.length; i++) {
      toolRows[i].addEventListener("click", function (ev) {
        var tag = (ev.target && ev.target.tagName) || "";
        if (tag === "A") return;
        this.classList.toggle("expanded");
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindReasoningToggles();
    bindToolToggles();
    var anchorEvt = getQueryParam("event_id");
    if (anchorEvt) scrollToAnchor(anchorEvt);
  });
})();
