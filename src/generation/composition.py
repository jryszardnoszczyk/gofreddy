"""FFmpeg-based video composition service."""

import asyncio
import logging
import os
import re
import tempfile
import unicodedata
from pathlib import Path

from .caption_presets import get_preset
from .exceptions import GenerationError, GenerationTimeoutError
from .models import CAPTION_SAFE_RE, Caption, CaptionStyle, CompositionSpec

logger = logging.getLogger(__name__)

_FFMPEG_TIMEOUT_SECONDS = 240  # 4 min for composition (raised for 10-scene)
_FFPROBE_TIMEOUT_SECONDS = 10

def _resolve_dimensions(resolution: str, aspect_ratio: str) -> tuple[int, int]:
    """Compute (width, height) from resolution + aspect ratio, rounded to even for FFmpeg."""
    short_edge = {"480p": 480, "720p": 720, "1080p": 1080}.get(resolution, 720)
    if aspect_ratio == "9:16":
        return (short_edge, round(short_edge * 16 / 9 / 2) * 2)  # portrait
    elif aspect_ratio == "1:1":
        return (short_edge, short_edge)  # square
    else:  # 16:9 landscape (default — also fallback for unknown values)
        return (round(short_edge * 16 / 9 / 2) * 2, short_edge)

# Caption sanitization — defense-in-depth against FFmpeg injection.
# Backslash MUST NOT be allowed (newline, filter separator in FFmpeg).
_CAPTION_SAFE_RE = CAPTION_SAFE_RE  # unified import from models

# ASS alignment values for subtitle positioning
_ALIGNMENT_MAP: dict[str, int] = {
    "bottom": 2,    # bottom-center
    "top": 6,       # top-center
    "center": 10,   # middle-center (SSA/ASS v4+)
}


def _build_force_style(style: CaptionStyle, alignment: int | None = None) -> str:
    """Build an ASS force_style string from a CaptionStyle instance."""
    parts = [
        f"FontName={style.font_name}",
        f"FontSize={style.font_size}",
        f"PrimaryColour={style.primary_colour}",
        f"OutlineColour={style.outline_colour}",
        f"BackColour={style.back_colour}",
        f"BorderStyle={style.border_style}",
        f"Outline={style.outline_width}",
        f"Shadow={style.shadow_depth}",
        f"Bold={int(style.bold)}",
        f"Italic={int(style.italic)}",
        f"Alignment={alignment if alignment is not None else style.alignment}",
        f"MarginV={style.margin_v}",
    ]
    return ",".join(parts)


def _sanitize_caption(text: str) -> str:
    """Sanitize caption text for FFmpeg subtitles. Strips disallowed chars."""
    text = unicodedata.normalize("NFKC", text)
    if not _CAPTION_SAFE_RE.match(text):
        text = re.sub(r"[\x00-\x1f\x7f\\;%{}\[\]`$|#]", "", text)
    # Escape FFmpeg special characters for SRT format
    for ch in ("'", "%", ":", "[", "]", ";"):
        text = text.replace(ch, f"\\{ch}")
    return text


def _generate_srt(captions: list[Caption], output_path: Path) -> None:
    """Generate an SRT subtitle file from captions."""
    # Use O_EXCL to prevent symlink pre-plant attacks on shared /tmp
    fd = os.open(str(output_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for i, cap in enumerate(captions, 1):
                start_h = int(cap.start_seconds // 3600)
                start_m = int((cap.start_seconds % 3600) // 60)
                start_s = int(cap.start_seconds % 60)
                start_ms = int((cap.start_seconds % 1) * 1000)

                end_h = int(cap.end_seconds // 3600)
                end_m = int((cap.end_seconds % 3600) // 60)
                end_s = int(cap.end_seconds % 60)
                end_ms = int((cap.end_seconds % 1) * 1000)

                safe_text = _sanitize_caption(cap.text)
                f.write(f"{i}\n")
                f.write(f"{start_h:02d}:{start_m:02d}:{start_s:02d},{start_ms:03d} --> ")
                f.write(f"{end_h:02d}:{end_m:02d}:{end_s:02d},{end_ms:03d}\n")
                f.write(f"{safe_text}\n\n")
    except Exception:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


async def _run_ffmpeg(args: list[str], timeout: float) -> tuple[bytes, bytes]:
    """Run FFmpeg subprocess with two-phase kill on timeout."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        # Two-phase kill: terminate -> wait -> kill -> reap
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            proc.kill()
        await proc.wait()  # MUST reap zombie
        raise GenerationTimeoutError("FFmpeg timed out")

    if proc.returncode != 0:
        stderr_tail = stderr.decode(errors="replace")[-500:]
        raise GenerationError(f"FFmpeg failed (rc={proc.returncode}): {stderr_tail}")
    return stdout, stderr


async def _run_ffprobe(args: list[str]) -> bytes:
    """Run ffprobe with timeout."""
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=_FFPROBE_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            proc.kill()
        await proc.wait()
        raise GenerationTimeoutError("ffprobe timed out")

    if proc.returncode != 0:
        raise GenerationError(f"ffprobe failed: {stderr.decode(errors='replace')[-200:]}")
    return stdout


class CompositionService:
    """FFmpeg-based video composition service."""

    async def _has_audio_stream(self, video_path: Path) -> bool:
        """Check if video file has an audio stream."""
        stdout = await _run_ffprobe([
            "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0", str(video_path),
        ])
        return bool(stdout.decode().strip())

    async def _probe_clip(self, video_path: Path) -> tuple[bool, float]:
        """Probe a clip for audio presence AND actual duration."""
        # Audio check
        audio_out = await _run_ffprobe([
            "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0", str(video_path),
        ])
        has_audio = bool(audio_out.decode().strip())

        # Duration check — must use VIDEO stream duration, not format duration.
        # format=duration returns the longest stream (often audio), which causes
        # xfade offsets to exceed the actual video length → black frames.
        dur_out = await _run_ffprobe([
            "-v", "error",
            "-select_streams", "v",
            "-show_entries", "stream=duration",
            "-of", "csv=p=0", str(video_path),
        ])
        try:
            duration = float(dur_out.decode().strip())
        except (ValueError, TypeError):
            duration = 5.0  # fallback

        return has_audio, duration

    async def compose(
        self,
        cadre_paths: list[Path],
        spec: CompositionSpec,
        output_path: Path,
        *,
        narration_path: Path | None = None,
        music_path: Path | None = None,
    ) -> Path:
        """Compose multiple cadre videos into a single output with transitions and captions."""
        if len(cadre_paths) < 1:
            raise GenerationError("At least one cadre path required")

        w, h = _resolve_dimensions(spec.resolution, spec.aspect_ratio)
        fade_dur = 0.5

        if len(cadre_paths) == 1:
            # Single cadre — just normalize and add captions
            return await self._compose_single(
                cadre_paths[0], spec, output_path, w, h,
                narration_path=narration_path, music_path=music_path,
            )

        # Probe each input for audio streams AND actual duration (concurrent)
        probe_results = await asyncio.gather(
            *[self._probe_clip(p) for p in cadre_paths]
        )
        has_audio = [r[0] for r in probe_results]
        # Use ACTUAL clip durations for xfade offsets — spec durations can differ
        # from what Grok actually generated, causing black frames in composition
        durations = [r[1] for r in probe_results]
        any_audio = any(has_audio)

        # Build FFmpeg filter graph for multi-cadre xfade
        args: list[str] = ["-y"]  # overwrite output

        # Add all inputs
        for p in cadre_paths:
            args.extend(["-i", str(p)])

        # Build filter complex
        n = len(cadre_paths)
        filter_parts: list[str] = []

        # Normalize each input (video + audio)
        for i in range(n):
            filter_parts.append(
                f"[{i}:v]settb=AVTB,setsar=sar=1,fps=30,scale={w}:{h},"
                f"format=yuv420p,pad=ceil(iw/2)*2:ceil(ih/2)*2[v{i}]"
            )
            if any_audio:
                if has_audio[i]:
                    # loudnorm (EBU R128) eliminates volume jumps between cadres
                    filter_parts.append(
                        f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,"
                        f"loudnorm=I=-14:TP=-1.5:LRA=11[a{i}]"
                    )
                else:
                    # Generate silent audio for clips without audio streams
                    clip_dur = durations[i] if i < len(durations) else 5
                    filter_parts.append(
                        f"anullsrc=r=44100:cl=stereo[sa{i}]"
                    )
                    filter_parts.append(
                        f"[sa{i}]atrim=duration={clip_dur}[a{i}]"
                    )

        # xfade chaining
        transition = spec.cadres[0].transition if spec.cadres else "fade"
        # Map model transitions to FFmpeg xfade transitions
        xfade_transition = {
            "fade": "fade",
            "cut": "fade",  # cut = very short fade
            "dissolve": "fade",
            "wipe": "wipeleft",
        }.get(transition, "fade")

        # Video xfade chain
        prev_v = "v0"
        cumulative = 0.0
        for i in range(n - 1):
            cumulative += durations[i]
            offset = cumulative - fade_dur * (i + 1)
            out_label = f"xf{i}" if i < n - 2 else "vout"
            filter_parts.append(
                f"[{prev_v}][v{i+1}]xfade=transition={xfade_transition}:"
                f"duration={fade_dur}:offset={offset}[{out_label}]"
            )
            prev_v = out_label

        # Audio crossfade chain (only if any input has audio)
        if any_audio:
            prev_a = "a0"
            for i in range(n - 1):
                out_label = f"af{i}" if i < n - 2 else "aout"
                filter_parts.append(
                    f"[{prev_a}][a{i+1}]acrossfade=d={fade_dur}:c1=tri:c2=tri[{out_label}]"
                )
                prev_a = out_label

        # --- Narration + Music mixing (PR-100) ---
        audio_out_label = "aout" if any_audio else None
        extra_input_idx = n  # Next available input index

        if narration_path:
            if not narration_path.resolve().is_file():
                raise GenerationError(f"Narration file not found: {narration_path}")
            args.extend(["-i", str(narration_path)])
            narr_idx = extra_input_idx
            extra_input_idx += 1
            # Normalize narration to -14 LUFS (broadcast speech standard)
            filter_parts.append(
                f"[{narr_idx}:a]aresample=44100,aformat=channel_layouts=stereo,"
                f"loudnorm=I=-14:TP=-1.5:LRA=11[narr]"
            )

        if music_path:
            if not music_path.resolve().is_file():
                raise GenerationError(f"Music file not found: {music_path}")
            args.extend(["-i", str(music_path)])
            mus_idx = extra_input_idx
            extra_input_idx += 1
            # Background music at -30 LUFS, loop + trim to video duration, fade out last 2s
            total_dur = sum(durations) - fade_dur * (n - 1) if n > 1 else durations[0] if durations else 30
            filter_parts.append(
                f"[{mus_idx}:a]aloop=loop=-1:size=2e+09,atrim=duration={total_dur},"
                f"aresample=44100,aformat=channel_layouts=stereo,"
                f"loudnorm=I=-30:TP=-1.5:LRA=11,"
                f"afade=t=out:st={max(0, total_dur - 2)}:d=2[bgm]"
            )

        # Mix audio sources based on what's available
        if narration_path and music_path and audio_out_label:
            # 3-source: cadre (-20 LUFS) + narration (-14) + music (-30)
            # Re-normalize cadre audio to -20 LUFS (ducked for narration)
            filter_parts.append(
                f"[{audio_out_label}]loudnorm=I=-20:TP=-1.5:LRA=11[cadre_ducked]"
            )
            filter_parts.append(
                "[cadre_ducked][narr][bgm]amix=inputs=3:duration=first[amixed]"
            )
            audio_out_label = "amixed"
        elif narration_path and music_path:
            # No cadre audio, just narration + music
            filter_parts.append(
                "[narr][bgm]amix=inputs=2:duration=first[amixed]"
            )
            audio_out_label = "amixed"
        elif narration_path and audio_out_label:
            # Cadre audio + narration (duck cadre)
            filter_parts.append(
                f"[{audio_out_label}]loudnorm=I=-20:TP=-1.5:LRA=11[cadre_ducked]"
            )
            filter_parts.append(
                "[cadre_ducked][narr]amix=inputs=2:duration=first[amixed]"
            )
            audio_out_label = "amixed"
        elif narration_path:
            audio_out_label = "narr"
        elif music_path and audio_out_label:
            filter_parts.append(
                f"[{audio_out_label}][bgm]amix=inputs=2:duration=first[amixed]"
            )
            audio_out_label = "amixed"
        elif music_path:
            audio_out_label = "bgm"

        # Captions — apply after xfade via subtitles filter
        srt_path = None
        final_v = "vout"
        if spec.captions:
            fd, srt_tmp = tempfile.mkstemp(suffix=".srt", prefix="gen-caption-")
            os.close(fd)
            srt_path = Path(srt_tmp)
            srt_path.unlink()  # Remove so _generate_srt can use O_EXCL
            _generate_srt(spec.captions, srt_path)
            # Determine alignment from first caption
            alignment = _ALIGNMENT_MAP.get(spec.captions[0].position, 2)
            style = get_preset(spec.caption_preset)
            force_style = _build_force_style(style, alignment=alignment)
            srt_escaped = str(srt_path).replace(":", "\\:").replace("'", "\\'")
            filter_parts.append(
                f"[vout]subtitles='{srt_escaped}':force_style='{force_style}'[vcap]"
            )
            final_v = "vcap"

        filter_complex = ";".join(filter_parts)
        args.extend([
            "-filter_complex", filter_complex,
            "-map", f"[{final_v}]",
        ])
        final_audio = audio_out_label or ("aout" if any_audio else None)
        if final_audio:
            args.extend(["-map", f"[{final_audio}]", "-c:a", "aac", "-b:a", "128k"])
        args.extend([
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            "-threads", "2",
            str(output_path),
        ])

        try:
            await _run_ffmpeg(args, _FFMPEG_TIMEOUT_SECONDS)
        finally:
            if srt_path:
                srt_path.unlink(missing_ok=True)

        # Validate output
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise GenerationError("FFmpeg produced zero-byte output")

        return output_path

    async def _compose_single(
        self,
        cadre_path: Path,
        spec: CompositionSpec,
        output_path: Path,
        w: int,
        h: int,
        *,
        narration_path: Path | None = None,
        music_path: Path | None = None,
    ) -> Path:
        """Handle single-cadre composition (normalize + optional captions)."""
        has_audio = await self._has_audio_stream(cadre_path)
        args = ["-y", "-i", str(cadre_path)]

        filter_parts = [
            f"[0:v]settb=AVTB,setsar=sar=1,fps=30,scale={w}:{h},"
            f"format=yuv420p,pad=ceil(iw/2)*2:ceil(ih/2)*2[vn]"
        ]

        # --- Narration + Music mixing for single cadre (PR-100) ---
        audio_out_label: str | None = None
        extra_input_idx = 1  # Input 0 is the cadre

        if narration_path or music_path:
            # When mixing, route cadre audio through filter graph
            if has_audio:
                filter_parts.append(
                    "[0:a]aresample=44100,aformat=channel_layouts=stereo,"
                    "loudnorm=I=-14:TP=-1.5:LRA=11[a0]"
                )
                audio_out_label = "a0"

            if narration_path:
                if not narration_path.resolve().is_file():
                    raise GenerationError(f"Narration file not found: {narration_path}")
                args.extend(["-i", str(narration_path)])
                narr_idx = extra_input_idx
                extra_input_idx += 1
                filter_parts.append(
                    f"[{narr_idx}:a]aresample=44100,aformat=channel_layouts=stereo,"
                    f"loudnorm=I=-14:TP=-1.5:LRA=11[narr]"
                )

            if music_path:
                if not music_path.resolve().is_file():
                    raise GenerationError(f"Music file not found: {music_path}")
                args.extend(["-i", str(music_path)])
                mus_idx = extra_input_idx
                extra_input_idx += 1
                # Probe cadre duration for music loop/trim
                _, cadre_dur = await self._probe_clip(cadre_path)
                filter_parts.append(
                    f"[{mus_idx}:a]aloop=loop=-1:size=2e+09,atrim=duration={cadre_dur},"
                    f"aresample=44100,aformat=channel_layouts=stereo,"
                    f"loudnorm=I=-30:TP=-1.5:LRA=11,"
                    f"afade=t=out:st={max(0, cadre_dur - 2)}:d=2[bgm]"
                )

            # Mix audio sources
            if narration_path and music_path and audio_out_label:
                filter_parts.append(
                    f"[{audio_out_label}]loudnorm=I=-20:TP=-1.5:LRA=11[cadre_ducked]"
                )
                filter_parts.append(
                    "[cadre_ducked][narr][bgm]amix=inputs=3:duration=first[amixed]"
                )
                audio_out_label = "amixed"
            elif narration_path and music_path:
                filter_parts.append(
                    "[narr][bgm]amix=inputs=2:duration=first[amixed]"
                )
                audio_out_label = "amixed"
            elif narration_path and audio_out_label:
                filter_parts.append(
                    f"[{audio_out_label}]loudnorm=I=-20:TP=-1.5:LRA=11[cadre_ducked]"
                )
                filter_parts.append(
                    "[cadre_ducked][narr]amix=inputs=2:duration=first[amixed]"
                )
                audio_out_label = "amixed"
            elif narration_path:
                audio_out_label = "narr"
            elif music_path and audio_out_label:
                filter_parts.append(
                    f"[{audio_out_label}][bgm]amix=inputs=2:duration=first[amixed]"
                )
                audio_out_label = "amixed"
            elif music_path:
                audio_out_label = "bgm"

        srt_path = None
        final_v = "vn"
        if spec.captions:
            fd, srt_tmp = tempfile.mkstemp(suffix=".srt", prefix="gen-caption-")
            os.close(fd)
            srt_path = Path(srt_tmp)
            srt_path.unlink()  # Remove so _generate_srt can use O_EXCL
            _generate_srt(spec.captions, srt_path)
            alignment = _ALIGNMENT_MAP.get(spec.captions[0].position, 2)
            style = get_preset(spec.caption_preset)
            force_style = _build_force_style(style, alignment=alignment)
            srt_escaped = str(srt_path).replace(":", "\\:").replace("'", "\\'")
            filter_parts.append(
                f"[vn]subtitles='{srt_escaped}':force_style='{force_style}'[vcap]"
            )
            final_v = "vcap"

        filter_complex = ";".join(filter_parts)
        args.extend([
            "-filter_complex", filter_complex,
            "-map", f"[{final_v}]",
        ])
        if audio_out_label:
            # Narration/music mixing routed through filter graph
            args.extend(["-map", f"[{audio_out_label}]", "-c:a", "aac", "-b:a", "128k"])
        elif has_audio:
            args.extend(["-map", "0:a", "-c:a", "aac", "-b:a", "128k"])
        args.extend([
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            "-threads", "2",
            str(output_path),
        ])

        try:
            await _run_ffmpeg(args, _FFMPEG_TIMEOUT_SECONDS)
        finally:
            if srt_path:
                srt_path.unlink(missing_ok=True)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise GenerationError("FFmpeg produced zero-byte output")

        return output_path

    async def extract_final_frame(self, video_path: Path, output_path: Path) -> Path:
        """Extract the final frame of a video as PNG."""
        args = [
            "-sseof", "-0.1",
            "-i", str(video_path),
            "-frames:v", "1",
            "-update", "1",
            "-q:v", "2",
            "-y",
            str(output_path),
        ]
        await _run_ffmpeg(args, _FFPROBE_TIMEOUT_SECONDS)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise GenerationError("Failed to extract final frame")

        return output_path

    async def validate_output(self, video_path: Path) -> float:
        """Validate video and return duration in seconds."""
        if not video_path.exists():
            raise GenerationError("Video file does not exist")
        if video_path.stat().st_size == 0:
            raise GenerationError("Video file is zero bytes")

        stdout = await _run_ffprobe([
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(video_path),
        ])

        duration_str = stdout.decode().strip()
        try:
            duration = float(duration_str)
        except (ValueError, TypeError):
            raise GenerationError(f"Could not parse duration: {duration_str!r}")

        if duration <= 0:
            raise GenerationError(f"Invalid duration: {duration}")

        return duration
