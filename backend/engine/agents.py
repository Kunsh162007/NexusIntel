"""
LangChain agents powered by Bright Data tools and AI/ML API.
Each track gets its own specialised agent.  The Auto-Focus Engine also uses
a generic deep-dive agent for anomaly investigation.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

import config

if TYPE_CHECKING:
    from engine.bright_data import BrightDataClient


# ── LLM factory ──────────────────────────────────────────────────────────────

def _get_llm(temperature: float = 0.2) -> ChatOpenAI:
    if config.is_aiml_configured():
        return ChatOpenAI(
            model=config.AIML_MODEL,
            openai_api_key=config.AIML_API_KEY,
            openai_api_base=config.AIML_API_BASE_URL,
            temperature=temperature,
        )
    raise RuntimeError("AIML_API_KEY is not configured — cannot create LLM.")


# ── Tool builders ─────────────────────────────────────────────────────────────

def build_bright_data_tools(bd: "BrightDataClient") -> list[Tool]:
    """Return LangChain Tool objects backed by Bright Data."""

    async def web_search(query: str) -> str:
        results = await bd.serp_search(query, num=5)
        if not results:
            return "No results found."
        lines = [f"[{i+1}] {r['title']}\n{r['url']}\n{r['snippet']}" for i, r in enumerate(results)]
        return "\n\n".join(lines)

    async def scrape_page(url: str) -> str:
        html = await bd.fetch_url(url.strip())
        text = bd.extract_text(html)
        return text[:4000]

    async def scrape_js_page(url: str) -> str:
        html = await bd.scraping_browser_fetch(url.strip())
        text = bd.extract_text(html)
        return text[:4000]

    return [
        Tool(
            name="web_search",
            func=None,
            coroutine=web_search,
            description=(
                "Search the live web for recent information. "
                "Input: a search query string. "
                "Returns: top search results with titles, URLs, and snippets."
            ),
        ),
        Tool(
            name="scrape_page",
            func=None,
            coroutine=scrape_page,
            description=(
                "Fetch and read a web page URL via Bright Data Web Unlocker. "
                "Bypasses CAPTCHAs and anti-bot measures. "
                "Input: a fully-qualified URL (https://...). "
                "Returns: readable page text (first 4000 chars)."
            ),
        ),
        Tool(
            name="scrape_js_page",
            func=None,
            coroutine=scrape_js_page,
            description=(
                "Fetch a JavaScript-rendered or interactive page via Scraping Browser. "
                "Use for SPAs, financial portals, dashboards. "
                "Input: a URL. Returns: rendered page text."
            ),
        ),
    ]


# ── Agent prompt ──────────────────────────────────────────────────────────────

AGENT_PROMPT = PromptTemplate.from_template(
    """You are NexusIntel's autonomous deep-dive intelligence agent.
Your job is to investigate a detected anomaly or answer a research query on the live web
using Bright Data tools and produce a structured intelligence report.

Available tools:
{tools}

Tool names: {tool_names}

Instructions:
- Use web_search to discover recent context around the anomaly.
- Use scrape_page for most pages; use scrape_js_page only for JS-heavy sites.
- Collect 3-5 pieces of concrete evidence.
- Format your FINAL ANSWER as JSON with keys:
  title, summary (2-3 sentences), key_findings (list of strings),
  impact (Critical/High/Medium/Low), recommendations (list of strings).

Begin!

Query: {input}
{agent_scratchpad}"""
)


# ── Public factory functions ──────────────────────────────────────────────────

def create_deep_dive_agent(bd: "BrightDataClient") -> AgentExecutor:
    """Generic agent for Auto-Focus anomaly investigation."""
    tools = build_bright_data_tools(bd)
    llm = _get_llm()
    agent = create_react_agent(llm, tools, AGENT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=6,
        handle_parsing_errors=True,
        return_intermediate_steps=False,
    )


# ── GTM-specialised agent ─────────────────────────────────────────────────────

GTM_PROMPT = PromptTemplate.from_template(
    """You are a Go-To-Market intelligence specialist.
Research the following competitor / lead signal and return a structured JSON report.

Tools: {tools}
Tool names: {tool_names}

Focus areas: pricing changes, product page changes, messaging shifts, hiring signals,
buyer intent indicators, and market positioning changes.

Output JSON keys: title, summary, competitor_changes (list), hiring_signals (list),
pricing_changes (list), messaging_changes (list), impact, recommendations.

Query: {input}
{agent_scratchpad}"""
)


def create_gtm_agent(bd: "BrightDataClient") -> AgentExecutor:
    tools = build_bright_data_tools(bd)
    llm = _get_llm()
    agent = create_react_agent(llm, tools, GTM_PROMPT)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=6,
                         handle_parsing_errors=True)


# ── Finance-specialised agent ─────────────────────────────────────────────────

FINANCE_PROMPT = PromptTemplate.from_template(
    """You are a Financial & Market Intelligence analyst.
Research the following financial signal and return a structured JSON report.

Tools: {tools}
Tool names: {tool_names}

Focus areas: pricing anomalies, alternative data (job postings, web traffic, freight),
regulatory filings (SEC, EU, APAC), cross-market price discrepancies, pre-earnings indicators.

Output JSON keys: title, summary, signal_type, data_points (list of dicts with source+value),
regulatory_links (list), impact_score (0-10), impact, recommendations.

Query: {input}
{agent_scratchpad}"""
)


def create_finance_agent(bd: "BrightDataClient") -> AgentExecutor:
    tools = build_bright_data_tools(bd)
    llm = _get_llm()
    agent = create_react_agent(llm, tools, FINANCE_PROMPT)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=6,
                         handle_parsing_errors=True)


# ── Security-specialised agent ────────────────────────────────────────────────

SECURITY_PROMPT = PromptTemplate.from_template(
    """You are a Security & Compliance threat analyst.
Research the following threat / compliance signal and return a structured JSON report.

Tools: {tools}
Tool names: {tool_names}

Focus areas: credential leaks, brand impersonation, threat-actor chatter on public forums,
newly published CVEs, regulatory changes (GDPR, CCPA, NIS2), reputational exposure.

Output JSON keys: title, summary, threat_type, severity (Critical/High/Medium/Low),
indicators_of_compromise (list), affected_entities (list), regulatory_references (list),
action_required (bool), recommendations.

Query: {input}
{agent_scratchpad}"""
)


def create_security_agent(bd: "BrightDataClient") -> AgentExecutor:
    tools = build_bright_data_tools(bd)
    llm = _get_llm()
    agent = create_react_agent(llm, tools, SECURITY_PROMPT)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=6,
                         handle_parsing_errors=True)
