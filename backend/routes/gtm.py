"""
GTM Intelligence track — competitors, pricing, hiring signals, lead enrichment.
"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Query

from models import SearchQuery, Track

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
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/competitor-analyze")
async def analyze_competitor(url: str = Query(..., description="Competitor website URL")):
    """Scrape and analyze a competitor's web presence."""
    from main import bright_data
    import config

    html = await bright_data.fetch_url(url)
    text = bright_data.extract_text(html)[:5000]

    if not config.is_aiml_configured():
        return {
            "url": url,
            "analysis": "Configure AIML_API_KEY for AI-powered competitor analysis.",
            "raw_text_preview": text[:500],
            "timestamp": datetime.utcnow().isoformat(),
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
                "content": "You are a GTM analyst. Extract competitor intelligence as JSON.",
            },
            {
                "role": "user",
                "content": (
                    f"Analyze this competitor page and extract:\n"
                    f"- pricing (list of plans/prices found)\n"
                    f"- key_messages (their main value props)\n"
                    f"- products (list of products/features)\n"
                    f"- hiring_signals (any job openings or team expansion hints)\n\n"
                    f"Page content:\n{text}"
                ),
            },
        ],
        temperature=0.2,
    )

    raw = resp.choices[0].message.content or "{}"
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    import json
    try:
        analysis = json.loads(raw)
    except Exception:
        analysis = {"raw": raw}

    return {
        "url": url,
        "analysis": analysis,
        "timestamp": datetime.utcnow().isoformat(),
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
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/memory/related")
async def get_related_gtm_insights(query: str):
    """Query the Cognee knowledge graph for related GTM insights."""
    from main import memory_graph
    results = await memory_graph.search_related(query, track=Track.GTM)
    return {"query": query, "related": results}
