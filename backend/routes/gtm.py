"""
GTM Intelligence track — competitors, pricing, hiring signals, lead enrichment.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from models import SearchQuery, Track

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/gtm", tags=["gtm"])


@router.get("/insights")
async def get_gtm_insights(limit: int = 20):
    from main import engine
    insights = engine.get_insights(track=Track.GTM, limit=limit)
    return [i.model_dump(mode="json") for i in insights]


@router.post("/search")
async def gtm_search(query: SearchQuery):
    """Run a live GTM intelligence search via Bright Data SERP + agent."""
    from main import bright_data, engine

    results = await bright_data.serp_search(
        query.query + " competitor pricing product announcement",
        country=query.country,
        num=query.num_results,
    )
    return {
        "query": query.query,
        "track": "gtm",
        "results": results,
        "timestamp": _now(),
    }


@router.get("/competitor-analyze")
async def analyze_competitor(url: str = Query(..., description="Competitor website URL")):
    """Scrape and analyze a competitor's web presence."""
    from main import bright_data
    import config

    try:
        html = await bright_data.fetch_url(url)
    except Exception as e:
        return {
            "url": url,
            "analysis": f"Could not fetch page: {str(e)[:200]}",
            "raw_text_preview": "",
            "timestamp": _now(),
        }

    text = bright_data.extract_text(html)[:5000]

    if not text.strip():
        return {
            "url": url,
            "analysis": "Page returned no readable content (may require JavaScript or login).",
            "raw_text_preview": "",
            "timestamp": _now(),
        }

    if not config.is_aiml_configured():
        return {
            "url": url,
            "analysis": "Configure AIML_API_KEY for AI-powered competitor analysis.",
            "raw_text_preview": text[:500],
            "timestamp": _now(),
        }

    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        api_key=config.AIML_API_KEY,
        base_url=config.AIML_API_BASE_URL,
    )
    resp = await client.chat.completions.create(
        model=config.AIML_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a GTM analyst. Extract competitor intelligence as JSON. "
                    "Every list item MUST be a plain string, not an object. "
                    "Only include facts that appear verbatim or near-verbatim in the page text. "
                    "If a field has no supporting evidence on the page, return an empty list for it. "
                    "Do not invent prices, products, messages, or job titles."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Analyze this competitor page and extract the following keys. "
                    "Each value must be a list of plain strings (not objects):\n"
                    "- pricing: list of pricing tier strings, e.g. 'Pro: $20/mo'\n"
                    "- key_messages: list of value-prop sentences\n"
                    "- products: list of product/feature name strings\n"
                    "- hiring_signals: list of job-opening strings\n\n"
                    "If the page is empty, error, or unrelated to a product/company, "
                    "return all fields as empty lists.\n\n"
                    f"Page content:\n{text}"
                ),
            },
        ],
        temperature=0.2,
    )

    raw = _FENCE_RE.sub("", (resp.choices[0].message.content or "{}").strip()).strip()
    import json
    try:
        analysis = json.loads(raw)
    except Exception:
        analysis = {"raw": raw}

    return {
        "url": url,
        "analysis": analysis,
        "timestamp": _now(),
    }


@router.get("/hiring-signals")
async def get_hiring_signals(company: str = Query(...)):
    """Search for hiring signals for a given company."""
    from main import bright_data

    results = await bright_data.serp_search(
        f'site:linkedin.com OR site:indeed.com "{company}" jobs hiring 2024 2025',
        num=8,
    )
    return {
        "company": company,
        "hiring_signals": results,
        "timestamp": _now(),
    }


@router.get("/memory/related")
async def get_related_gtm_insights(query: str):
    """Query the Cognee knowledge graph for related GTM insights."""
    from main import memory_graph
    results = await memory_graph.search_related(query, track=Track.GTM)
    return {"query": query, "related": results}
