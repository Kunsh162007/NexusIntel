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
        """Fetch a URL through Web Unlocker (defeats CAPTCHAs / anti-bot).

        Falls back to direct fetch when Web Unlocker refuses the URL — e.g.
        sec.gov which is blocked by the Unlocker's robots.txt policy but is
        perfectly happy with a direct request that includes a proper UA.
        """
        if not config.is_bright_data_configured():
            return await self._fallback_fetch(url)

        proxies = self._unlocker_proxies()
        try:
            async with httpx.AsyncClient(
                proxies=proxies, verify=False, timeout=self.timeout
            ) as client:
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
                return resp.text
        except httpx.HTTPStatusError as exc:
            # Bright Data returns 4xx with a JSON body for policy refusals
            # (robots.txt, "bad_endpoint", etc.) — those are recoverable via
            # direct fetch for sites that don't actually block us.
            if exc.response is not None and 400 <= exc.response.status_code < 500:
                return await self._fallback_fetch(url)
            raise

    def _user_agent_for(self, url: str) -> str:
        """SEC.gov requires a contactable UA; use it for any .gov site."""
        if ".gov" in url:
            return "NexusIntel Research nexusintel-research@example.com (educational hackathon project)"
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )

    async def _fallback_fetch(self, url: str) -> str:
        """Direct fetch (no proxy) used when Bright Data is not configured
        or when the Web Unlocker refuses the URL by policy."""
        headers = {"User-Agent": self._user_agent_for(url)}
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
        results: list[dict] = []
        seen: set[str] = set()

        # Modern Google HTML structures (selectors change frequently)
        candidate_selectors = [
            "div.g",
            "div[data-hveid] div.g",
            "div.Gx5Zad",
            "div.tF2Cxc",
            "div.MjjYud",
            "div.kvH3mc",
            "div[jscontroller] h3",
        ]
        candidates = []
        for sel in candidate_selectors:
            candidates.extend(soup.select(sel))

        # As a last resort, walk every <h3> on the page
        if not candidates:
            candidates = soup.find_all("h3")

        for node in candidates:
            block = node if node.name != "h3" else (node.find_parent("div") or node)
            title_tag = block.select_one("h3") if block.name != "h3" else block
            link_tag = None
            for a in block.find_all("a", href=True):
                href = a.get("href", "")
                if href.startswith("/url?"):
                    # Google redirector — extract the real URL
                    from urllib.parse import urlparse, parse_qs
                    qs = parse_qs(urlparse(href).query)
                    href = (qs.get("q") or qs.get("url") or [""])[0]
                if href.startswith("http") and "google.com" not in href:
                    link_tag = {"href": href}
                    break
            snippet_tag = block.select_one(
                ".VwiC3b, div[data-sncf], span.aCOpRe, .s3v9rd, .lEBKkf"
            )
            if title_tag and link_tag:
                url = link_tag["href"]
                if url in seen:
                    continue
                seen.add(url)
                results.append({
                    "title": title_tag.get_text(strip=True),
                    "url": url,
                    "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
                })
            if len(results) >= 10:
                break
        return results

    async def _fallback_serp(self, query: str) -> list[dict]:
        """
        Reliable fallback using HackerNews + Reddit public JSON APIs.
        These never block cloud IPs and require no credentials.
        """
        from urllib.parse import quote_plus
        encoded = quote_plus(query)
        short_timeout = httpx.Timeout(15.0)
        headers = {"User-Agent": "NexusIntel/1.0 (hackathon research tool)"}

        async with httpx.AsyncClient(timeout=short_timeout, headers=headers) as client:
            hn, reddit = await asyncio.gather(
                self._search_hackernews(client, encoded),
                self._search_reddit(client, encoded),
                return_exceptions=True,
            )
            results = []
            if isinstance(hn, list):
                results.extend(hn)
            if isinstance(reddit, list):
                results.extend(reddit)
            return results[:10]

    async def _search_hackernews(self, client, encoded_query: str) -> list[dict]:
        try:
            resp = await client.get(
                f"https://hn.algolia.com/api/v1/search?query={encoded_query}"
                f"&tags=story&hitsPerPage=6"
            )
            results = []
            for hit in resp.json().get("hits", []):
                if hit.get("title"):
                    results.append({
                        "title": hit["title"],
                        "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        "snippet": f"{hit.get('points', 0)} points · {hit.get('num_comments', 0)} comments on HackerNews",
                    })
            return results
        except Exception:
            return []

    async def _search_reddit(self, client, encoded_query: str) -> list[dict]:
        try:
            resp = await client.get(
                f"https://www.reddit.com/search.json?q={encoded_query}&sort=relevance&limit=6&type=link"
            )
            results = []
            for child in resp.json().get("data", {}).get("children", []):
                p = child.get("data", {})
                if p.get("title"):
                    results.append({
                        "title": p["title"],
                        "url": p.get("url") or f"https://reddit.com{p.get('permalink', '')}",
                        "snippet": (p.get("selftext") or f"r/{p.get('subreddit', '')} · {p.get('score', 0)} upvotes")[:200],
                    })
            return results
        except Exception:
            return []

    # kept for reference — no longer called
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
