"""YouTube video fetcher using yt-dlp."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace as dataclass_replace
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from ..common.enums import Platform
from .base import BaseFetcher
from .exceptions import CreatorNotFoundError, DownloadError, VideoUnavailableError
from .models import VideoResult, VideoStats

logger = logging.getLogger(__name__)

# Pre-compiled regex for VTT HTML tag stripping
_VTT_TAG_RE = re.compile(r"<[^>]+>")

if TYPE_CHECKING:
    from ..storage import R2VideoStorage
    from .config import FetcherSettings


def _backfill_video_metadata(videos: list[VideoStats]) -> list[VideoStats]:
    """Enrich VideoStats entries that are missing posted_at or duration_seconds.

    Uses a non-flat ``extract_info`` call per video (download=False) so yt-dlp
    returns the full metadata including ``upload_date`` and ``duration``.
    Only runs on the already-limited top-N list to avoid unnecessary API calls.
    Errors on individual videos are logged and skipped — the original entry is
    kept as-is.
    """
    enriched: list[VideoStats] = []
    for vs in videos:
        if vs.posted_at is not None and vs.duration_seconds is not None:
            enriched.append(vs)
            continue

        url = f"https://www.youtube.com/watch?v={vs.video_id}"
        try:
            with YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as ydl:
                info = ydl.extract_info(url, download=False) or {}

            updates: dict[str, Any] = {}

            # Backfill posted_at from upload_date (YYYYMMDD string)
            if vs.posted_at is None:
                upload_date = info.get("upload_date")
                if isinstance(upload_date, str) and len(upload_date) == 8:
                    try:
                        updates["posted_at"] = datetime.strptime(
                            upload_date, "%Y%m%d"
                        ).replace(tzinfo=timezone.utc)
                    except ValueError:
                        pass

            # Backfill duration_seconds from duration (float/int seconds)
            if vs.duration_seconds is None:
                raw_dur = info.get("duration")
                if raw_dur is not None:
                    try:
                        updates["duration_seconds"] = int(raw_dur)
                    except (TypeError, ValueError):
                        pass

            if updates:
                enriched.append(dataclass_replace(vs, **updates))
            else:
                enriched.append(vs)

        except Exception:
            logger.warning(
                "youtube_backfill_metadata_failed: %s — keeping original entry",
                vs.video_id,
                exc_info=True,
            )
            enriched.append(vs)

    return enriched


class YouTubeFetcher(BaseFetcher):
    """Fetch YouTube videos via yt-dlp."""

    def __init__(
        self,
        storage: R2VideoStorage,
        settings: FetcherSettings | None = None,
    ) -> None:
        super().__init__(storage, settings)
        # yt-dlp is I/O-bound (network), not CPU-bound; safe to use more threads
        max_workers = min(10, os.cpu_count() or 4)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    @property
    def platform(self) -> Platform:
        return Platform.YOUTUBE

    async def __aexit__(self, *args) -> None:
        await super().__aexit__(*args)
        self._executor.shutdown(wait=False)

    def _download_sync(self, video_id: str, output_dir: Path) -> tuple[Path, dict[str, Any]]:
        """Synchronous yt-dlp download - runs in thread pool."""
        url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "merge_output_format": "mp4",
            "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "subtitlesformat": "vtt",
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
            # Use android_vr client to bypass YouTube SABR streaming enforcement
            # (yt-dlp#12482) which blocks direct downloads on web/web_safari clients.
            "extractor_args": {"youtube": {"player_client": ["android_vr"]}},
            # Enable installed JS runtimes (yt-dlp only enables deno by default).
            "js_runtimes": {"node": {}, "bun": {}},
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = output_dir / f"{video_id}.mp4"
                return video_path, info

        except YtDlpDownloadError as e:
            error_str = str(e).lower()
            if "video unavailable" in error_str or "private video" in error_str:
                raise VideoUnavailableError(Platform.YOUTUBE, video_id) from e
            if "sign in" in error_str or "age" in error_str:
                raise VideoUnavailableError(Platform.YOUTUBE, video_id) from e
            # If the video itself downloaded but subtitles/post-processing failed,
            # proceed with video-only analysis (transcript will be None).
            video_path = output_dir / f"{video_id}.mp4"
            if video_path.exists() and video_path.stat().st_size > 0:
                logger.warning(
                    "youtube_partial_download: %s (video OK, subtitle/post-proc failed): %s",
                    video_id, str(e)[:200],
                )
                return video_path, {}

            # Subtitle-specific 429: yt-dlp aborts entire download (yt-dlp#14153).
            # Retry without subtitles so the video still gets analyzed.
            if "subtitle" in error_str:
                logger.warning(
                    "youtube_subtitle_429_retry: %s — retrying without subtitles",
                    video_id,
                )
                no_sub_opts = {
                    k: v for k, v in ydl_opts.items()
                    if k not in ("writeautomaticsub", "subtitleslangs", "subtitlesformat")
                }
                try:
                    with YoutubeDL(no_sub_opts) as ydl2:
                        info = ydl2.extract_info(url, download=True)
                        video_path = output_dir / f"{video_id}.mp4"
                        return video_path, info or {}
                except YtDlpDownloadError as e2:
                    raise DownloadError(Platform.YOUTUBE, video_id, str(e2)) from e2

            raise DownloadError(Platform.YOUTUBE, video_id, str(e)) from e

    async def _fetch_and_store(self, video_id: str) -> VideoResult:
        """Fetch YouTube video and store to R2."""
        loop = asyncio.get_running_loop()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Run yt-dlp in thread pool
            video_path, info = await loop.run_in_executor(
                self._executor,
                self._download_sync,
                video_id,
                temp_path,
            )
            if not isinstance(info, dict):
                info = {}

            if not video_path.exists():
                raise DownloadError(
                    self.platform, video_id, "Video file not created"
                )

            # Get file size before upload
            file_size = video_path.stat().st_size

            # Upload to R2 using file path (matches R2VideoStorage interface)
            await self.storage.upload(
                local_path=video_path,
                platform=self.platform,
                video_id=video_id,
            )

            # Parse upload date
            upload_date = info.get("upload_date")
            posted_at = None
            if upload_date:
                try:
                    posted_at = datetime.strptime(
                        upload_date, "%Y%m%d"
                    ).replace(tzinfo=timezone.utc)
                except ValueError:
                    pass

            # Extract VTT transcript before TemporaryDirectory exits
            transcript_text = self._extract_vtt_transcript(temp_path, video_id)

            # Extract thumbnail (yt-dlp returns list of thumbnail dicts)
            thumbnails = info.get("thumbnails")
            thumbnail_url = None
            if isinstance(thumbnails, list) and thumbnails:
                # Last thumbnail is usually highest resolution
                thumbnail_url = thumbnails[-1].get("url") if isinstance(thumbnails[-1], dict) else None

            # Extract tags and mentions from description
            raw_tags = info.get("tags")
            hashtags = [t for t in raw_tags if isinstance(t, str)][:20] if isinstance(raw_tags, list) else None
            desc = info.get("description") or ""
            mentions = re.findall(r"@([\w.]+)", desc)[:20] if desc else None

            return VideoResult(
                video_id=video_id,
                platform=self.platform,
                r2_key=f"videos/youtube/{video_id}.mp4",
                title=info.get("title"),
                description=desc or None,
                creator_username=info.get("uploader_id") or info.get("channel"),
                creator_id=info.get("channel_id"),
                duration_seconds=int(info.get("duration", 0)),
                view_count=info.get("view_count"),
                like_count=info.get("like_count"),
                comment_count=info.get("comment_count"),
                posted_at=posted_at,
                fetched_at=datetime.now(timezone.utc),
                file_size_bytes=file_size,
                transcript_text=transcript_text,
                thumbnail_url=thumbnail_url,
                hashtags=hashtags or None,
                mentions=mentions or None,
            )

    def _extract_vtt_transcript(self, output_dir: Path, video_id: str) -> str | None:
        """Extract plain text from downloaded VTT subtitle file."""
        vtt_patterns = [
            output_dir / f"{video_id}.en.vtt",
        ]
        for vtt_path in vtt_patterns:
            if vtt_path.exists():
                return self._parse_vtt_to_text(vtt_path)
        # Glob fallback for unexpected naming
        for vtt_file in output_dir.glob(f"{video_id}*.vtt"):
            return self._parse_vtt_to_text(vtt_file)
        return None

    @staticmethod
    def _parse_vtt_to_text(vtt_path: Path) -> str | None:
        """Parse VTT file to plain text, removing timestamps and tags."""
        # Guard against oversized files (typical VTT is 10-100KB)
        if vtt_path.stat().st_size > 1_000_000:
            return None
        text = vtt_path.read_text(encoding="utf-8", errors="replace")
        lines: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            # Skip header, timestamps, empty lines
            if not line or line.startswith("WEBVTT") or "-->" in line:
                continue
            # Skip numeric cue IDs
            if line.isdigit():
                continue
            clean = _VTT_TAG_RE.sub("", line)
            if clean.strip():
                lines.append(clean.strip())
        # Deduplicate consecutive identical lines (VTT often repeats)
        deduped: list[str] = []
        for line in lines:
            if not deduped or deduped[-1] != line:
                deduped.append(line)
        result = " ".join(deduped)
        return result if result.strip() else None

    async def _list_creator_videos(
        self, handle: str, limit: int
    ) -> list[VideoStats]:
        """List video IDs from a YouTube channel (regular videos + Shorts)."""
        loop = asyncio.get_running_loop()

        def _extract_tab(url: str, max_entries: int) -> list[dict]:
            ydl_opts = {
                "quiet": True,
                "extract_flat": "in_playlist",
                "playlistend": max_entries,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get("entries", [])

        def extract_all_sync():
            # Fetch /shorts first (primary source), then /videos as supplement
            shorts_url = f"https://www.youtube.com/@{handle}/shorts"
            videos_url = f"https://www.youtube.com/@{handle}/videos"

            all_entries = []
            try:
                all_entries.extend(_extract_tab(shorts_url, limit))
            except Exception:
                pass  # Shorts tab may not exist
            try:
                all_entries.extend(_extract_tab(videos_url, limit))
            except Exception:
                pass  # Videos tab may fail; shorts alone are fine

            if not all_entries:
                raise CreatorNotFoundError(self.platform, handle)

            # Deduplicate by video ID, preserving order
            seen: set[str] = set()
            results = []
            for entry in all_entries:
                vid = entry.get("id")
                if not vid or vid in seen:
                    continue
                seen.add(vid)
                raw_ts = entry.get("timestamp")
                posted_at = datetime.fromtimestamp(raw_ts, tz=timezone.utc) if isinstance(raw_ts, (int, float)) else None
                raw_dur = entry.get("duration")
                results.append(VideoStats(
                    video_id=vid,
                    play_count=entry.get("view_count"),
                    like_count=entry.get("like_count"),
                    comment_count=entry.get("comment_count"),
                    posted_at=posted_at,
                    title=entry.get("title") or None,
                    duration_seconds=int(raw_dur) if raw_dur is not None else None,
                ))
            # Sort by play_count descending so limit cuts the least popular
            results.sort(key=lambda v: v.play_count or 0, reverse=True)
            top_results = results[:limit]

            # Second pass: extract_flat=True omits upload_date and duration
            # for most videos.  Backfill from per-video metadata on the
            # already-limited top-N list so we never over-fetch.
            top_results = _backfill_video_metadata(top_results)

            return top_results

        try:
            return await loop.run_in_executor(
                self._executor, extract_all_sync
            )
        except CreatorNotFoundError:
            raise
        except Exception as e:
            logger.warning(
                "youtube_list_creator_videos_failed: handle=%s — wrapping as CreatorNotFoundError",
                handle,
                exc_info=True,
            )
            raise CreatorNotFoundError(self.platform, handle) from e

    # ─── Search Methods (PR-012) ───────────────────────────────────────────────

    async def search(
        self,
        query: str,
        max_results: int = 50,
        content_format: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search YouTube videos including Shorts.

        Args:
            query: Search query string
            max_results: Maximum number of results (default 50)
            content_format: "short" for Shorts only, "long" for regular only,
                          None/other for both interleaved

        Returns:
            List of video info dictionaries
        """
        loop = asyncio.get_running_loop()

        def search_sync() -> list[dict[str, Any]]:
            base_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
            }

            # Cap per-source at 50 to avoid slow pagination on large limits.
            # After dedup + interleave we still return up to max_results.
            per_source = min(max_results, 50)

            entries: list[dict[str, Any]] = []
            shorts_entries: list[dict[str, Any]] = []

            # Regular search (skip when user wants short-form only)
            if content_format != "short":
                search_url = f"ytsearch{per_source}:{query}"
                with YoutubeDL(base_opts) as ydl:
                    info = ydl.extract_info(search_url, download=False)
                entries = info.get("entries", []) if info else []

            # Shorts search (skip when user wants long-form only)
            if content_format != "long":
                shorts_url = f"https://www.youtube.com/results?search_query={query}&sp=EgIYAQ%3D%3D"
                shorts_opts = {**base_opts, "playlistend": per_source}
                with YoutubeDL(shorts_opts) as ydl:
                    shorts_info = ydl.extract_info(shorts_url, download=False)
                shorts_entries = shorts_info.get("entries", []) if shorts_info else []

            # Interleave regular and Shorts, then deduplicate by video ID.
            # Interleaving ensures truncation to max_results keeps a mix
            # of both types instead of only regular videos.
            from itertools import zip_longest
            interleaved = [
                e for pair in zip_longest(entries, shorts_entries)
                for e in pair if e is not None
            ]
            seen_ids: set[str] = set()
            results: list[dict[str, Any]] = []
            for entry in interleaved:
                if not isinstance(entry, dict) or not entry.get("id"):
                    continue
                vid = entry["id"]
                if vid in seen_ids:
                    continue
                seen_ids.add(vid)
                results.append({
                    "id": vid,
                    "title": entry.get("title"),
                    "description": entry.get("description"),
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "uploader_id": entry.get("uploader_id"),
                    "channel": entry.get("channel"),
                    "channel_id": entry.get("channel_id"),
                    "view_count": entry.get("view_count"),
                    "like_count": entry.get("like_count"),
                    "comment_count": entry.get("comment_count"),
                    "duration": entry.get("duration"),
                    "upload_date": entry.get("upload_date"),
                    "timestamp": entry.get("timestamp"),
                    "thumbnails": entry.get("thumbnails"),
                    "tags": entry.get("tags"),
                })
            return results[:max_results]

        return await loop.run_in_executor(self._executor, search_sync)
