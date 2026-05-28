"""
Cognee integration — shared persistent knowledge graph across all tracks.

Uses the open-source cognee package (pip install cognee) with the AI/ML API
as the LLM backend. No paid Cognee cloud plan required.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import config

if TYPE_CHECKING:
    from models import InsightBrief, Track

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    def __init__(self):
        self._cognee_ready = False
        self._fallback_store: list[dict] = []

    async def initialize(self):
        if not config.is_aiml_configured():
            logger.info("AIML_API_KEY not set — using in-memory fallback graph")
            return

        try:
            import cognee

            # Configure cognee to use AI/ML API (OpenAI-compatible)
            os.environ.setdefault("LLM_API_KEY", config.AIML_API_KEY)
            os.environ.setdefault("LLM_API_BASE", config.AIML_API_BASE_URL)
            os.environ.setdefault("LLM_MODEL", config.AIML_MODEL)
            os.environ.setdefault("EMBEDDING_MODEL", "text-embedding-3-small")
            os.environ.setdefault("EMBEDDING_API_KEY", config.AIML_API_KEY)
            os.environ.setdefault("EMBEDDING_API_BASE", config.AIML_API_BASE_URL)

            # Use local LanceDB for vector storage — no external DB needed
            os.environ.setdefault("VECTOR_DB_PROVIDER", "lancedb")
            os.environ.setdefault("VECTOR_DB_URL", os.path.abspath(config.COGNEE_DB_PATH))

            # Verify cognee can be imported and used
            await cognee.prune.prune_data()
            self._cognee_ready = True
            logger.info("Cognee knowledge graph initialised (local, using AI/ML API)")

        except ImportError:
            logger.warning("cognee not installed — using in-memory fallback")
        except Exception as exc:
            logger.warning(f"Cognee init failed ({exc}) — using in-memory fallback")

    async def store_insight(self, brief: "InsightBrief"):
        text = (
            f"Track: {brief.track.upper()}\n"
            f"Title: {brief.title}\n"
            f"Summary: {brief.summary}\n"
            f"Impact: {brief.impact}\n"
            f"Source: {brief.source_name} ({brief.source_url})\n"
            f"Recommendations: {'; '.join(brief.recommendations)}\n"
            f"Cross-track links: {', '.join(brief.cross_track_links)}\n"
            f"Timestamp: {brief.timestamp.isoformat()}"
        )

        if self._cognee_ready:
            try:
                import cognee
                await cognee.add(text, dataset_name=f"nexusintel_{brief.track.value}")
                await cognee.cognify()
                logger.info(f"Stored in Cognee graph: {brief.title}")
                return
            except Exception as exc:
                logger.warning(f"Cognee store error: {exc}")

        # In-memory fallback
        self._fallback_store.append({
            "id": brief.id,
            "track": brief.track.value,
            "title": brief.title,
            "summary": brief.summary,
            "text": text,
            "timestamp": brief.timestamp.isoformat(),
        })
        logger.info(f"Stored in memory graph: {brief.title}")

    async def search_related(self, query: str, track: "Track | None" = None) -> list[dict]:
        if self._cognee_ready:
            try:
                import cognee
                results = await cognee.search(
                    query_text=query,
                    query_type=cognee.SearchType.INSIGHTS,
                )
                return [{"content": str(r), "source": "cognee"} for r in (results or [])[:5]]
            except Exception as exc:
                logger.warning(f"Cognee search error: {exc}")

        # Keyword search over in-memory store
        q = query.lower()
        matched = [
            e for e in self._fallback_store
            if q in e["text"].lower()
            and (track is None or e["track"] == track.value)
        ]
        return [{"content": m["text"], "source": "memory"} for m in matched[:5]]

    async def get_cross_track_context(self, insight: "InsightBrief") -> str:
        results = await self.search_related(insight.title + " " + insight.summary)
        if not results:
            return ""
        return "\n---\n".join(r["content"][:400] for r in results[:3])
