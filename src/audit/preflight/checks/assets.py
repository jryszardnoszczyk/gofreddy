"""Brand-asset probes: logo, robots.txt, sitemap.xml.

Cheap proxies — no image processing, no full crawl. Logo extraction =
``<link rel="icon">`` + ``<img>`` in header/footer/nav, hashed via sha256.
robots.txt parsing is line-based; AI-bot policy lookup covers GPTBot,
ClaudeBot, anthropic-ai, PerplexityBot, Google-Extended.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup


_AI_BOTS = ("GPTBot", "ClaudeBot", "anthropic-ai", "PerplexityBot", "Google-Extended")


async def _fetch_text(client: httpx.AsyncClient, url: str) -> str:
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            return ""
        return resp.text
    except httpx.HTTPError:
        return ""


async def _fetch_bytes(client: httpx.AsyncClient, url: str) -> bytes:
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            return b""
        return resp.content
    except httpx.HTTPError:
        return b""


def _extract_logo_urls(html: str, base: str) -> list[str]:
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for link in soup.find_all("link", rel=lambda v: v and "icon" in (v if isinstance(v, str) else " ".join(v)).lower()):
        href = link.get("href")
        if isinstance(href, str):
            urls.append(href if href.startswith("http") else base + href.lstrip("/"))
    # Header/footer/nav logo imgs
    for container in soup.find_all(["header", "footer", "nav"]):
        for img in container.find_all("img"):
            src = img.get("src")
            if isinstance(src, str):
                urls.append(src if src.startswith("http") else base + src.lstrip("/"))
    # Dedupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _parse_robots(text: str) -> dict[str, Any]:
    if not text:
        return {
            "present": False,
            "disallow_count": 0,
            "sitemap_urls": [],
            "ai_bot_policies": {bot: "unspecified" for bot in _AI_BOTS},
        }
    disallow_count = 0
    sitemap_urls: list[str] = []
    # Per-user-agent policy map: user_agent.lower() → {"allow": [...], "disallow": [...]}
    current_agents: list[str] = []
    policies: dict[str, dict[str, list[str]]] = {}

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            current_agents = []  # blank line resets the agent block
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key == "user-agent":
            current_agents.append(value.lower())
            policies.setdefault(value.lower(), {"allow": [], "disallow": []})
        elif key == "sitemap":
            sitemap_urls.append(value)
        elif key == "disallow":
            disallow_count += 1
            for ua in current_agents:
                policies.setdefault(ua, {"allow": [], "disallow": []})["disallow"].append(value)
        elif key == "allow":
            for ua in current_agents:
                policies.setdefault(ua, {"allow": [], "disallow": []})["allow"].append(value)

    ai_policies: dict[str, str] = {}
    for bot in _AI_BOTS:
        bot_key = bot.lower()
        if bot_key not in policies:
            ai_policies[bot] = "unspecified"
            continue
        bot_policy = policies[bot_key]
        # Disallow: / wins; otherwise check explicit allow.
        if any(p == "/" for p in bot_policy["disallow"]):
            ai_policies[bot] = "disallow"
        elif bot_policy["allow"] or bot_policy["disallow"]:
            ai_policies[bot] = "allow"
        else:
            ai_policies[bot] = "unspecified"

    return {
        "present": True,
        "disallow_count": disallow_count,
        "sitemap_urls": sitemap_urls,
        "ai_bot_policies": ai_policies,
    }


def _parse_sitemap(text: str) -> dict[str, Any]:
    if not text:
        return {
            "urls_discovered": 0,
            "nested_sitemaps": 0,
            "preflight_adversarial_flag": False,
        }
    nested = len(re.findall(r"<sitemap>", text, flags=re.IGNORECASE))
    url_count = len(re.findall(r"<url>", text, flags=re.IGNORECASE))
    return {
        "urls_discovered": url_count,
        "nested_sitemaps": nested,
        "preflight_adversarial_flag": url_count > 500,
    }


async def check(domain: str) -> dict:
    base = f"https://{domain.strip().rstrip('/')}/"

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        homepage_html = await _fetch_text(client, base)
        robots_text = await _fetch_text(client, base + "robots.txt")
        sitemap_text = await _fetch_text(client, base + "sitemap.xml")

        logo_urls = _extract_logo_urls(homepage_html, base)
        # Hash logo bytes — distinct hashes = logo-version sprawl.
        hashes: set[str] = set()
        formats: set[str] = set()
        for url in logo_urls[:8]:  # cap to avoid blowing up on weird DOMs
            data = await _fetch_bytes(client, url)
            if data:
                hashes.add(hashlib.sha256(data).hexdigest()[:16])
                if "." in url:
                    ext = url.rsplit(".", 1)[-1].split("?")[0].lower()
                    if ext in {"svg", "png", "jpg", "jpeg", "ico", "webp"}:
                        formats.add(ext)

    return {
        "logo": {
            "src_urls": logo_urls,
            "distinct_hashes": len(hashes),
            "formats": sorted(formats),
        },
        "brand_colors": {
            # CSS-custom-property scrape deferred — Stage-2 Narrative agent
            # has the homepage HTML and can extract via its own pass.
            "primary": None,
            "secondary": None,
            "css_source": None,
        },
        "robots_txt": _parse_robots(robots_text),
        "sitemap": _parse_sitemap(sitemap_text),
    }
