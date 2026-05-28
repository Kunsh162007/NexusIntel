"""
TriggerWare.ai integration — event-driven action layer.

When the Auto-Focus Engine confirms a high-impact signal, this module fires
the configured webhooks automatically (CRM updates, Slack alerts, etc.).
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import httpx

import config

if TYPE_CHECKING:
    from models import InsightBrief, ImpactLevel

logger = logging.getLogger(__name__)

# Impact levels that trigger an alert (configure via env if needed)
ALERT_IMPACT_LEVELS = {"Critical", "High"}


class TriggerClient:
    def __init__(self):
        self.api_key = config.TRIGGERWARE_API_KEY
        self.base_url = config.TRIGGERWARE_BASE_URL
        self.webhook_url = config.TRIGGERWARE_WEBHOOK_URL
        self._fired_count = 0

    # ── Core fire method ──────────────────────────────────────────────────

    async def fire_alert(self, brief: "InsightBrief"):
        if brief.impact not in ALERT_IMPACT_LEVELS:
            return

        payload = self._build_payload(brief)

        # 1. Fire to configured generic webhook (TriggerWare or any endpoint)
        if self.webhook_url:
            await self._post_webhook(self.webhook_url, payload)

        # 2. Fire via TriggerWare.ai REST API if configured
        if self.api_key:
            await self._triggerware_api(brief, payload)

        self._fired_count += 1
        logger.info(f"Alert fired for: {brief.title} (total={self._fired_count})")

    # ── TriggerWare.ai API ────────────────────────────────────────────────

    async def _triggerware_api(self, brief: "InsightBrief", payload: dict):
        """
        POST to TriggerWare.ai to create and immediately fire a trigger event.
        Replace this endpoint with the actual TriggerWare API when available.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "trigger_name": f"nexusintel_{brief.track.value}_alert",
            "event": "anomaly_detected",
            "data": payload,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/triggers/fire",
                    json=body,
                    headers=headers,
                )
                if resp.status_code not in (200, 201, 202):
                    logger.warning(
                        f"TriggerWare returned {resp.status_code}: {resp.text[:200]}"
                    )
        except Exception as exc:
            logger.warning(f"TriggerWare API call failed: {exc}")

    # ── Generic webhook ───────────────────────────────────────────────────

    async def _post_webhook(self, url: str, payload: dict):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=payload)
                logger.info(f"Webhook fired to {url} → {resp.status_code}")
        except Exception as exc:
            logger.warning(f"Webhook POST to {url} failed: {exc}")

    # ── Payload builder ───────────────────────────────────────────────────

    def _build_payload(self, brief: "InsightBrief") -> dict:
        return {
            "system": "NexusIntel AI",
            "event_type": "critical_insight_brief",
            "track": brief.track.value,
            "impact": brief.impact,
            "title": brief.title,
            "summary": brief.summary,
            "recommendations": brief.recommendations,
            "source_url": brief.source_url,
            "source_name": brief.source_name,
            "cross_track_links": brief.cross_track_links,
            "timestamp": brief.timestamp.isoformat(),
            "insight_id": brief.id,
        }

    def get_stats(self) -> dict:
        return {"alerts_fired": self._fired_count, "webhook_configured": bool(self.webhook_url)}
