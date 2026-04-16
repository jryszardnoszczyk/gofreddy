"""SSRF validation utility for outbound URL fetching.

Validates URLs against a comprehensive deny-list of private, reserved, and
special-purpose IP ranges before allowing outbound HTTP requests.
"""

import asyncio
import ipaddress
import socket
from typing import Final
from urllib.parse import urlparse

# Complete SSRF deny-list: RFC 1918, CGNAT, link-local, cloud metadata,
# documentation nets, benchmarking, multicast, reserved, IPv6 equivalents.
# Sources: OWASP SSRF Cheat Sheet, IANA Special-Purpose Registry, safehttpx.
_BLOCKED_NETWORKS: Final[tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]] = (
    # IPv4
    ipaddress.ip_network("0.0.0.0/8"),         # "This" network (RFC 791)
    ipaddress.ip_network("10.0.0.0/8"),         # Private (RFC 1918)
    ipaddress.ip_network("100.64.0.0/10"),      # CGNAT / Shared (RFC 6598)
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback (RFC 1122)
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local + cloud metadata (RFC 3927)
    ipaddress.ip_network("172.16.0.0/12"),      # Private (RFC 1918)
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments (RFC 6890)
    ipaddress.ip_network("192.0.2.0/24"),       # Documentation TEST-NET-1 (RFC 5737)
    ipaddress.ip_network("192.88.99.0/24"),     # 6to4 relay anycast (RFC 7526)
    ipaddress.ip_network("192.168.0.0/16"),     # Private (RFC 1918)
    ipaddress.ip_network("198.18.0.0/15"),      # Benchmarking (RFC 2544)
    ipaddress.ip_network("198.51.100.0/24"),    # Documentation TEST-NET-2 (RFC 5737)
    ipaddress.ip_network("203.0.113.0/24"),     # Documentation TEST-NET-3 (RFC 5737)
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast (RFC 5771)
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved (RFC 1112)
    ipaddress.ip_network("255.255.255.255/32"), # Limited broadcast
    # IPv6
    ipaddress.ip_network("::1/128"),            # Loopback
    ipaddress.ip_network("::/128"),             # Unspecified
    ipaddress.ip_network("::ffff:0:0/96"),      # IPv4-mapped (hides private IPv4)
    ipaddress.ip_network("64:ff9b::/96"),       # NAT64 well-known prefix (RFC 6052)
    ipaddress.ip_network("64:ff9b:1::/48"),     # IPv4/IPv6 translation (RFC 8215)
    ipaddress.ip_network("100::/64"),           # Discard-only (RFC 6666)
    ipaddress.ip_network("2001::/32"),          # Teredo tunneling (RFC 4380)
    ipaddress.ip_network("2002::/16"),          # 6to4 tunneling (RFC 3056)
    ipaddress.ip_network("fc00::/7"),           # Unique local (RFC 4193)
    ipaddress.ip_network("fe80::/10"),          # Link-local (RFC 4291)
    ipaddress.ip_network("ff00::/8"),           # Multicast
)


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Defense-in-depth: explicit deny-list + Python built-in checks.

    The explicit list catches CGNAT (100.64.0.0/10) and IPv4-mapped-IPv6
    which Python's is_private misses. Built-in checks act as safety net.
    """
    # Unmap IPv6-mapped-IPv4 addresses to check the underlying IPv4
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local or ip.is_multicast:
        return True
    return any(ip in network for network in _BLOCKED_NETWORKS)


async def resolve_and_validate(url: str) -> tuple[str, str]:
    """Validate URL and resolve DNS, returning (validated_ip, hostname).

    Raises ValueError if URL is unsafe (non-HTTPS, private IP, DNS failure).
    """
    parsed = urlparse(url)

    # Scheme: HTTPS only
    if parsed.scheme != "https":
        raise ValueError(f"Only HTTPS URLs allowed, got: {parsed.scheme}")

    # Hostname: must be present
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")

    # Reject userinfo (credential smuggling): https://attacker@host/path
    if "@" in (parsed.netloc or ""):
        raise ValueError("URLs with userinfo (@) are not allowed")

    # DNS resolution: resolve ALL addresses in executor (async-safe)
    loop = asyncio.get_running_loop()
    try:
        addrs = await loop.run_in_executor(
            None,
            lambda: socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM),
        )
    except socket.gaierror as e:
        raise ValueError(f"DNS resolution failed for {hostname}") from e

    if not addrs:
        raise ValueError(f"No DNS records for {hostname}")

    # Return first non-blocked IP
    for _family, _type, _proto, _canonname, sockaddr in addrs:
        ip = ipaddress.ip_address(sockaddr[0])
        if not _is_blocked_ip(ip):
            return str(ip), hostname

    raise ValueError(f"All resolved IPs for {hostname} are in blocked ranges")


# ---------------------------------------------------------------------------
# fal.ai domain allowlist validation (SSRF protection for generation inputs)
# ---------------------------------------------------------------------------

_FAL_ALLOWED_DOMAINS: Final[frozenset[str]] = frozenset({
    "v3.fal.media",
    "fal.media",
    "fal.run",
    "storage.googleapis.com",
})


def validate_fal_url_domain(
    url: str,
    *,
    extra_domains: tuple[str, ...] = (),
) -> None:
    """Validate that *url* uses HTTPS and its hostname is in the fal.ai allowlist.

    Args:
        url: The URL to validate.
        extra_domains: Additional hostnames to accept (e.g. an R2 bucket domain).

    Raises:
        ValueError: If the scheme is not HTTPS or the domain is not allowed.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Insecure URL scheme (expected https): {url[:100]}")
    domain = parsed.hostname or ""
    allowed = (_FAL_ALLOWED_DOMAINS | frozenset(extra_domains)) if extra_domains else _FAL_ALLOWED_DOMAINS
    if domain not in allowed:
        raise ValueError(f"URL domain not allowed: {domain}")
