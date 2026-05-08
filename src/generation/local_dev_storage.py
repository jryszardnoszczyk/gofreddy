"""Local-disk preview storage shim for autoresearch dev mode.

`FakeImagePreviewService` (src/generation/fake.py) needs an object with
`upload_preview(user_id, filename, bytes) -> r2_key` and
`get_preview_url(r2_key, expiry=None) -> url`. The production
`R2GenerationStorage` requires R2/S3 credentials we don't carry in the
autoresearch test environment.

This shim writes preview bytes to a local directory under ``$TMPDIR`` and
returns ``file://`` URLs. Sufficient for storyboard agents whose pipeline
just needs preview_image_url to be a non-empty string for downstream
pipeline progression — they don't actually fetch the bytes.

Surfaced 2026-05-08 storyboard frame-generation: agents got 403 (tier gate),
then 503 ``preview_unavailable`` once tier was unlocked, because
``app.state.image_preview_service = None``. Wiring the real
``ImagePreviewService`` requires a Gemini/Grok/Fal client + R2 storage.
This shim unblocks the lane without those dependencies.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import UUID


class LocalDevPreviewStorage:
    """Writes preview bytes to local disk; returns file:// URLs.

    Drop-in replacement for ``R2GenerationStorage`` in
    ``FakeImagePreviewService``. Production must use the real R2 storage.
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(tempfile.gettempdir()) / "gofreddy-previews"
        self._root.mkdir(parents=True, exist_ok=True)

    async def upload_preview(self, user_id: UUID, filename: str, data: bytes) -> str:
        user_dir = self._root / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        target = user_dir / filename
        target.write_bytes(data)
        return str(target)

    async def get_preview_url(self, r2_key: str, expiry: int = 3600) -> str:
        del expiry  # local file URLs don't expire
        return f"file://{r2_key}"

    async def download_preview(self, r2_key: str) -> bytes:
        return Path(r2_key).read_bytes()
