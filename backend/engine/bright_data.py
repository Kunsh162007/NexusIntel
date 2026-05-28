import httpx
import json
import asyncio
from typing import Optional
from bs4 import BeautifulSoup
import config


class BrightDataClient:
    """Wraps all five Bright Data products used in NexusIntel."""

    def __init__(self):
        self.api_token = config.BRIGHT_DATA_API_TOKEN
        self.customer_id = config.BRIGHT_DATA_CUSTOMER_ID
        self.timeout = httpx.Timeout(45.0)

    # ── Internal helpers ──────────────────────────────────────────────────

    def _proxy_url(self, zone: str, password: str) -> str:
        return (
            f"http://brd-customer-{self.customer_id}"
            f"-zone-{zone}:{password}@brd.superproxy.io:22225"
        )

    def _unlocker_proxies(self) -> dict:
        url = self._proxy_url(
            config.BRIGHT_DATA_UNLOCKER_ZONE,
            config.BRIGHT_DATA_UNLOCKER_PASSWORD,
        )
        return {"http://": url, "https://": url}

    def _serp_proxies(self) -> dict:
        url = self._proxy_url(
            config.BRIGHT_DATA_SERP_ZONE,
            config.BRIGHT_DATA_SERP_PASSWORD,
        )
        return {"http://": url, "https://": url}

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_token}"}

    # ── Web Unlocker ──────────────────────────────────────────────────────

    async def fetch_url(self, url: str) -> str:
        """Fetch a URL through Web Unlocker (defeats CAPTCHAs / anti-bot)."""
        if not config.is_bright_data_configured():
            return await self._fallback_fetch(url)

        proxies = self._unlocker_proxies()
        async with httpx.AsyncClient(
            proxies=proxies, verify=False, timeout=self.timeout
        ) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            return resp.text

    async def _fallback_fetch(self, url: str) -> str:
        """Direct fetch (no proxy) used when Bright Data is not configured."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            )
        }
        async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
            try:
                resp = await client.get(url, follow_redirects=True)
                return resp.text  # return whatever we get; don't raise on 4xx/5xx
            except Exception:
                return ""

    def extract_text(self, html: str) -> str:
        """Strip HTML tags and return clean readable text."""
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return " ".join(soup.get_text(separator=" ").split())

    # ── SERP API ──────────────────────────────────────────────────────────

    async def serp_search(self, query: str, country: str = "us", num: int = 10) -> list[dict]:
        """Return structured search results via SERP zone, with Bing fallback."""
        if not config.is_bright_data_configured():
            return await self._fallback_serp(query)

        from urllib.parse import quote_plus
        serp_url = (
            f"https://www.google.com/search?q={quote_plus(query)}&num={num}"
            f"&gl={country.lower()}&hl=en"
        )
        proxies = self._serp_proxies()
        try:
            async with httpx.AsyncClient(
                proxies=proxies, verify=False, timeout=self.timeout
            ) as client:
                resp = await client.get(serp_url, follow_redirects=True)
                results = self._parse_serp_html(resp.text, query)
        except Exception:
            results = []

        # Fall back to Bing if Bright Data SERP returns nothing
        if not results:
            results = await self._fallback_serp(query)
        return results

    def _parse_serp_html(self, html: str, query: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        # Modern Google HTML structure (2024-2025)
        for g in soup.select("div.g, div[data-hveid] div.g, div.Gx5Zad"):
            title_tag = g.select_one("h3")
            # Get the first external link (skip internal google.com hrefs)
            link_tag = None
            for a in g.select("a[href]"):
                href = a.get("href", "")
                if href.startswith("http") and "google.com" not in href:
                    link_tag = a
                    break
            snippet_tag = g.select_one(".VwiC3b, div[data-sncf], span.aCOpRe, .s3v9rd")
            if title_tag and link_tag:
                results.append({
                    "title": title_tag.get_text(strip=True),
                    "url": link_tag["href"],
                    "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
                })
            if len(results) >= 10:
                break
        return results

    async def _fallback_serp(self, query: str) -> list[dict]:
        """Bing HTML search as a no-credential fallback (more reliable from cloud IPs)."""
        encoded = httpx.URL(query=query).query
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
            # Try Bing first
            results = await self._parse_bing(client, encoded)
            if results:
                return results
            # Fall back to DuckDuckGo HTML
            return await self._parse_ddg(client, encoded)

    async def _parse_bing(self, client, encoded_query: str) -> list[dict]:
        try:
            resp = await client.get(
                f"https://www.bing.com/search?q={encoded_query}&count=10",
                follow_redirects=True,
            )
            soup = BeautifulSoup(resp.text, "lxml")
            results = []
            for li in soup.select("li.b_algo"):
                title_el = li.select_one("h2 a")
                snippet_el = li.select_one(".b_caption p, .b_algoSlug")
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": title_el.get("href", ""),
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })
                if len(results) >= 10:
                    break
            return results
        except Exception:
            return []

    async def _parse_ddg(self, client, encoded_query: str) -> list[dict]:
        try:
            resp = await client.get(
                f"https://html.duckduckgo.com/html/?q={encoded_query}",
                follow_redirects=True,
            )
            soup = BeautifulSoup(resp.text, "lxml")
            results = []
            for r in soup.select(".result__body"):
                title_el = r.select_one(".result__title a, .result__a")
                link_el = r.select_one(".result__url a, .result__url")
                snippet_el = r.select_one(".result__snippet")
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": link_el.get_text(strip=True) if link_el else "",
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })
                if len(results) >= 10:
                    break
            return results
        except Exception:
            return []

    # ── Web Scraper API ───────────────────────────────────────────────────

    async def scraper_api(self, dataset_id: str, params: list[dict]) -> list[dict]:
        """Trigger a Bright Data Web Scraper API job and wait for results."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            trigger = await client.post(
                "https://api.brightdata.com/dca/trigger",
                params={
                    "dataset_id": dataset_id,
                    "format": "json",
                    "uncompressed_webhook": True,
                },
                json=params,
                headers=self._auth_headers(),
            )
            trigger.raise_for_status()
            snapshot_id = trigger.json().get("snapshot_id")
            if not snapshot_id:
                return []

            for _ in range(24):
                await asyncio.sleep(5)
                status = await client.get(
                    f"https://api.brightdata.com/dca/dataset/{snapshot_id}",
                    headers=self._auth_headers(),
                )
                if status.status_code == 200:
                    data = status.json()
                    if isinstance(data, list):
                        return data
            return []

    # ── Scraping Browser ──────────────────────────────────────────────────

    async def scraping_browser_fetch(self, url: str) -> str:
        """
        Fetch JavaScript-heavy pages via Scraping Browser.
        Falls back to Web Unlocker when browser zone is not configured.
        """
        if not config.BRIGHT_DATA_BROWSER_PASSWORD:
            return await self.fetch_url(url)

        browser_url = self._proxy_url(
            config.BRIGHT_DATA_BROWSER_ZONE,
            config.BRIGHT_DATA_BROWSER_PASSWORD,
        )
        proxies = {"http://": browser_url, "https://": browser_url}
        async with httpx.AsyncClient(
            proxies=proxies, verify=False, timeout=self.timeout
        ) as client:
            resp = await client.get(url, follow_redirects=True)
            return resp.text
