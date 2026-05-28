"""
Finance & Market Intelligence track — alt-data, regulatory filings, pricing anomalies.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Query

from models import SearchQuery, Track

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/insights")
async def get_finance_insights(limit: int = 20):
    from main import engine
    insights = engine.get_insights(track=Track.FINANCE, limit=limit)
    return [i.model_dump(mode="json") for i in insights]


@router.post("/search")
async def finance_search(query: SearchQuery):
    from main import bright_data

    results = await bright_data.serp_search(
        query.query + " market signal regulatory filing earnings",
        country=query.country,
        num=query.num_results,
    )
    return {
        "query": query.query,
        "track": "finance",
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/regulatory-filings")
async def get_regulatory_filings(company: str | None = Query(None)):
    """Fetch recent SEC 8-K filings."""
    from main import bright_data

    url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        "?action=getcurrent&type=8-K&dateb=&owner=include&count=10"
    )
    if company:
        url += f"&company={company}"

    html = await bright_data.fetch_url(url)
    text = bright_data.extract_text(html)

    return {
        "source": "SEC EDGAR",
        "company_filter": company,
        "content_preview": text[:2000],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/pricing-anomalies")
async def get_pricing_anomalies(product_query: str = Query(...)):
    """Search for cross-market pricing anomalies."""
    from main import bright_data
    import config

    search_results = await bright_data.serp_search(
        f'"{product_query}" price discount sale promo site:amazon.com OR site:bestbuy.com OR site:walmart.com',
        num=10,
    )

    if not config.is_aiml_configured():
        return {
            "product": product_query,
            "results": search_results,
            "anomaly_analysis": "Configure AIML_API_KEY for AI anomaly detection.",
            "timestamp": datetime.utcnow().isoformat(),
        }

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=config.AIML_API_KEY, base_url=config.AIML_API_BASE_URL)
    results_text = "\n".join([f"- {r['title']}: {r['snippet']}" for r in search_results[:5]])

    resp = await client.chat.completions.create(
        model=config.AIML_MODEL,
        messages=[
            {"role": "system", "content": "You are a market analyst. Detect pricing anomalies."},
            {
                "role": "user",
                "content": (
                    f"Product: {product_query}\n\nSearch results:\n{results_text}\n\n"
                    "Identify any pricing anomalies (unusual discounts, price cuts, promotions). "
                    "Return JSON: anomalies_found (bool), anomalies (list of dicts with platform+price+context), "
                    "summary (string), impact (High/Medium/Low)."
                ),
            },
        ],
        temperature=0.2,
    )
    raw = resp.choices[0].message.content or "{}"
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    try:
        analysis = json.loads(raw)
    except Exception:
        analysis = {"raw": raw}

    return {
        "product": product_query,
        "results": search_results,
        "anomaly_analysis": analysis,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/alt-data")
async def get_alt_data(query: str = Query(...)):
    """Fetch alternative data signals (job postings, web traffic trends)."""
    from main import bright_data

    job_results = await bright_data.serp_search(
        f'"{query}" hiring jobs "we\'re hiring" layoff 2025',
        num=5,
    )
    traffic_results = await bright_data.serp_search(
        f'"{query}" web traffic growth revenue Q1 Q2 2025',
        num=5,
    )
    return {
        "company": query,
        "hiring_signals": job_results,
        "traffic_signals": traffic_results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/memory/related")
async def get_related_finance_insights(query: str):
    from main import memory_graph
    results = await memory_graph.search_related(query, track=Track.FINANCE)
    return {"query": query, "related": results}
