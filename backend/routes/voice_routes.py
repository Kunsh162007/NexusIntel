"""
Voice endpoints — Speechmatics STT + command parsing.
"""
from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException

from models import VoiceCommandRequest, VoiceCommandResponse

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/command", response_model=VoiceCommandResponse)
async def voice_command(request: VoiceCommandRequest):
    """
    Receive base64-encoded audio, transcribe via Speechmatics,
    parse the command, and return a structured response.
    """
    from main import speech_client, command_parser

    transcript = await speech_client.transcribe_base64(
        request.audio_base64,
        language=request.language,
        fmt=request.format,
    )

    parsed = command_parser.parse(transcript)
    return VoiceCommandResponse(
        transcript=transcript,
        command_type=parsed["command_type"],
        result=parsed.get("result"),
        track_switched_to=parsed.get("track"),
    )


@router.post("/upload")
async def voice_upload(file: UploadFile = File(...), language: str = "en"):
    """Accept a raw audio file upload and return transcript + parsed command."""
    from main import speech_client, command_parser

    audio_bytes = await file.read()
    fmt = (file.filename or "audio.wav").rsplit(".", 1)[-1].lower()
    transcript = await speech_client.transcribe(audio_bytes, language=language, fmt=fmt)
    parsed = command_parser.parse(transcript)

    return {
        "transcript": transcript,
        "command": parsed,
    }


@router.get("/status")
async def voice_status():
    import config
    return {
        "speechmatics_configured": bool(config.SPEECHMATICS_API_KEY),
        "note": "TTS handled by browser Web Speech API (no server key required)",
    }
