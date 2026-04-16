"""Markdown rendering for competitive briefs."""

from __future__ import annotations

from typing import Any


def render_brief_markdown(brief_data: dict[str, Any]) -> str:
    """Render a competitive brief as markdown. Pure function."""
    parts: list[str] = []
    client_name = brief_data.get("client_name", "Client")
    date_range = brief_data.get("date_range", "7d")

    parts.append(f"# Competitive Intelligence Brief — {client_name}")
    parts.append(f"\n**Period:** {date_range}\n")

    # Executive summary
    exec_summary = brief_data.get("executive_summary")
    if exec_summary:
        parts.append("## Executive Summary\n")
        parts.append(exec_summary)
        parts.append("")

    # Sections
    for section in brief_data.get("sections", []):
        title = section.get("title", "Section")
        status = section.get("status", "ok")
        content = section.get("content", "")

        parts.append(f"## {title}\n")

        if status in ("skipped", "error"):
            parts.append(f"*{content}*\n")
            continue

        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            parts.append(_format_list_content(title, content))
        else:
            parts.append(str(content))
        parts.append("")

    # Changes
    changes = brief_data.get("changes", [])
    if changes:
        parts.append("## Changes from Prior Brief\n")
        for change in changes:
            parts.append(f"- {change.get('change', '')}")
        parts.append("")

    # Recommendations
    recommendations = brief_data.get("recommendations", [])
    if recommendations:
        parts.append("## Recommendations\n")
        for i, rec in enumerate(recommendations, 1):
            parts.append(f"{i}. {rec}")
        parts.append("")

    return "\n".join(parts)


def _format_list_content(title: str, items: list[dict[str, Any]]) -> str:
    """Format list content as a markdown table or list."""
    if not items:
        return "*No data available.*"

    title_lower = title.lower()

    if "share of voice" in title_lower:
        return _format_sov_table(items)
    elif "sentiment" in title_lower:
        return _format_sentiment(items)
    elif "ads" in title_lower:
        return _format_ads(items)
    elif "partnership" in title_lower:
        return _format_partnerships(items)
    else:
        return _format_generic_table(items)


def _format_sov_table(items: list[dict[str, Any]]) -> str:
    lines = ["| Brand | Mentions | Share | Sentiment |", "|-------|----------|-------|-----------|"]
    for item in items:
        brand = item.get("brand", "")
        mentions = item.get("mention_count", 0)
        pct = item.get("percentage", 0)
        sentiment = item.get("sentiment_avg", 0)
        lines.append(f"| {brand} | {mentions} | {pct:.1f}% | {sentiment:.2f} |")
    return "\n".join(lines)


def _format_sentiment(items: list[dict[str, Any]]) -> str:
    lines = ["| Period | Avg Sentiment | Mentions | Positive | Negative |",
             "|--------|--------------|----------|----------|----------|"]
    for item in items:
        period = item.get("period", "")
        avg = item.get("avg_sentiment", 0)
        count = item.get("mention_count", 0)
        pos = item.get("positive", 0)
        neg = item.get("negative", 0)
        lines.append(f"| {period} | {avg:.2f} | {count} | {pos} | {neg} |")
    return "\n".join(lines)


def _format_ads(items: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for i, ad in enumerate(items[:10], 1):  # Cap display at 10
        headline = ad.get("headline", "No headline")
        platform = ad.get("platform", "unknown")
        provider = ad.get("provider", "")
        body = (ad.get("body_text") or "")[:100]
        lines.append(f"### Ad {i}: {headline}")
        lines.append(f"**Platform:** {platform} | **Source:** {provider}")
        if body:
            lines.append(f"> {body}")
        lines.append("")
    return "\n".join(lines)


def _format_partnerships(items: list[dict[str, Any]]) -> str:
    lines = ["| Brand | Creator | Platform | Mentions | Status |",
             "|-------|---------|----------|----------|--------|"]
    for item in items:
        brand = item.get("brand", "")
        creator = item.get("creator", "")
        platform = item.get("platform", "")
        count = item.get("mention_count", 0)
        status = "NEW" if item.get("is_new") else ("ESCALATION" if item.get("is_escalation") else "")
        lines.append(f"| {brand} | {creator} | {platform} | {count} | {status} |")
    return "\n".join(lines)


def _format_generic_table(items: list[dict[str, Any]]) -> str:
    if not items:
        return "*No data.*"

    # Use first item's keys as columns
    keys = list(items[0].keys())[:6]  # Cap at 6 columns
    header = "| " + " | ".join(keys) + " |"
    sep = "|" + "|".join("---" for _ in keys) + "|"
    rows = []
    for item in items[:20]:  # Cap at 20 rows
        vals = [str(item.get(k, ""))[:50] for k in keys]
        rows.append("| " + " | ".join(vals) + " |")
    return "\n".join([header, sep] + rows)
