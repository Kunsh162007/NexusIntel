"""
Auto-Focus Engine — the autonomous core of NexusIntel AI.

Continuously monitors a watchlist of live web sources, detects semantic anomalies
via embedding-based comparison, dispatches deep-dive agents, stores insights in
Cognee, fires TriggerWare webhooks, and broadcasts to WebSocket clients.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import config
from models import InsightBrief, ImpactLevel, Track, WatchListItem

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _strip_code_fence(raw: str) -> str:
    """Strip ```json ... ``` fences from an LLM response, if present."""
    return _FENCE_RE.sub("", raw.strip()).strip()


# ── Default watchlist ─────────────────────────────────────────────────────────

DEFAULT_WATCHLIST: list[WatchListItem] = [
    WatchListItem(
        url="https://news.ycombinator.com/",
        track=Track.GTM,
        name="Hacker News",
        description="Tech competitor activity & market signals",
        anomaly_threshold=0.82,
    ),
    WatchListItem(
        url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&dateb=&owner=include&count=10&search_text=",
        track=Track.FINANCE,
        name="SEC Recent 8-K Filings",
        description="Latest corporate regulatory filings",
        anomaly_threshold=0.80,
    ),
    WatchListItem(
        url="https://www.cisa.gov/news-events/cybersecurity-advisories",
        track=Track.SECURITY,
        name="CISA Security Advisories",
        description="Government cybersecurity threat advisories",
        anomaly_threshold=0.78,
    ),
    WatchListItem(
        url="https://feeds.feedburner.com/TechCrunch",
        track=Track.FINANCE,
        name="TechCrunch Feed",
        description="Tech market news and funding signals",
        anomaly_threshold=0.75,
    ),
]


# ── Embedding helper (uses scikit-learn TF-IDF as fallback) ──────────────────

class EmbeddingEngine:
    def __init__(self):
        self._use_aiml = config.is_aiml_configured()
        self._openai_client = None
        self._tfidf = None

    async def embed(self, text: str) -> np.ndarray:
        text = text[:8000]
        if self._use_aiml:
            return await self._aiml_embed(text)
        return self._tfidf_embed(text)

    async def _aiml_embed(self, text: str) -> np.ndarray:
        if self._openai_client is None:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(
                api_key=config.AIML_API_KEY,
                base_url=config.AIML_API_BASE_URL,
            )
        resp = await self._openai_client.embeddings.create(
            model=config.AIML_EMBEDDING_MODEL,
            input=text,
        )
        return np.array(resp.data[0].embedding)

    def _tfidf_embed(self, text: str) -> np.ndarray:
        # HashingVectorizer is stateless — same token always maps to same dimension.
        # This guarantees vectors are comparable across calls.
        from sklearn.feature_extraction.text import HashingVectorizer
        if self._tfidf is None:
            self._tfidf = HashingVectorizer(
                n_features=512,
                stop_words="english",
                alternate_sign=False,
                norm="l2",
            )
        try:
            vec = self._tfidf.transform([text])
            return vec.toarray()[0]
        except Exception:
            return np.zeros(512)


# ── Internal state per watchlist item ────────────────────────────────────────

class _ItemState:
    def __init__(self, item: WatchListItem):
        self.item = item
        self.baseline: Optional[np.ndarray] = None
        self.last_checked: Optional[datetime] = None
        self.last_content: str = ""


# ── Engine ───────────────────────────────────────────────────────────────────

class AutoFocusEngine:
    def __init__(
        self,
        bright_data,
        memory_graph,
        trigger_client,
        ws_broadcaster: Callable,
    ):
        self.bd = bright_data
        self.memory = memory_graph
        self.triggers = trigger_client
        self.broadcaster = ws_broadcaster
        self.embedder = EmbeddingEngine()

        self._states: dict[str, _ItemState] = {
            item.id: _ItemState(item) for item in DEFAULT_WATCHLIST
        }
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._insights: list[InsightBrief] = []
        self._anomaly_count = 0
        self._active_agents = 0
        self._last_check: Optional[datetime] = None

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._monitor_loop())
            logger.info("Auto-Focus Engine started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Auto-Focus Engine stopped")

    # ── Public API ────────────────────────────────────────────────────────

    def add_watch_item(self, item: WatchListItem):
        self._states[item.id] = _ItemState(item)

    def remove_watch_item(self, item_id: str):
        self._states.pop(item_id, None)

    def get_watchlist(self) -> list[WatchListItem]:
        return [s.item for s in self._states.values()]

    def get_insights(self, track: Optional[Track] = None, limit: int = 50) -> list[InsightBrief]:
        items = self._insights
        if track:
            items = [i for i in items if i.track == track]
        return sorted(items, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_status(self) -> dict:
        next_check = None
        if self._last_check:
            next_check = self._last_check + timedelta(seconds=config.ENGINE_CHECK_INTERVAL_SECONDS)
        return {
            "running": self._running,
            "watchlist_count": len(self._states),
            "insights_generated": len(self._insights),
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "anomalies_detected": self._anomaly_count,
            "next_check": next_check.isoformat() if next_check else None,
            "active_agents": self._active_agents,
        }

    # ── Monitor loop ──────────────────────────────────────────────────────

    async def _monitor_loop(self):
        # Initial baseline pass (no anomaly detection)
        logger.info("Building baselines for watchlist...")
        await self._check_all(baseline_pass=True)

        while self._running:
            await asyncio.sleep(config.ENGINE_CHECK_INTERVAL_SECONDS)
            logger.info("Auto-Focus cycle starting...")
            await self._check_all(baseline_pass=False)

    async def _check_all(self, baseline_pass: bool):
        self._last_check = datetime.now(timezone.utc)
        tasks = [
            self._check_item(state, baseline_pass)
            for state in self._states.values()
            if state.item.active
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_item(self, state: _ItemState, baseline_pass: bool):
        item = state.item
        try:
            html = await self.bd.fetch_url(item.url)
            text = self.bd.extract_text(html)[:6000]
            embedding = await self.embedder.embed(text)

            state.last_checked = datetime.now(timezone.utc)

            if state.baseline is None or baseline_pass:
                state.baseline = embedding
                state.last_content = text
                logger.debug(f"Baseline set for {item.name}")
                return

            similarity = float(
                cosine_similarity([embedding], [state.baseline])[0][0]
            )
            logger.info(f"{item.name} similarity={similarity:.3f} threshold={item.anomaly_threshold}")

            if similarity < item.anomaly_threshold:
                logger.warning(f"ANOMALY detected on {item.name} (sim={similarity:.3f})")
                self._anomaly_count += 1
                state.baseline = embedding
                state.last_content = text
                asyncio.create_task(
                    self._handle_anomaly(item, text, similarity)
                )
        except Exception as exc:
            logger.error(f"Error checking {item.url}: {exc}")

    # ── Anomaly handling ──────────────────────────────────────────────────

    async def _handle_anomaly(self, item: WatchListItem, content: str, similarity: float):
        self._active_agents += 1
        try:
            brief = await self._investigate(item, content, similarity)
            self._insights.append(brief)

            # Store in Cognee memory graph
            try:
                await self.memory.store_insight(brief)
            except Exception as e:
                logger.warning(f"Cognee store failed: {e}")

            # Fire TriggerWare webhook
            try:
                await self.triggers.fire_alert(brief)
            except Exception as e:
                logger.warning(f"TriggerWare fire failed: {e}")

            # Broadcast to WebSocket clients
            await self.broadcaster({
                "type": "insight",
                "data": brief.model_dump(mode="json"),
            })
        finally:
            self._active_agents -= 1

    async def _investigate(
        self, item: WatchListItem, content: str, similarity: float
    ) -> InsightBrief:
        if not config.is_aiml_configured():
            return self._demo_brief(item, similarity)

        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=config.AIML_API_KEY,
            base_url=config.AIML_API_BASE_URL,
        )

        prompt = (
            f"A significant change was detected on {item.name} ({item.url}).\n"
            f"Track: {item.track.upper()}\n"
            f"Content sample:\n{content[:3000]}\n\n"
            "Generate a Critical Insight Brief as JSON with these keys:\n"
            "title (string), summary (2-3 sentences), impact (Critical/High/Medium/Low),\n"
            "recommendations (list of 3 strings), cross_track_links (list of affected tracks).\n"
            "Return ONLY the JSON object."
        )

        resp = await client.chat.completions.create(
            model=config.AIML_MODEL,
            messages=[
                {"role": "system", "content": "You are an enterprise intelligence analyst. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        raw = _strip_code_fence(resp.choices[0].message.content or "{}")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

        return InsightBrief(
            title=data.get("title", f"Change detected: {item.name}"),
            summary=data.get("summary", f"Significant content shift detected on {item.url}"),
            impact=ImpactLevel(data.get("impact", "High")),
            recommendations=data.get("recommendations", ["Review the source", "Assess business impact", "Take action if needed"]),
            track=item.track,
            source_url=item.url,
            source_name=item.name,
            similarity_score=round(similarity, 4),
            cross_track_links=data.get("cross_track_links", []),
        )

    def _demo_brief(self, item: WatchListItem, similarity: float) -> InsightBrief:
        """Fallback brief when AI/ML API is not configured."""
        return InsightBrief(
            title=f"[Demo] Change detected on {item.name}",
            summary=(
                f"The Auto-Focus Engine detected a semantic shift (similarity={similarity:.3f}) "
                f"on {item.url}. Configure AIML_API_KEY for AI-generated analysis."
            ),
            impact=ImpactLevel.HIGH,
            recommendations=[
                "Configure AIML_API_KEY to enable AI-powered analysis",
                f"Manually review {item.url}",
                f"Assess business impact for the {item.track.upper()} team",
            ],
            track=item.track,
            source_url=item.url,
            source_name=item.name,
            similarity_score=round(similarity, 4),
        )

    # ── Demo scenario (for live demo without waiting for real anomalies) ──

    async def run_demo_scenario(self, scenario: str = "competitor_price_cut") -> InsightBrief:
        scenarios = {
            "competitor_price_cut": InsightBrief(
                title="CRITICAL: Competitor Slashes Flagship Price by 18%",
                summary=(
                    "TechRival Corp has dropped the price of its EnterpriseShield platform from "
                    "$4,200/mo to $3,444/mo — an 18% reduction. Simultaneously, a new EU data-residency "
                    "regulation published today names TechRival's home region, creating a compliance "
                    "exposure that may explain the defensive pricing move."
                ),
                impact=ImpactLevel.CRITICAL,
                recommendations=[
                    "Alert sales team to update competitive battlecards immediately",
                    "Finance team should model margin impact of a counter-pricing response",
                    "Legal/Compliance should assess EU regulation impact on shared customers",
                ],
                track=Track.GTM,
                source_url="https://techrival.example.com/pricing",
                source_name="TechRival Corp Pricing Page",
                similarity_score=0.61,
                cross_track_links=["finance", "security"],
            ),
            "data_breach_detected": InsightBrief(
                title="HIGH: 47K Credential Records Detected on Dark Web Forum",
                summary=(
                    "A threat actor has posted what appears to be 47,000 email/password combinations "
                    "attributed to customers of a major enterprise SaaS vendor. Cross-referencing with "
                    "our customer list shows potential exposure for 12 accounts. Immediate password "
                    "reset and MFA enforcement recommended."
                ),
                impact=ImpactLevel.CRITICAL,
                recommendations=[
                    "Immediately notify affected customers and force password resets",
                    "Enable MFA enforcement across all at-risk accounts",
                    "File incident report per applicable breach notification regulations",
                ],
                track=Track.SECURITY,
                source_url="https://cisa.gov/advisories",
                source_name="Threat Intelligence Feed",
                similarity_score=0.59,
                cross_track_links=["gtm", "finance"],
            ),
            "regulatory_filing": InsightBrief(
                title="MEDIUM: SEC 8-K Filing Signals Pre-Earnings Anomaly",
                summary=(
                    "Three competing firms in the enterprise software sector have filed SEC 8-K reports "
                    "within a 48-hour window, each citing 'material changes to revenue guidance.' "
                    "Web traffic data across their pricing pages shows a 34% spike, suggesting "
                    "aggressive customer acquisition ahead of earnings."
                ),
                impact=ImpactLevel.HIGH,
                recommendations=[
                    "Finance team should update earnings model with revised competitor guidance",
                    "GTM team should monitor for churning customers looking to switch",
                    "Review pipeline to identify deals that may be influenced by competitor pricing",
                ],
                track=Track.FINANCE,
                source_url="https://sec.gov/cgi-bin/browse-edgar",
                source_name="SEC EDGAR Filing System",
                similarity_score=0.72,
                cross_track_links=["gtm", "security"],
            ),
        }

        brief = scenarios.get(scenario, scenarios["competitor_price_cut"])

        self._insights.append(brief)
        self._anomaly_count += 1

        try:
            await self.memory.store_insight(brief)
        except Exception:
            pass

        try:
            await self.triggers.fire_alert(brief)
        except Exception:
            pass

        await self.broadcaster({"type": "insight", "data": brief.model_dump(mode="json")})
        return brief
