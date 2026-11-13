"""Thin client for Gnani AI Prisma (speech to text) and Timbre (text to speech)."""
import os
import requests

STT_URL = "https://api.vachana.ai/stt/v3"
TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"


class GnaniError(RuntimeError):
    pass


def _key() -> str:
    key = os.environ.get("GNANI_API_KEY", "").strip()
    if not key:
        raise GnaniError("Set GNANI_API_KEY (create one at app.gnani.ai).")
    return key


def transcribe(wav_bytes: bytes, language_code: str = "indic-auto") -> dict:
    """Prisma v3.0 speech to text. Clips up to 30 seconds."""
    r = requests.post(
        STT_URL,
        headers={"X-API-Key-ID": _key()},
        files={"audio_file": ("order.wav", wav_bytes, "audio/wav")},
        data={"model": "prisma-v3.0", "language_code": language_code},
        timeout=60,
    )
    if r.status_code != 200 or not r.json().get("success"):
        raise GnaniError(f"STT failed ({r.status_code}): {r.text[:200]}")
    return r.json()


def speak(text: str, voice: str = "Nalini", language: str = "hi-en") -> bytes:
    """Timbre v2.5 text to speech. Returns WAV bytes."""
    r = requests.post(
        TTS_URL,
        headers={"X-API-Key-ID": _key(), "Content-Type": "application/json"},
        json={
            "text": text,
            "voice": voice,
            "model": "timbre-v2.5",
            "language": language,
            "speed": 1.0,
            "audio_config": {"sample_rate": 16000, "container": "wav"},
        },
        timeout=60,
    )
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("audio"):
        raise GnaniError(f"TTS failed ({r.status_code}): {r.text[:200]}")
    return r.content
