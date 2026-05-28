"""
Security & Compliance track — threat monitoring, credential leaks, regulatory changes.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Query

from models import Track

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/security", tags=["security"])


@router.get("/insights")
async def get_security_insights(limit: int = 20):
    from main import engine
    insights = engine.get_insights(track=Track.SECURITY, limit=limit)
    return [i.model_dump(mode="json") for i in insights]


@router.get("/threat-scan")
async def threat_scan(query: str = Query(...)):
    """Scan for external threats related to a keyword (brand, product, company)."""
    from main import bright_data
    import config

    results = await bright_data.serp_search(
        f'"{query}" data breach leak vulnerability CVE threat 2024 2025',
        num=10,
    )

    if not config.is_aiml_configured():
        return {
            "query": query,
            "results": results,
            "threat_summary": "Configure AIML_API_KEY for AI threat analysis.",
            "timestamp": datetime.utcnow().isoformat(),
        }

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=config.AIML_API_KEY, base_url=config.AIML_API_BASE_URL)
    results_text = "\n".join([f"- {r['title']}: {r['snippet']}" for r in results[:6]])

    resp = await client.chat.completions.create(
        model=config.AIML_MODEL,
        messages=[
            {"role": "system", "content": "You are a cybersecurity threat analyst."},
            {
                "role": "user",
                "content": (
                    f"Query: {query}\n\nSearch results:\n{results_text}\n\n"
                    "Analyze for security threats. Return JSON with: "
                    "threats_detected (bool), threats (list: type+severity+description), "
                    "overall_severity (Critical/High/Medium/Low/None), "
                    "recommendations (list), summary (string)."
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
        "query": query,
        "results": results,
        "threat_analysis": analysis,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/credential-check")
async def credential_check(domain: str = Query(...)):
    """Check for public mentions of credential leaks for a domain."""
    from main import bright_data

    results = await bright_data.serp_search(
        f'site:haveibeenpwned.com OR "data breach" OR "credential leak" "{domain}" 2024 2025',
        num=8,
    )
    return {
        "domain": domain,
        "results": results,
        "disclaimer": "Results sourced from public web. For definitive breach info, check haveibeenpwned.com directly.",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/brand-monitor")
async def brand_monitor(brand: str = Query(...)):
    """Monitor for brand impersonation and reputational threats."""
    from main import bright_data

    impersonation = await bright_data.serp_search(
        f'"{brand}" fake scam phishing impersonation "not affiliated"',
        num=5,
    )
    reputation = await bright_data.serp_search(
        f'"{brand}" review complaint lawsuit fraud negative 2025',
        num=5,
    )
    return {
        "brand": brand,
        "impersonation_signals": impersonation,
        "reputation_signals": reputation,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/regulatory-changes")
async def regulatory_changes(region: str = Query("global")):
    """Fetch recent regulatory changes that may affect compliance."""
    from main import bright_data

    region_terms = {
        "us": "CCPA HIPAA SOC2 FTC SEC",
        "eu": "GDPR NIS2 DORA AI Act",
        "global": "GDPR CCPA SOC2 ISO27001 NIS2",
    }.get(region.lower(), "compliance regulation 2025")

    results = await bright_data.serp_search(
        f"new regulation compliance update {region_terms} 2025",
        num=8,
    )
    return {
        "region": region,
        "regulatory_updates": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/cve-feed")
async def cve_feed(product: str | None = Query(None)):
    """Fetch recent CVEs from CISA advisories."""
    from main import bright_data

    url = "https://www.cisa.gov/news-events/cybersecurity-advisories"
    html = await bright_data.fetch_url(url)
    text = bright_data.extract_text(html)

    query = f"CVE vulnerability {product}" if product else "critical CVE vulnerability"
    serp_results = await bright_data.serp_search(f"site:nvd.nist.gov {query} 2025", num=5)

    return {
        "source": "CISA Advisories + NVD",
        "product_filter": product,
        "cisa_preview": text[:1500],
        "nvd_results": serp_results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/memory/related")
async def get_related_security_insights(query: str):
    from main import memory_graph
    results = await memory_graph.search_related(query, track=Track.SECURITY)
    return {"query": query, "related": results}
