"""Tests for SSRF URL validation and path traversal prevention (PR-057 I1)."""

import asyncio
from unittest.mock import patch

import pytest

from src.common.url_validation import _is_blocked_ip, resolve_and_validate
from src.stories.storage import R2StoryStorage, _SAFE_KEY_COMPONENT

import ipaddress


# ── URL Scheme Tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_download_url_https_only():
    """Rejects non-HTTPS schemes: http, ftp, file."""
    for scheme in ("http", "ftp", "file"):
        url = f"{scheme}://example.com/video.mp4"
        with pytest.raises(ValueError, match="Only HTTPS URLs allowed"):
            await resolve_and_validate(url)


@pytest.mark.asyncio
async def test_validate_download_url_accepts_valid_https():
    """Accepts valid public HTTPS URLs."""
    # Mock DNS to return a public IP
    public_addr = [
        (2, 1, 6, "", ("93.184.216.34", 443)),
    ]
    with patch("src.common.url_validation.socket.getaddrinfo", return_value=public_addr):
        ip, hostname = await resolve_and_validate("https://example.com/video.mp4")
        assert ip == "93.184.216.34"
        assert hostname == "example.com"


@pytest.mark.asyncio
async def test_validate_download_url_returns_ip_hostname_tuple():
    """Verify returns (ip, hostname) tuple."""
    public_addr = [
        (2, 1, 6, "", ("1.2.3.4", 443)),
    ]
    with patch("src.common.url_validation.socket.getaddrinfo", return_value=public_addr):
        result = await resolve_and_validate("https://cdn.example.com/path")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "1.2.3.4"
        assert result[1] == "cdn.example.com"


# ── Private IP Rejection Tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_download_url_rejects_private_ips():
    """Rejects private IPs: 10.x, 172.16.x, 192.168.x, 127.x, 169.254.169.254."""
    private_ips = [
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "127.0.0.1",
        "169.254.169.254",
    ]
    for ip in private_ips:
        addr = [(2, 1, 6, "", (ip, 443))]
        with patch("src.common.url_validation.socket.getaddrinfo", return_value=addr):
            with pytest.raises(ValueError, match="blocked ranges"):
                await resolve_and_validate(f"https://evil.com/{ip}")


@pytest.mark.asyncio
async def test_validate_download_url_rejects_ipv6_private():
    """Rejects IPv6 private addresses: ::1, fc00::, fe80::."""
    ipv6_addrs = ["::1", "fc00::1", "fe80::1"]
    for ip in ipv6_addrs:
        addr = [(10, 1, 6, "", (ip, 443, 0, 0))]
        with patch("src.common.url_validation.socket.getaddrinfo", return_value=addr):
            with pytest.raises(ValueError, match="blocked ranges"):
                await resolve_and_validate("https://evil.com/path")


@pytest.mark.asyncio
async def test_validate_download_url_rejects_ipv6_mapped_ipv4():
    """Rejects IPv6-mapped IPv4 private addresses like ::ffff:169.254.169.254."""
    addr = [(10, 1, 6, "", ("::ffff:169.254.169.254", 443, 0, 0))]
    with patch("src.common.url_validation.socket.getaddrinfo", return_value=addr):
        with pytest.raises(ValueError, match="blocked ranges"):
            await resolve_and_validate("https://evil.com/path")


@pytest.mark.asyncio
async def test_validate_download_url_rejects_cgnat():
    """Rejects CGNAT range 100.64.0.0/10."""
    addr = [(2, 1, 6, "", ("100.64.0.1", 443))]
    with patch("src.common.url_validation.socket.getaddrinfo", return_value=addr):
        with pytest.raises(ValueError, match="blocked ranges"):
            await resolve_and_validate("https://evil.com/path")


@pytest.mark.asyncio
async def test_validate_download_url_rejects_nat64():
    """Rejects NAT64 prefix 64:ff9b:: encoded private IPs."""
    addr = [(10, 1, 6, "", ("64:ff9b::10.0.0.1", 443, 0, 0))]
    with patch("src.common.url_validation.socket.getaddrinfo", return_value=addr):
        with pytest.raises(ValueError, match="blocked ranges"):
            await resolve_and_validate("https://evil.com/path")


@pytest.mark.asyncio
async def test_validate_download_url_rejects_6to4_teredo():
    """Rejects 6to4 (2002::) and Teredo (2001::) tunneled IPs."""
    for prefix in ("2002::1", "2001::1"):
        addr = [(10, 1, 6, "", (prefix, 443, 0, 0))]
        with patch("src.common.url_validation.socket.getaddrinfo", return_value=addr):
            with pytest.raises(ValueError, match="blocked ranges"):
                await resolve_and_validate("https://evil.com/path")


# ── Hostname/Userinfo Validation ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_download_url_rejects_no_hostname():
    """Rejects URLs with empty or missing hostname."""
    with pytest.raises(ValueError, match="no hostname"):
        await resolve_and_validate("https:///path")


@pytest.mark.asyncio
async def test_validate_download_url_rejects_userinfo():
    """Rejects credential smuggling: https://attacker@host/path."""
    with pytest.raises(ValueError, match="userinfo"):
        await resolve_and_validate("https://attacker@host.com/path")


# ── DNS Failure ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_download_url_rejects_dns_failure():
    """Rejects when DNS resolution fails."""
    import socket
    with patch(
        "src.common.url_validation.socket.getaddrinfo",
        side_effect=socket.gaierror("DNS lookup failed"),
    ):
        with pytest.raises(ValueError, match="DNS resolution failed"):
            await resolve_and_validate("https://nonexistent.example.com/path")


# ── _is_blocked_ip unit tests ─────────────────────────────────────────────


def test_is_blocked_ip_ipv4_mapped_ipv6():
    """IPv6-mapped IPv4 addresses are unmapped and checked."""
    ip = ipaddress.ip_address("::ffff:192.168.1.1")
    assert _is_blocked_ip(ip) is True


def test_is_blocked_ip_public():
    """Public IPs are not blocked."""
    ip = ipaddress.ip_address("8.8.8.8")
    assert _is_blocked_ip(ip) is False


# ── Path Traversal Tests ──────────────────────────────────────────────────


def test_story_key_rejects_path_traversal():
    """Rejects path traversal attempts in username/story_id."""
    bad_inputs = [
        "../etc/passwd",
        "..%2F",
        "/etc/passwd",
        "..",
        "..\\windows",
        "-flag",  # starts with dash
    ]
    for bad in bad_inputs:
        assert _SAFE_KEY_COMPONENT.match(bad) is None, f"Should reject: {bad}"


def test_story_key_rejects_special_chars():
    """Rejects null bytes, spaces, unicode in key components."""
    bad_inputs = [
        "user\x00name",
        "user name",
        "üser",
        "user/name",
        "",
    ]
    for bad in bad_inputs:
        assert _SAFE_KEY_COMPONENT.match(bad) is None, f"Should reject: {bad!r}"


def test_story_key_accepts_valid_inputs():
    """Accepts alphanumeric, dots, hyphens, underscores."""
    good_inputs = [
        "username123",
        "user.name",
        "user_name",
        "user-name",
        "a",  # single char
        "A1234567890abcdef",
    ]
    for good in good_inputs:
        assert _SAFE_KEY_COMPONENT.match(good) is not None, f"Should accept: {good}"


# ── Storage Integration Tests ─────────────────────────────────────────────


def test_story_storage_key_validation():
    """R2StoryStorage._story_key rejects path traversal."""
    from src.common.enums import Platform

    storage = R2StoryStorage.__new__(R2StoryStorage)
    storage.STORY_PREFIX = "stories"

    with pytest.raises(ValueError, match="Invalid username"):
        storage._story_key(Platform.INSTAGRAM, "../admin", "story1", "video")

    with pytest.raises(ValueError, match="Invalid story_id"):
        storage._story_key(Platform.INSTAGRAM, "user1", "../etc", "video")


# ── Redirect Rejection Test ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_download_rejects_3xx_redirect():
    """Verify 3xx status raises ValueError during download."""
    import httpx

    storage = R2StoryStorage.__new__(R2StoryStorage)
    storage.STORY_PREFIX = "stories"
    storage._video_storage = None
    storage._settings = None

    mock_response = httpx.Response(301, headers={"Location": "http://evil.com"})

    public_addr = [(2, 1, 6, "", ("93.184.216.34", 443))]

    with (
        patch("src.common.url_validation.socket.getaddrinfo", return_value=public_addr),
        patch("httpx.AsyncClient.get", return_value=mock_response),
    ):
        with pytest.raises(ValueError, match="Unexpected redirect status"):
            await storage.download_and_upload_story(
                "https://cdn.example.com/video.mp4",
                platform=__import__("src.common.enums", fromlist=["Platform"]).Platform.INSTAGRAM,
                username="testuser",
                story_id="story123",
                media_type="video",
            )
