"""L4 R2 publish helper tests — graceful no-op + dry-run + content-type."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.audit.r2_publish import _content_type, upload_audit_dir


@pytest.fixture
def env_complete(monkeypatch):
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "test_key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "test_secret")
    monkeypatch.setenv("R2_ACCOUNT_ID", "abc123")
    monkeypatch.setenv("R2_AUDITS_BUCKET", "test-audits")
    monkeypatch.delenv("R2_PUBLIC_BASE_URL", raising=False)


@pytest.fixture
def env_missing(monkeypatch):
    for var in ["R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ACCOUNT_ID"]:
        monkeypatch.delenv(var, raising=False)


def _seed(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / "report.html").write_text("<html>x</html>")
    (d / "report.pdf").write_bytes(b"%PDF-stub")
    (d / "assets").mkdir()
    (d / "assets" / "logo.png").write_bytes(b"\x89PNG_stub")


def test_content_type_html_pdf_json():
    assert _content_type("report.html") == "text/html; charset=utf-8"
    assert _content_type("report.pdf") == "application/pdf"
    assert _content_type("data.json") == "application/json"
    assert _content_type("style.css") == "text/css"
    assert _content_type("img.png") == "image/png"
    assert _content_type("img.jpg") == "image/jpeg"
    assert _content_type("img.svg") == "image/svg+xml"
    assert _content_type("unknown.bin") == "application/octet-stream"


def test_dry_run_returns_url_without_upload(env_complete, tmp_path):
    _seed(tmp_path / "deliv")
    with patch("boto3.client") as mock_boto:
        url = upload_audit_dir(tmp_path / "deliv", "abc123", dry_run=True)
    assert url == "https://reports.gofreddy.ai/abc123/"
    mock_boto.assert_not_called()


def test_dry_run_honors_custom_public_base(env_complete, monkeypatch, tmp_path):
    monkeypatch.setenv("R2_PUBLIC_BASE_URL", "https://staging.reports.example/")
    _seed(tmp_path / "deliv")
    url = upload_audit_dir(tmp_path / "deliv", "x", dry_run=True)
    assert url == "https://staging.reports.example/x/"


def test_returns_empty_string_when_credentials_incomplete(env_missing, tmp_path):
    _seed(tmp_path / "deliv")
    url = upload_audit_dir(tmp_path / "deliv", "abc123")
    assert url == ""


def test_uploads_each_file_with_correct_key_and_content_type(env_complete, tmp_path):
    _seed(tmp_path / "deliv")
    mock_client = MagicMock()
    with patch("boto3.client", return_value=mock_client):
        url = upload_audit_dir(tmp_path / "deliv", "ulid_xyz")
    assert url == "https://reports.gofreddy.ai/ulid_xyz/"
    # 3 files: report.html, report.pdf, assets/logo.png
    assert mock_client.upload_file.call_count == 3
    keys = [call.args[2] for call in mock_client.upload_file.call_args_list]
    assert "ulid_xyz/report.html" in keys
    assert "ulid_xyz/report.pdf" in keys
    assert "ulid_xyz/assets/logo.png" in keys
    # Content-Type set per extension
    for call in mock_client.upload_file.call_args_list:
        ct = call.kwargs["ExtraArgs"]["ContentType"]
        if call.args[2].endswith(".html"):
            assert ct == "text/html; charset=utf-8"
        elif call.args[2].endswith(".pdf"):
            assert ct == "application/pdf"
        elif call.args[2].endswith(".png"):
            assert ct == "image/png"


def test_returns_empty_when_upload_fails_partway(env_complete, tmp_path):
    _seed(tmp_path / "deliv")
    mock_client = MagicMock()
    mock_client.upload_file.side_effect = [None, Exception("network down"), None]
    with patch("boto3.client", return_value=mock_client):
        url = upload_audit_dir(tmp_path / "deliv", "ulid_xyz")
    assert url == ""


def test_uses_account_id_to_build_endpoint_url(env_complete, tmp_path):
    _seed(tmp_path / "deliv")
    mock_client = MagicMock()
    with patch("boto3.client", return_value=mock_client) as mock_boto:
        upload_audit_dir(tmp_path / "deliv", "x")
    assert mock_boto.call_args.kwargs["endpoint_url"] == "https://abc123.r2.cloudflarestorage.com"
    assert mock_boto.call_args.kwargs["region_name"] == "auto"


def test_honors_custom_bucket(env_complete, monkeypatch, tmp_path):
    monkeypatch.setenv("R2_AUDITS_BUCKET", "production-audits")
    _seed(tmp_path / "deliv")
    mock_client = MagicMock()
    with patch("boto3.client", return_value=mock_client):
        upload_audit_dir(tmp_path / "deliv", "x")
    bucket_used = mock_client.upload_file.call_args_list[0].args[1]
    assert bucket_used == "production-audits"
