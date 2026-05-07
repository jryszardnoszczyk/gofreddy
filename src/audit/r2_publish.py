"""R2 publish helper — uploads audit deliverable to gofreddy-audits bucket.

Sync API on purpose (publish is a one-shot CLI op, not on the audit hot
path). Uses boto3's S3-compatible client against Cloudflare R2's
endpoint; auth via env vars.

Environment (all required for upload to fire — graceful no-op if any
missing, returning empty string):
- ``R2_ACCESS_KEY_ID``
- ``R2_SECRET_ACCESS_KEY``
- ``R2_ACCOUNT_ID``       (used to build endpoint URL)
- ``R2_AUDITS_BUCKET``    (default ``gofreddy-audits``)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def upload_audit_dir(local_dir: Path, slug: str, *, dry_run: bool = False) -> str:
    """Upload every file under ``local_dir`` to R2 under prefix ``<slug>/``.

    Returns the public URL on success (``reports.gofreddy.ai/<slug>/``),
    empty string when env is incomplete or the upload partially fails.
    Best-effort — does not raise.
    """
    public_base = os.environ.get(
        "R2_PUBLIC_BASE_URL", "https://reports.gofreddy.ai"
    ).rstrip("/")
    public_url = f"{public_base}/{slug}/"

    if dry_run:
        logger.info("dry-run upload of %s → %s", local_dir, public_url)
        return public_url

    access_key = os.environ.get("R2_ACCESS_KEY_ID", "").strip()
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY", "").strip()
    account_id = os.environ.get("R2_ACCOUNT_ID", "").strip()
    bucket = os.environ.get("R2_AUDITS_BUCKET", "gofreddy-audits")

    if not (access_key and secret_key and account_id):
        logger.info("R2 credentials incomplete — skipping upload to %s", public_url)
        return ""

    try:
        import boto3  # type: ignore[import-untyped]
    except ImportError:
        logger.info("boto3 not installed — skipping R2 upload")
        return ""

    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )

    uploaded = 0
    for path in sorted(local_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(local_dir)
        key = f"{slug}/{rel.as_posix()}"
        try:
            client.upload_file(
                str(path), bucket, key,
                ExtraArgs={"ContentType": _content_type(path.name)},
            )
            uploaded += 1
        except Exception:
            logger.exception("R2 upload failed for %s", key)
            return ""
    logger.info("uploaded %d files to %s/%s", uploaded, bucket, slug)
    return public_url


def _content_type(filename: str) -> str:
    if filename.endswith(".html"):
        return "text/html; charset=utf-8"
    if filename.endswith(".pdf"):
        return "application/pdf"
    if filename.endswith(".json"):
        return "application/json"
    if filename.endswith(".css"):
        return "text/css"
    if filename.endswith(".js"):
        return "application/javascript"
    if filename.endswith(".png"):
        return "image/png"
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        return "image/jpeg"
    if filename.endswith(".svg"):
        return "image/svg+xml"
    return "application/octet-stream"
