"""Sitemap parser for GEO DISCOVER phase.

Fetches robots.txt -> extracts Sitemap directives -> parses XML recursively.
Handles nested sitemaps, sitemap index files, and gzipped sitemaps.
"""

import gzip
import logging
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

import httpx

logger = logging.getLogger(__name__)

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
MAX_URLS = 10_000
MAX_SITEMAP_SIZE = 50_000_000  # 50MB — prevents memory exhaustion from huge sitemaps
FETCH_TIMEOUT = 30.0


@dataclass(frozen=True)
class SitemapEntry:
    """Single URL entry from a sitemap."""

    url: str
    lastmod: str | None = None
    changefreq: str | None = None
    priority: float | None = None


@dataclass
class SitemapInventory:
    """Complete sitemap inventory for a domain."""

    entries: list[SitemapEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    sitemaps_parsed: int = 0


class SitemapParser:
    """Parse sitemaps from a domain."""

    def __init__(self, timeout: float = FETCH_TIMEOUT):
        self._timeout = timeout

    async def parse(self, base_url: str) -> SitemapInventory:
        """Parse all sitemaps for a domain.

        1. Fetch robots.txt for Sitemap directives
        2. Fall back to /sitemap.xml if none found
        3. Recursively parse sitemap index files
        """
        inventory = SitemapInventory()

        # Normalize base URL
        if not base_url.endswith("/"):
            base_url = base_url.rstrip("/")
        domain = base_url.split("//", 1)[-1].split("/")[0]
        scheme = "https" if base_url.startswith("https") else "http"
        root = f"{scheme}://{domain}"

        async with httpx.AsyncClient(
            timeout=self._timeout, follow_redirects=True
        ) as client:
            # Step 1: Check robots.txt
            sitemap_urls = await self._extract_from_robots(
                client, f"{root}/robots.txt"
            )

            # Step 2: Fallback to /sitemap.xml
            if not sitemap_urls:
                sitemap_urls = [f"{root}/sitemap.xml"]

            # Step 3: Parse each sitemap (recursive for indices)
            for sitemap_url in sitemap_urls:
                if len(inventory.entries) >= MAX_URLS:
                    break
                await self._parse_sitemap(client, sitemap_url, inventory)

        return inventory

    async def _extract_from_robots(
        self, client: httpx.AsyncClient, robots_url: str
    ) -> list[str]:
        """Extract Sitemap: directives from robots.txt."""
        try:
            response = await client.get(robots_url)
            if response.status_code != 200:
                return []

            sitemaps = []
            for line in response.text.splitlines():
                line = line.strip()
                if line.lower().startswith("sitemap:"):
                    url = line.split(":", 1)[1].strip()
                    if url.startswith("http"):
                        sitemaps.append(url)
            return sitemaps
        except Exception as e:
            logger.debug("robots.txt fetch failed: %s", e)
            return []

    async def _parse_sitemap(
        self,
        client: httpx.AsyncClient,
        url: str,
        inventory: SitemapInventory,
        depth: int = 0,
    ) -> None:
        """Parse a single sitemap URL. Handles XML and gzipped formats."""
        if depth > 3 or len(inventory.entries) >= MAX_URLS:
            return

        try:
            response = await client.get(url)
            if response.status_code != 200:
                inventory.errors.append(f"HTTP {response.status_code}: {url}")
                return

            content = response.content

            # Size cap before parsing (prevents Billion Laughs XML DoS)
            if len(content) > MAX_SITEMAP_SIZE:
                inventory.errors.append(f"Sitemap too large ({len(content)} bytes): {url}")
                return

            # Handle gzipped
            if url.endswith(".gz") or response.headers.get(
                "content-type", ""
            ).startswith("application/x-gzip"):
                try:
                    content = gzip.decompress(content)
                except Exception:
                    inventory.errors.append(f"Gzip decode failed: {url}")
                    return

            root_elem = ET.fromstring(content)
            inventory.sitemaps_parsed += 1
            tag = root_elem.tag.lower()

            # Sitemap index
            if "sitemapindex" in tag:
                for sitemap in root_elem.findall("sm:sitemap", SITEMAP_NS):
                    loc = sitemap.find("sm:loc", SITEMAP_NS)
                    if loc is not None and loc.text:
                        child_url = loc.text.strip()
                        # SSRF prevention: skip cross-domain sitemap references
                        from urllib.parse import urlparse
                        if urlparse(child_url).netloc != urlparse(url).netloc:
                            inventory.errors.append(f"Cross-domain sitemap skipped: {child_url}")
                            continue
                        await self._parse_sitemap(
                            client, child_url, inventory, depth + 1
                        )
            # URL set
            elif "urlset" in tag:
                for url_elem in root_elem.findall("sm:url", SITEMAP_NS):
                    if len(inventory.entries) >= MAX_URLS:
                        break
                    loc = url_elem.find("sm:loc", SITEMAP_NS)
                    if loc is None or not loc.text:
                        continue

                    lastmod_elem = url_elem.find("sm:lastmod", SITEMAP_NS)
                    changefreq_elem = url_elem.find("sm:changefreq", SITEMAP_NS)
                    priority_elem = url_elem.find("sm:priority", SITEMAP_NS)

                    entry = SitemapEntry(
                        url=loc.text.strip(),
                        lastmod=(
                            lastmod_elem.text.strip()
                            if lastmod_elem is not None and lastmod_elem.text
                            else None
                        ),
                        changefreq=(
                            changefreq_elem.text.strip()
                            if changefreq_elem is not None and changefreq_elem.text
                            else None
                        ),
                        priority=(
                            float(priority_elem.text.strip())
                            if priority_elem is not None and priority_elem.text
                            else None
                        ),
                    )
                    inventory.entries.append(entry)

        except ET.ParseError as e:
            inventory.errors.append(f"XML parse error: {url}: {e}")
        except Exception as e:
            inventory.errors.append(f"Error parsing {url}: {e}")
