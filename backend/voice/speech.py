"""
Speechmatics integration — voice-to-intelligence pipeline.

STT (Speechmatics) converts voice commands to text.
TTS is handled client-side via the browser's Web Speech API.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import re

import httpx

import config

logger = logging.getLogger(__name__)


class SpeechmaticsClient:
    def __init__(self):
        self.api_key = config.SPEECHMATICS_API_KEY
        self.base_url = config.SPEECHMATICS_BASE_URL

    async def transcribe(self, audio_bytes: bytes, language: str = "en", fmt: str = "wav") -> str:
        """
        Submit audio to Speechmatics ASR and return the transcript.
        Falls back to a demo transcript if the API key is not configured.
        """
        if not self.api_key:
            logger.info("Speechmatics not configured — returning demo transcript")
            return "Switch to security track"

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Step 1: Create a job
        job_config = {
            "type": "transcription",
            "transcription_config": {"language": language, "operating_point": "enhanced"},
        }
        files = {
            "config": (None, json.dumps(job_config), "application/json"),
            "data_file": (f"audio.{fmt}", audio_bytes, f"audio/{fmt}"),
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            create_resp = await client.post(
                f"{self.base_url}/jobs/",
                files=files,
                headers=headers,
            )
            create_resp.raise_for_status()
            job_id = create_resp.json()["id"]

            # Step 2: Poll for completion
            import asyncio
            for _ in range(60):
                await asyncio.sleep(2)
                status_resp = await client.get(
                    f"{self.base_url}/jobs/{job_id}/",
                    headers=headers,
                )
                data = status_resp.json()
                if data.get("job", {}).get("status") == "done":
                    break

            # Step 3: Retrieve transcript
            transcript_resp = await client.get(
                f"{self.base_url}/jobs/{job_id}/transcript",
                params={"format": "txt"},
                headers=headers,
            )
            return transcript_resp.text.strip()

    async def transcribe_base64(self, audio_b64: str, language: str = "en", fmt: str = "wav") -> str:
        audio_bytes = base64.b64decode(audio_b64)
        return await self.transcribe(audio_bytes, language=language, fmt=fmt)


class CommandParser:
    """Maps transcript text to NexusIntel commands."""

    TRACK_PATTERNS = {
        "gtm": r"\b(gtm|go.?to.?market|sales|competitor|lead)\b",
        "finance": r"\b(finance|financial|market|stock|regulatory|filing)\b",
        "security": r"\b(security|threat|breach|compliance|vulnerability)\b",
    }

    def parse(self, transcript: str) -> dict:
        text = transcript.lower().strip()

        # Track switch command
        for track, pattern in self.TRACK_PATTERNS.items():
            if re.search(pattern, text):
                return {
                    "command_type": "track_switch",
                    "track": track,
                    "transcript": transcript,
                    "result": f"Switching to {track.upper()} track",
                }

        # Briefing request
        if any(w in text for w in ["brief", "briefing", "summary", "read", "report"]):
            return {
                "command_type": "briefing",
                "transcript": transcript,
                "result": "Generating latest briefing...",
            }

        # Search request
        if any(w in text for w in ["search", "find", "look up", "analyze", "check"]):
            return {
                "command_type": "search",
                "transcript": transcript,
                "result": f"Searching for: {transcript}",
            }

        # Status request
        if any(w in text for w in ["status", "engine", "running", "monitoring"]):
            return {
                "command_type": "status",
                "transcript": transcript,
                "result": "Fetching engine status...",
            }

        return {
            "command_type": "unknown",
            "transcript": transcript,
            "result": f"Command not recognized: '{transcript}'",
        }
