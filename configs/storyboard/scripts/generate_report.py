#!/usr/bin/env python3
"""Generate a comprehensive HTML+PDF storyboard report from a session directory.

Downloads all scene preview images, assembles a multi-phase HTML report, and
converts it to PDF via headless Chrome.

Usage:
    python3 configs/storyboard/scripts/generate_report.py sessions/storyboard/Gossip.Goblin
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import httpx

# Add project root to path for autoresearch imports
_project_root = Path(__file__).resolve().parents[3]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from autoresearch.report_base import (
    build_html_document,
    common_argparse,
    esc,
    html_to_pdf,
    load_json,
    load_jsonl,
    load_markdown,
    md_to_html,
    parse_findings,
    render_findings,
    render_logs_appendix,
    render_session_log,
    render_session_summary,
    truncate,
)

# ---------------------------------------------------------------------------
# Storyboard-specific CSS
# ---------------------------------------------------------------------------

STORYBOARD_CSS = """\
.scene-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }
.scene-card { border: 1px solid #ddd; border-radius: 8px; overflow: hidden; page-break-inside: avoid; }
.scene-card img { width: 100%; height: auto; display: block; }
.scene-info { padding: 10px; font-size: 0.85em; }
.scene-info strong { color: #0f3460; }
.scores { display: inline-block; background: #e8f5e9; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
.protagonist { background: #fff3e0; padding: 10px; border-radius: 6px; margin: 8px 0; }
.beats { background: #f3e5f5; padding: 10px; border-radius: 6px; margin: 8px 0; }
.prompt { font-size: 0.8em; color: #555; margin-top: 5px; }
.score-low { background: #fff3e0; }
.score-high { background: #e8f5e9; }
.story-bible { background: #e8eaf6; padding: 15px; border-radius: 8px; margin: 10px 0; }
.feedback { font-size: 0.8em; color: #666; font-style: italic; margin-top: 4px; }
.scene-details { font-size: 0.8em; margin: 6px 0; display: grid; grid-template-columns: auto 1fr; gap: 2px 8px; }
.scene-details dt { font-weight: 600; color: #0f3460; }
.scene-details dd { margin: 0; color: #444; }
.audio-script { background: #f8f8f0; border-left: 3px solid #666; padding: 8px 12px; margin: 4px 0; font-style: italic; line-height: 1.5; }
.pattern-error { color: #ef5350; font-size: 0.8em; }
.pattern-card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 12px 0; page-break-inside: avoid; overflow: hidden; }
.pattern-card .thumb { width: 160px; height: 90px; object-fit: cover; border-radius: 4px; float: left; margin-right: 12px; }
.pattern-card .meta-row { font-size: 0.85em; color: #555; margin: 4px 0; }
.pattern-card .narrative-field { margin: 6px 0; }
.pattern-card .narrative-field dt { font-weight: 600; color: #0f3460; font-size: 0.85em; margin-top: 8px; }
.pattern-card .narrative-field dd { margin: 2px 0 0 0; font-size: 0.85em; color: #333; }
.confidence-badge { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 0.75em; margin-right: 4px; }
.conf-high { background: #e8f5e9; color: #2e7d32; }
.conf-med { background: #fff3e0; color: #e65100; }
.conf-low { background: #ffebee; color: #c62828; }
details summary { cursor: pointer; font-weight: 600; color: #666; font-size: 0.9em; padding: 4px 0; }
.sb-meta { background: #f5f5f5; padding: 10px 14px; border-radius: 6px; margin-bottom: 10px; font-size: 0.85em; }
.sb-meta dt { font-weight: 600; color: #0f3460; display: inline; }
.sb-meta dd { display: inline; margin: 0 12px 0 4px; }
"""


# ---------------------------------------------------------------------------
# Image downloading
# ---------------------------------------------------------------------------


def download_images(
    frames_dir: Path,
    export_dir: Path,
    storyboards: list[dict],
) -> dict[str, Path]:
    """Download all scene images from R2 URLs. Returns {scene_id: local_path}."""
    image_map: dict[str, Path] = {}
    export_dir.mkdir(parents=True, exist_ok=True)

    download_tasks: list[tuple[str, str, int, str]] = []

    for sb in storyboards:
        project_id = sb.get("project_id", sb.get("id", "unknown"))
        proj_short = project_id[:8]
        frame_data = load_json(frames_dir / f"{project_id}.json")
        if not frame_data or not isinstance(frame_data, dict):
            continue
        for scene in frame_data.get("scenes", frame_data.get("frames", [])):
            url = scene.get("image_url")
            scene_id = scene.get("scene_id", scene.get("id", ""))
            idx = scene.get("index", 0)
            if url:
                download_tasks.append((proj_short, scene_id, idx, url))

    if not download_tasks:
        print("  No images to download.", file=sys.stderr)
        return image_map

    print(f"  Downloading {len(download_tasks)} scene images...", file=sys.stderr)

    with httpx.Client(
        timeout=httpx.Timeout(30.0, read=60.0),
        follow_redirects=True,
    ) as client:
        for proj_short, scene_id, idx, url in download_tasks:
            filename = f"{proj_short}_scene{idx}.png"
            dest = export_dir / filename
            try:
                resp = client.get(url)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
                image_map[scene_id] = dest
                print(f"    OK  {filename} ({len(resp.content) // 1024}KB)", file=sys.stderr)
            except Exception as exc:
                print(f"    FAIL {filename}: {exc}", file=sys.stderr)

    return image_map


# ---------------------------------------------------------------------------
# Storyboard-specific renderers
# ---------------------------------------------------------------------------


def render_header(
    creator: str,
    platform: str,
    video_count: int,
    storyboard_count: int,
    frame_count: int,
) -> str:
    from datetime import datetime, timezone

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""\
<h1>Storyboard Report &mdash; {esc(creator)}</h1>
<div class="story-meta">
  <strong>Creator:</strong> {esc(creator)} &nbsp;|&nbsp;
  <strong>Platform:</strong> {esc(platform)} &nbsp;|&nbsp;
  <strong>Date:</strong> {date_str} &nbsp;|&nbsp;
  <strong>Videos Analyzed:</strong> {video_count} &nbsp;|&nbsp;
  <strong>Storyboards:</strong> {storyboard_count} &nbsp;|&nbsp;
  <strong>Total Frames:</strong> {frame_count}
</div>
"""


def render_report_md_section(report_md_text: str) -> str:
    """Convert the main report.md to styled HTML via mistune."""
    if not report_md_text:
        return ""
    lines = report_md_text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("# ") or not line.strip() or line.startswith("**") or line.startswith("---"):
            start = i + 1
        else:
            break
    body = "\n".join(lines[start:])
    return f'<div class="report-md">\n{md_to_html(body)}\n</div>'


def render_story_plans(session_dir: Path) -> str:
    """Render story plans from stories/*.json when report.md is not available."""
    stories_dir = session_dir / "stories"
    if not stories_dir.is_dir():
        return ""
    stories: list[dict] = []
    for p in sorted(stories_dir.glob("*.json")):
        data = load_json(p)
        if data and isinstance(data, dict):
            stories.append(data)
    if not stories:
        return ""

    parts: list[str] = ['<h2><span class="phase-header">Story Plans</span> Production Briefs</h2>']

    for story in stories:
        title = esc(story.get("title", "Untitled"))
        logline = esc(story.get("logline", ""))
        why = esc(story.get("why_this_works", ""))
        emotion = esc(story.get("emotional_map", ""))
        visual_sig = esc(story.get("visual_signature", ""))
        voice_style = esc(story.get("voice_style", ""))
        duration = story.get("duration_target_seconds", "?")
        scene_count = story.get("scene_count", "?")

        # Protagonist
        protag = story.get("protagonist", {})
        if isinstance(protag, dict):
            protag_html = f"""<strong>{esc(protag.get('name', ''))}</strong> — {esc(protag.get('role', ''))}<br>
            <em>{esc(protag.get('personality', ''))}</em><br>
            Visual: {esc(protag.get('visual', ''))}"""
        else:
            protag_html = esc(str(protag))

        # Supporting characters
        supporting = story.get("supporting_characters", [])
        if supporting and isinstance(supporting, list):
            sup_items = "".join(
                f"<li><strong>{esc(c.get('name', ''))}</strong> ({esc(c.get('role', ''))}) — {esc(c.get('visual', ''))}</li>"
                for c in supporting if isinstance(c, dict)
            )
            sup_html = f"<ul>{sup_items}</ul>" if sup_items else ""
        else:
            sup_html = ""

        # Voice script
        voice_script = story.get("voice_script", [])
        if voice_script and isinstance(voice_script, list):
            vs_items = "".join(
                f'<li><strong>{esc(v.get("beat", ""))}</strong>: "{esc(v.get("line", ""))}" <em>({esc(v.get("delivery", ""))})</em></li>'
                for v in voice_script if isinstance(v, dict)
            )
            vs_html = f"<ul>{vs_items}</ul>" if vs_items else ""
        else:
            vs_html = ""

        # Audio design
        audio_design = story.get("audio_design", {})
        if audio_design and isinstance(audio_design, dict):
            ad_parts = []
            if audio_design.get("music_genre"):
                ad_parts.append(f"<dt>Music</dt><dd>{esc(str(audio_design['music_genre']))}</dd>")
            if audio_design.get("sound_effects"):
                sfx = audio_design["sound_effects"]
                if isinstance(sfx, list):
                    ad_parts.append(f"<dt>SFX</dt><dd>{esc(', '.join(str(s) for s in sfx))}</dd>")
            if audio_design.get("voice_processing"):
                ad_parts.append(f"<dt>Voice FX</dt><dd>{esc(str(audio_design['voice_processing']))}</dd>")
            if audio_design.get("silence_moments"):
                sil = audio_design["silence_moments"]
                if isinstance(sil, list):
                    ad_parts.append(f"<dt>Silence</dt><dd>{esc(', '.join(str(s) for s in sil))}</dd>")
            ad_html = f'<dl class="scene-details">{"".join(ad_parts)}</dl>' if ad_parts else ""
        else:
            ad_html = ""

        # Story beats
        beats = story.get("story_beats", {})
        if beats and isinstance(beats, dict):
            beats_items = "".join(
                f"<li><strong>{esc(str(k))}</strong>: {esc(str(v))}</li>"
                for k, v in beats.items()
            )
            beats_html = f"<ul>{beats_items}</ul>"
        else:
            beats_html = ""

        # Visual production
        visual_prod = story.get("visual_production", [])
        if visual_prod and isinstance(visual_prod, list):
            vp_items = "".join(
                f"<li>{esc(str(v.get('scene', '')))}: {esc(str(v.get('prompt', v.get('description', ''))))}</li>"
                for v in visual_prod if isinstance(v, dict)
            )
            vp_html = f"<ul>{vp_items}</ul>" if vp_items else ""
        else:
            vp_html = ""

        parts.append(f"""
<div class="story-bible" style="margin-bottom: 20px;">
  <h3>{title}</h3>
  <p><strong>Logline:</strong> {logline}</p>
  <p><strong>Duration:</strong> {duration}s &nbsp;|&nbsp; <strong>Scenes:</strong> {scene_count}</p>
  <p><strong>Emotional Arc:</strong> {emotion}</p>
  <p><strong>Visual Signature:</strong> {visual_sig}</p>
  <p><strong>Why This Works:</strong> <em>{why}</em></p>

  <h4>Protagonist</h4>
  <p>{protag_html}</p>

  {"<h4>Supporting Characters</h4>" + sup_html if sup_html else ""}

  <h4>Voice &amp; Dialogue Style</h4>
  <p>{voice_style}</p>
  {"<h4>Voice Script</h4>" + vs_html if vs_html else ""}

  {"<h4>Audio Design</h4>" + ad_html if ad_html else ""}

  {"<h4>Story Beats</h4>" + beats_html if beats_html else ""}

  {"<h4>Visual Production Plan</h4>" + vp_html if vp_html else ""}
</div>""")

    return "\n".join(parts)


def render_session_overview(session_md: str) -> str:
    """Render session metadata and analysis overview from session.md."""
    if not session_md:
        return ""
    parts: list[str] = ['<h2><span class="phase-header">Session</span> Pipeline Overview</h2>']
    parts.append(f'<div class="report-md">\n{md_to_html(session_md)}\n</div>')
    return "\n".join(parts)


def render_storyboards(
    storyboards: list[dict],
    frames_data: dict[str, dict],
    image_map: dict[str, Path],
) -> str:
    """Render scene image gallery."""
    if not storyboards:
        return ""
    parts: list[str] = [
        '<h2><span class="phase-header">Scene Gallery</span> Generated Frames</h2>'
    ]

    for sb in storyboards:
        project_id = sb.get("project_id", sb.get("id", "unknown"))
        title = esc(sb.get("title", "Untitled"))
        short_title = title.split(" \u2014 ")[0].split(" — ")[0] if (" \u2014 " in title or " — " in title) else title

        frame_file = frames_data.get(project_id, {})
        frame_scenes = {s.get("scene_id", s.get("id", "")): s for s in frame_file.get("scenes", frame_file.get("frames", []))}

        merged_scenes: list[dict] = []
        for scene in sb.get("scenes", []):
            scene_id = scene.get("id") or scene.get("scene_id", "")
            frame_scene = frame_scenes.get(scene_id, {})
            merged = {**scene, **{k: v for k, v in frame_scene.items() if v is not None}}
            merged_scenes.append(merged)

        merged_scenes.sort(key=lambda s: s.get("index", 0))

        if not merged_scenes:
            continue

        # Storyboard-level metadata
        protag_desc = esc(sb.get("protagonist_description", ""))
        emotion_arc = esc(sb.get("target_emotion_arc", ""))
        style_brief = esc(sb.get("style_brief_summary", ""))
        src_count = len(sb.get("source_analysis_ids", []))

        sb_meta_parts: list[str] = []
        if protag_desc and protag_desc not in ("Not specified", ""):
            sb_meta_parts.append(f"<dt>Protagonist:</dt><dd>{protag_desc}</dd>")
        if emotion_arc and emotion_arc not in ("Not specified", ""):
            sb_meta_parts.append(f"<dt>Emotion Arc:</dt><dd>{emotion_arc}</dd>")
        if style_brief:
            sb_meta_parts.append(f"<dt>Style:</dt><dd>{style_brief}</dd>")
        if src_count:
            sb_meta_parts.append(f"<dt>Sources:</dt><dd>{src_count} analyzed videos</dd>")
        sb_meta_html = f'<dl class="sb-meta">{"".join(sb_meta_parts)}</dl>' if sb_meta_parts else ""

        parts.append(f'<h3>{short_title}</h3>\n{sb_meta_html}\n<div class="scene-grid">')

        for scene in merged_scenes:
            idx = scene.get("index", 0)
            scene_id = scene.get("id") or scene.get("scene_id", "")
            scene_title = esc(scene.get("title", f"Scene {idx}"))
            duration = scene.get("duration_seconds", "?")
            beat = esc(scene.get("beat", ""))
            scene_score = scene.get("scene_score", "?")
            style_score = scene.get("style_score", "?")
            qa_score = scene.get("qa_score", "?")
            prompt_text = esc(scene.get("prompt", ""))
            feedback = esc(scene.get("feedback", ""))
            caption = esc(scene.get("caption", ""))
            audio_direction = esc(scene.get("audio_direction", ""))
            summary = esc(scene.get("summary", ""))
            shot_type = esc(scene.get("shot_type", ""))
            camera_movement = esc(scene.get("camera_movement", ""))
            transition = esc(scene.get("transition", ""))
            improvement = esc(scene.get("improvement_suggestion", ""))

            try:
                score_class = "score-high" if int(qa_score) >= 8 else "score-low"
            except (ValueError, TypeError):
                score_class = ""

            local_path = image_map.get(scene_id)
            if local_path and local_path.exists():
                img_rel = local_path.name
                img_html = f'<img src="{esc(img_rel)}" alt="Scene {idx}: {scene_title}" loading="lazy">'
            else:
                img_html = (
                    '<div style="height:200px;background:#eee;display:flex;'
                    'align-items:center;justify-content:center;color:#999;">'
                    "Image not available</div>"
                )

            feedback_html = f'<div class="feedback">{feedback}</div>' if feedback else ""

            # Build detail rows for non-empty fields
            details = []
            if summary:
                details.append(f"<dt>Summary</dt><dd>{summary}</dd>")
            if audio_direction:
                details.append(
                    f'<dt>Voiceover &amp; Audio</dt>'
                    f'<dd><blockquote class="audio-script">{audio_direction}</blockquote></dd>'
                )
            if shot_type:
                details.append(f"<dt>Shot</dt><dd>{shot_type}</dd>")
            if camera_movement:
                details.append(f"<dt>Camera</dt><dd>{camera_movement}</dd>")
            if transition:
                details.append(f"<dt>Transition</dt><dd>{transition}</dd>")
            if improvement:
                details.append(f"<dt>Improve</dt><dd>{improvement}</dd>")
            details_html = f'<dl class="scene-details">{"".join(details)}</dl>' if details else ""

            parts.append(f"""\
  <div class="scene-card">
    {img_html}
    <div class="scene-info">
      <strong>{scene_title}</strong> &mdash; {duration}s &mdash; <em>{beat}</em><br>
      <span class="scores {score_class}">QA: {qa_score} | Scene: {scene_score} | Style: {style_score}</span>
      <div class="prompt">{prompt_text}</div>
      {details_html}
      {feedback_html}
    </div>
  </div>""")

        parts.append("</div>")  # close scene-grid

    return "\n".join(parts)


def _conf_badge(score: float) -> str:
    """Return a colored confidence badge."""
    if score >= 0.8:
        cls = "conf-high"
    elif score >= 0.5:
        cls = "conf-med"
    else:
        cls = "conf-low"
    return f'<span class="confidence-badge {cls}">{score:.0%}</span>'


def _is_rich_pattern(p: dict) -> bool:
    """Check if a pattern has meaningful narrative data."""
    for field in ("transcript_summary", "story_arc", "protagonist"):
        val = p.get(field, "")
        if val and val not in ("", "Not available"):
            return True
    return False


def render_pattern_extractions(patterns: list[dict], platform: str = "youtube") -> str:
    """Render full per-video analysis cards with thumbnails and all narrative fields."""
    if not patterns:
        return ""

    # Separate rich vs empty patterns
    rich = [p for p in patterns if _is_rich_pattern(p)]
    sparse = [p for p in patterns if not _is_rich_pattern(p)]

    parts: list[str] = [
        f'<h2><span class="phase-header">Video Analysis</span> Pattern Extractions ({len(rich)} rich, {len(sparse)} structural)</h2>',
    ]

    narrative_fields = [
        ("transcript_summary", "Transcript Summary"),
        ("story_arc", "Story Arc"),
        ("emotional_journey", "Emotional Journey"),
        ("protagonist", "Protagonist"),
        ("theme", "Theme"),
        ("visual_style", "Visual Style"),
        ("audio_style", "Audio Style"),
        ("scene_beat_map", "Scene Beat Map"),
    ]

    confidence_fields = [
        ("hook_confidence", "Hook"),
        ("narrative_confidence", "Narrative"),
        ("cta_confidence", "CTA"),
        ("pacing_confidence", "Pacing"),
        ("music_confidence", "Music"),
        ("text_overlay_confidence", "Text"),
    ]

    for p in rich + sparse:
        vid = p.get("_video_id", "?")
        error = p.get("error")
        is_rich = _is_rich_pattern(p)

        # Thumbnail
        thumb_url = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg" if platform == "youtube" else ""
        thumb_html = f'<img class="thumb" src="{esc(thumb_url)}" alt="{esc(vid)}" onerror="this.style.display=\'none\'">' if thumb_url else ""

        # Meta row
        hook = esc(p.get("hook_type", "?"))
        narrative = esc(p.get("narrative_structure", "?"))
        pacing = esc(p.get("pacing", "?"))
        music = esc(p.get("music_usage", "?"))
        cta = esc(p.get("cta_type", "?"))
        time_val = p.get("processing_time_seconds", 0)
        time_str = f"{time_val:.0f}s" if isinstance(time_val, (int, float)) else "?"

        # Confidence badges
        badges = " ".join(
            f"{label}: {_conf_badge(p.get(field, 0))}"
            for field, label in confidence_fields
            if p.get(field, 0) > 0
        )

        if error:
            parts.append(
                f'<div class="pattern-card" style="border-color: #ef9a9a;">'
                f'{thumb_html}<strong><a href="https://youtube.com/watch?v={esc(vid)}" target="_blank">{esc(vid)}</a></strong>'
                f' <span class="pattern-error">FAILED: {esc(str(error))}</span></div>'
            )
            continue

        # Build narrative detail section
        detail_items: list[str] = []
        for field, label in narrative_fields:
            val = p.get(field, "")
            if val and val not in ("", "Not available"):
                detail_items.append(f"<dt>{label}</dt><dd>{esc(val)}</dd>")

        detail_html = f'<dl class="narrative-field">{"".join(detail_items)}</dl>' if detail_items else ""

        # Wrap sparse patterns in collapsible
        open_attr = " open" if is_rich else ""
        tag_start = f"<details{open_attr}><summary>" if not is_rich else ""
        tag_end = "</summary>" if not is_rich else ""
        tag_close = "</details>" if not is_rich else ""

        parts.append(f"""\
<div class="pattern-card">
  {thumb_html}
  {tag_start}<strong><a href="https://youtube.com/watch?v={esc(vid)}" target="_blank">{esc(vid)}</a></strong>
  &mdash; {hook} | {narrative} | {pacing} | {music} | {cta} | {time_str}{tag_end}
  <div class="meta-row">{badges}</div>
  {detail_html}
  {tag_close}
  <div style="clear:both;"></div>
</div>""")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = common_argparse(
        "Generate comprehensive HTML+PDF storyboard report from a session directory."
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip downloading images (use if URLs are expired)",
    )
    args = parser.parse_args()

    session_dir: Path = args.session_dir.resolve()
    if not session_dir.is_dir():
        print(f"ERROR: Session directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Session directory: {session_dir}", file=sys.stderr)

    # ---- Load data ----
    print("Loading session data...", file=sys.stderr)

    session_md = load_markdown(session_dir / "session.md")
    findings_md = load_markdown(session_dir / "findings.md")
    findings = parse_findings(findings_md)
    session_log = load_jsonl(session_dir / "results.jsonl")

    def extract_meta(key: str) -> str:
        m = re.search(rf"^## {key}:\s*(.+)$", session_md, re.MULTILINE)
        return m.group(1).strip() if m else ""

    creator = extract_meta("Creator") or session_dir.name
    platform = extract_meta("Platform") or "unknown"

    try:
        storyboard_count = int(extract_meta("Storyboard Count") or "0")
    except ValueError:
        storyboard_count = 0
    try:
        frame_count = int(extract_meta("Frames Generated") or "0")
    except ValueError:
        frame_count = 0

    report_md_text = load_markdown(session_dir / "report.md")
    report_md_html = render_report_md_section(report_md_text)
    print(f"  Loaded report.md ({len(report_md_text)} chars)", file=sys.stderr)

    video_count = report_md_text.count("\n|") - 5 if report_md_text else 0
    frames_gen = extract_meta("Frames Generated")
    if frames_gen:
        m = re.match(r"(\d+)", frames_gen)
        if m:
            frame_count = int(m.group(1))

    # Load storyboards
    storyboards: list[dict] = []
    storyboards_dir = session_dir / "storyboards"
    if storyboards_dir.is_dir():
        for p in sorted(storyboards_dir.glob("*.json")):
            data = load_json(p)
            if data and isinstance(data, dict):
                storyboards.append(data)
    storyboards.sort(key=lambda s: s.get("story_plan_index", 999))
    print(f"  Loaded {len(storyboards)} storyboards", file=sys.stderr)

    # Load frames data
    frames_data: dict[str, dict] = {}
    frames_dir = session_dir / "frames"
    if frames_dir.is_dir():
        for p in sorted(frames_dir.glob("*.json")):
            data = load_json(p)
            if data and isinstance(data, dict):
                pid = data.get("project_id", p.stem)
                frames_data[pid] = data

    total_scenes = sum(len(f.get("scenes", f.get("frames", []))) for f in frames_data.values())
    print(f"  Loaded {len(frames_data)} frame files ({total_scenes} scenes)", file=sys.stderr)

    # Load patterns
    patterns: list[dict] = []
    patterns_dir = session_dir / "patterns"
    if patterns_dir.is_dir():
        for p in sorted(patterns_dir.glob("*.json")):
            data = load_json(p)
            if data and isinstance(data, dict):
                data["_video_id"] = p.stem
                patterns.append(data)
    print(f"  Loaded {len(patterns)} pattern extractions", file=sys.stderr)

    # Load session summary
    session_summary_raw = load_json(session_dir / "session_summary.json")
    session_summary = session_summary_raw if isinstance(session_summary_raw, dict) else None

    # Update counts from actual data if session.md had 0
    if frame_count == 0:
        frame_count = total_scenes
    if storyboard_count == 0:
        storyboard_count = len(storyboards)
    if patterns:
        video_count = len(patterns)

    # ---- Export directory ----
    export_dir = session_dir / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    # ---- Download images ----
    image_map: dict[str, Path] = {}
    if not args.skip_images:
        image_map = download_images(frames_dir, export_dir, storyboards)
        print(f"  Downloaded {len(image_map)}/{total_scenes} images", file=sys.stderr)
    else:
        print("  Skipping image downloads (--skip-images)", file=sys.stderr)

    # ---- Generate HTML ----
    print("Generating HTML report...", file=sys.stderr)

    sections: list[tuple[str, str]] = [
        ("header", render_header(creator, platform, video_count, storyboard_count, frame_count)),
    ]

    if report_md_html:
        # Full report.md available — use as main content
        sections.append(("report", report_md_html))
    else:
        # No report.md — render pipeline stages from raw data
        sections.append(("session_overview", render_session_overview(session_md)))
        sections.append(("story_plans", render_story_plans(session_dir)))

    sections.extend([
        ("gallery", render_storyboards(storyboards, frames_data, image_map)),
        ("findings", render_findings(findings)),
        ("patterns", render_pattern_extractions(patterns, platform)),
        ("session_log", render_session_log(session_log)),
    ])

    if not args.skip_logs:
        sections.append(("logs", render_logs_appendix(session_dir / "logs")))

    sections.append(("summary", render_session_summary(session_summary)))

    html_content = build_html_document(
        title=f"Storyboard Report — {creator}",
        sections=sections,
        css_extra=STORYBOARD_CSS,
    )

    html_path = export_dir / "storyboard-report.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"  HTML report: {html_path} ({html_path.stat().st_size // 1024}KB)", file=sys.stderr)

    # ---- Convert to PDF ----
    if not args.skip_pdf:
        pdf_path = export_dir / "storyboard-report.pdf"
        html_to_pdf(html_path, pdf_path)
    else:
        print("  Skipping PDF generation (--skip-pdf)", file=sys.stderr)

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
