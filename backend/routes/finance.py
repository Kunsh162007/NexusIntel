"""
Finance & Market Intelligence track — alt-data, regulatory filings, pricing anomalies.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from models import SearchQuery, Track

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

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
        "timestamp": _now(),
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

    try:
        html = await bright_data.fetch_url(url)
        text = bright_data.extract_text(html)
    except Exception as exc:
        logger.warning(f"SEC fetch failed: {exc}")
        return {
            "source": "SEC EDGAR",
            "company_filter": company,
            "content_preview": "",
            "error": f"Could not fetch SEC EDGAR: {str(exc)[:200]}",
            "timestamp": _now(),
        }

    if not text.strip():
        return {
            "source": "SEC EDGAR",
            "company_filter": company,
            "content_preview": "",
            "error": "SEC EDGAR returned no readable content (proxy or CAPTCHA may have blocked the request).",
            "timestamp": _now(),
        }

    return {
        "source": "SEC EDGAR",
        "company_filter": company,
        "content_preview": text[:2000],
        "timestamp": _now(),
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
            "timestamp": _now(),
        }

    # Short-circuit: no SERP results means there's nothing real to analyze.
    # Without this the LLM will happily hallucinate "anomalies" for a query
    # like "garbledfakeproductxyz".
    if not search_results:
        return {
            "product": product_query,
            "results": [],
            "anomaly_analysis": {
                "anomalies_found": False,
                "anomalies": [],
                "summary": f"No public pricing data found for '{product_query}'. The product name may be misspelled or have no online retail presence.",
                "impact": "Low",
            },
            "timestamp": _now(),
        }

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=config.AIML_API_KEY, base_url=config.AIML_API_BASE_URL)
    results_text = "\n".join([f"- {r['title']}: {r['snippet']}" for r in search_results[:5]])

    resp = await client.chat.completions.create(
        model=config.AIML_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a market analyst. Detect pricing anomalies ONLY when the "
                    "search results actually mention the specified product with concrete "
                    "prices or discounts. Do not invent data. If results are off-topic, "
                    "missing prices, or unrelated to the product, set anomalies_found=false "
                    "and explain why in the summary."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Product: {product_query}\n\nSearch results:\n{results_text}\n\n"
                    "Identify any pricing anomalies (unusual discounts, price cuts, promotions) "
                    "ONLY if the results above contain real pricing for this exact product. "
                    "Return JSON: anomalies_found (bool), anomalies (list of dicts with platform+price+context), "
                    "summary (string), impact (High/Medium/Low). "
                    "If no relevant data, return anomalies_found=false with an empty anomalies list."
                ),
            },
        ],
        temperature=0.2,
    )
    raw = _FENCE_RE.sub("", (resp.choices[0].message.content or "{}").strip()).strip()
    try:
        analysis = json.loads(raw)
    except Exception:
        analysis = {"raw": raw}

    return {
        "product": product_query,
        "results": search_results,
        "anomaly_analysis": analysis,
        "timestamp": _now(),
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
        "timestamp": _now(),
    }


@router.get("/memory/related")
async def get_related_finance_insights(query: str):
    from main import memory_graph
    results = await memory_graph.search_related(query, track=Track.FINANCE)
    return {"query": query, "related": results}
