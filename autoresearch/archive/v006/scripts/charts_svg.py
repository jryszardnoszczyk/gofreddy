"""Inline SVG chart helpers for autoresearch reports.

Pure-stdlib SVG generation — no matplotlib, no plotly, no JS runtime.
Output is `<svg>...</svg>` strings ready for embedding in
report.html. Chrome PDF + WeasyPrint both render SVG natively, so the
same chart appears in both HTML and PDF.

Functions:
    bar_chart(data, *, title=None, value_format='{:,.0f}', max_bars=12,
              width=720, height=320) -> str
    sparkline(values, *, width=240, height=40) -> str
    donut(slices, *, width=320, height=320, title=None) -> str
    timeline_dots(events, *, width=720, height=120) -> str

All helpers escape user-supplied text via xml.sax.saxutils.escape so
labels with HTML metacharacters render safely. The shared sanitizer
allows the SVG primitives these functions emit; agent-authored SVG
that uses the same primitive set passes through unchanged.

Style: muted earth tones matching the .rprt-* CSS palette
(BASE_CSS in src/shared/reporting/report_base.py).
"""
from __future__ import annotations

from xml.sax.saxutils import escape as _xml_escape

# Palette — chosen to read on the .rprt-* cream background (#fefcf6) and
# to match the theme accents from BASE_CSS. Sequential where it matters.
_PALETTE = [
    "#0f3460",  # navy (primary)
    "#16a34a",  # green (success)
    "#d97706",  # amber (warn)
    "#dc2626",  # red (critical)
    "#7c3aed",  # purple (insight)
    "#0891b2",  # teal (data)
    "#ea580c",  # orange (energy)
    "#525252",  # neutral
]


def _esc(s: str) -> str:
    return _xml_escape(str(s), {'"': "&quot;", "'": "&apos;"})


def _format_value(v: float, fmt: str) -> str:
    try:
        return fmt.format(v)
    except (KeyError, ValueError, IndexError):
        return str(v)


def bar_chart(
    data: list[tuple[str, float]],
    *,
    title: str | None = None,
    value_format: str = "{:,.0f}",
    max_bars: int = 12,
    width: int = 720,
    height: int = 320,
    color: str | None = None,
) -> str:
    """Horizontal bar chart with values labelled at the bar end.

    ``data``: list of (label, value) tuples. Sorted descending by value.
    Truncates to ``max_bars`` and shows a "+N more" footer if exceeded.
    """
    if not data:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} '
            f'40" width="{width}" height="40">'
            '<text x="10" y="24" font-family="Georgia,serif" font-size="13" '
            'fill="#6b7280">(no data)</text></svg>'
        )

    sorted_data = sorted(data, key=lambda kv: -float(kv[1]))
    overflow = max(0, len(sorted_data) - max_bars)
    rows = sorted_data[:max_bars]
    bar_color = color or _PALETTE[0]
    max_val = max((float(v) for _, v in rows), default=1.0) or 1.0
    title_pad = 30 if title else 0
    label_col_w = 220
    value_col_w = 90
    plot_x = label_col_w
    plot_w = max(60, width - label_col_w - value_col_w - 20)
    row_h = max(18, (height - title_pad - 20) // len(rows))
    total_h = title_pad + row_h * len(rows) + 24 + (24 if overflow else 0)
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} '
        f'{total_h}" width="{width}" height="{total_h}" '
        f'font-family="Georgia,serif">',
    ]
    if title:
        parts.append(
            f'<text x="0" y="20" font-size="14" font-weight="600" '
            f'fill="#0f3460">{_esc(title)}</text>'
        )
    for i, (label, value) in enumerate(rows):
        y = title_pad + i * row_h + 4
        bar_w = max(2, int((float(value) / max_val) * plot_w))
        # Label
        parts.append(
            f'<text x="0" y="{y + row_h * 0.6:.0f}" font-size="12" '
            f'fill="#1f2937">{_esc(str(label)[:34])}'
            + ("…" if len(str(label)) > 34 else "")
            + '</text>'
        )
        # Bar
        parts.append(
            f'<rect x="{plot_x}" y="{y}" width="{bar_w}" '
            f'height="{row_h - 6:.0f}" fill="{bar_color}" rx="3"/>'
        )
        # Value label
        parts.append(
            f'<text x="{plot_x + bar_w + 6}" y="{y + row_h * 0.65:.0f}" '
            f'font-size="11" fill="#374151" font-family="JetBrains Mono,'
            f'monospace">{_esc(_format_value(float(value), value_format))}'
            f'</text>'
        )
    if overflow:
        parts.append(
            f'<text x="0" y="{total_h - 4}" font-size="11" fill="#6b7280" '
            f'font-style="italic">+{overflow} more (full list in bundle)</text>'
        )
    parts.append('</svg>')
    return "".join(parts)


def sparkline(
    values: list[float], *, width: int = 240, height: int = 40,
    color: str | None = None,
) -> str:
    """Compact line chart for trend visualisation."""
    if not values:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} '
            f'{height}" width="{width}" height="{height}"></svg>'
        )
    line_color = color or _PALETTE[0]
    floats = [float(v) for v in values]
    lo, hi = min(floats), max(floats)
    rng = max(hi - lo, 1e-9)
    n = len(floats)
    pad_x, pad_y = 4, 4
    plot_w = width - 2 * pad_x
    plot_h = height - 2 * pad_y
    points = []
    for i, v in enumerate(floats):
        x = pad_x + (i / max(n - 1, 1)) * plot_w
        y = pad_y + plot_h - ((v - lo) / rng) * plot_h
        points.append(f"{x:.1f},{y:.1f}")
    last_x, last_y = points[-1].split(",")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} '
        f'{height}" width="{width}" height="{height}">'
        f'<polyline points="{" ".join(points)}" fill="none" '
        f'stroke="{line_color}" stroke-width="1.6" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="2.5" fill="{line_color}"/>'
        f'</svg>'
    )


def donut(
    slices: list[tuple[str, float]], *,
    width: int = 320, height: int = 320,
    title: str | None = None,
) -> str:
    """Donut chart with right-side legend.

    ``slices``: list of (label, value). 0-valued slices skipped.
    """
    nonzero = [(k, float(v)) for k, v in slices if float(v) > 0]
    if not nonzero:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} '
            f'{height}" width="{width}" height="{height}">'
            '<text x="10" y="24" font-family="Georgia,serif" font-size="13" '
            'fill="#6b7280">(no data)</text></svg>'
        )
    total = sum(v for _, v in nonzero)
    cx = height // 2
    cy = height // 2
    r_outer = min(cx, cy) - 16
    r_inner = r_outer * 0.55

    import math
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} '
        f'{height}" width="{width}" height="{height}" '
        f'font-family="Georgia,serif">',
    ]
    if title:
        parts.append(
            f'<text x="{cx}" y="20" font-size="13" font-weight="600" '
            f'fill="#0f3460" text-anchor="middle">{_esc(title)}</text>'
        )

    angle_start = -math.pi / 2  # start at 12 o'clock
    for i, (label, value) in enumerate(nonzero):
        frac = value / total
        angle_end = angle_start + frac * 2 * math.pi
        large_arc = 1 if (angle_end - angle_start) > math.pi else 0
        x0 = cx + r_outer * math.cos(angle_start)
        y0 = cy + r_outer * math.sin(angle_start)
        x1 = cx + r_outer * math.cos(angle_end)
        y1 = cy + r_outer * math.sin(angle_end)
        x2 = cx + r_inner * math.cos(angle_end)
        y2 = cy + r_inner * math.sin(angle_end)
        x3 = cx + r_inner * math.cos(angle_start)
        y3 = cy + r_inner * math.sin(angle_start)
        d = (
            f"M {x0:.1f} {y0:.1f} "
            f"A {r_outer} {r_outer} 0 {large_arc} 1 {x1:.1f} {y1:.1f} "
            f"L {x2:.1f} {y2:.1f} "
            f"A {r_inner} {r_inner} 0 {large_arc} 0 {x3:.1f} {y3:.1f} Z"
        )
        color = _PALETTE[i % len(_PALETTE)]
        parts.append(
            f'<path d="{d}" fill="{color}" stroke="#fefcf6" stroke-width="1.5"/>'
        )
        angle_start = angle_end

    # Centre total
    parts.append(
        f'<text x="{cx}" y="{cy + 4}" font-size="20" font-weight="700" '
        f'fill="#0f3460" text-anchor="middle">'
        f'{_format_value(total, "{:,.0f}")}</text>'
    )
    parts.append(
        f'<text x="{cx}" y="{cy + 22}" font-size="11" fill="#6b7280" '
        f'text-anchor="middle">total</text>'
    )

    # Legend below the donut
    legend_y = 2 * cy + 4
    parts.append(
        f'<g transform="translate(20, {legend_y})">'
    )
    cols = 2
    col_w = (width - 40) // cols
    for i, (label, value) in enumerate(nonzero[:8]):
        col = i % cols
        row = i // cols
        x = col * col_w
        y = row * 16
        color = _PALETTE[i % len(_PALETTE)]
        pct = 100.0 * value / total
        parts.append(
            f'<rect x="{x}" y="{y}" width="10" height="10" fill="{color}" rx="2"/>'
            f'<text x="{x + 16}" y="{y + 9}" font-size="11" fill="#1f2937">'
            f'{_esc(str(label)[:24])}'
            + ("…" if len(str(label)) > 24 else "")
            + f' <tspan fill="#6b7280">{pct:.0f}%</tspan></text>'
        )
    parts.append('</g>')
    parts.append('</svg>')
    # bump viewBox height to fit legend
    legend_rows = (min(len(nonzero), 8) + cols - 1) // cols
    extended_h = legend_y + legend_rows * 16 + 12
    return parts[0].replace(
        f'viewBox="0 0 {width} {height}"',
        f'viewBox="0 0 {width} {extended_h}"',
    ).replace(
        f'height="{height}"',
        f'height="{extended_h}"',
    ) + "".join(parts[1:])


def timeline_dots(
    events: list[tuple[str, float]], *,
    width: int = 720, height: int = 120,
    color: str | None = None,
) -> str:
    """Horizontal timeline: list of (label, x_position 0..1)."""
    if not events:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} '
            f'{height}" width="{width}" height="{height}"></svg>'
        )
    line_color = color or _PALETTE[0]
    pad_x = 30
    plot_w = width - 2 * pad_x
    y_axis = height // 2
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} '
        f'{height}" width="{width}" height="{height}" '
        f'font-family="Georgia,serif">',
        f'<line x1="{pad_x}" y1="{y_axis}" x2="{width - pad_x}" '
        f'y2="{y_axis}" stroke="#d4d0c0" stroke-width="2" '
        f'stroke-linecap="round"/>',
    ]
    for i, (label, frac) in enumerate(events):
        x = pad_x + max(0.0, min(1.0, float(frac))) * plot_w
        # Alternate above / below to avoid label overlap
        text_y = y_axis - 18 if i % 2 == 0 else y_axis + 26
        parts.append(
            f'<circle cx="{x}" cy="{y_axis}" r="6" fill="{line_color}" '
            f'stroke="#fefcf6" stroke-width="2"/>'
            f'<text x="{x}" y="{text_y}" font-size="11" fill="#1f2937" '
            f'text-anchor="middle">{_esc(str(label)[:24])}</text>'
        )
    parts.append('</svg>')
    return "".join(parts)
