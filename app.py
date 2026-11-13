"""Kirana Voice Counter: speak a Hinglish order, get an itemised bill read back to you.

Run:  GNANI_API_KEY=... python app.py   then open http://localhost:8000
Needs ffmpeg on PATH (browser recordings are converted to 16 kHz WAV for Prisma).
"""
import json
import os
import subprocess
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import gnani
from kirana import CATALOG, parse_order, spoken_summary

ROOT = Path(__file__).parent
MAX_AUDIO = 5 * 1024 * 1024


def to_wav16k(raw: bytes) -> bytes:
    """Convert whatever the browser recorded (webm/ogg/mp4) to 16 kHz mono WAV."""
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", "pipe:0", "-ar", "16000", "-ac", "1", "-t", "30", "-f", "wav", "pipe:1"],
        input=raw, capture_output=True, timeout=30,
    )
    if p.returncode != 0 or not p.stdout:
        raise ValueError("Could not read the recording: " + p.stderr.decode()[:150])
    return p.stdout


def bill_json(bill, transcript_meta=None):
    return {
        "transcript": bill.transcript,
        "lines": [asdict(l) for l in bill.lines],
        "total": bill.total,
        "unmatched": bill.unmatched,
        "summary": spoken_summary(bill),
        "language": (transcript_meta or {}).get("detected_language_code"),
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        if n > MAX_AUDIO:
            raise ValueError("Upload too large")
        return self.rfile.read(n)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/catalog":
            self._send(200, {k: {"price": v[0], "unit": v[1]} for k, v in CATALOG.items()})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        try:
            if self.path == "/api/order":
                meta = gnani.transcribe(to_wav16k(self._body()))
                self._send(200, bill_json(parse_order(meta["transcript"]), meta))
            elif self.path == "/api/text":
                text = json.loads(self._body())["text"]
                self._send(200, bill_json(parse_order(text)))
            elif self.path == "/api/speak":
                text = json.loads(self._body())["text"][:400]
                self._send(200, gnani.speak(text), "audio/wav")
            else:
                self._send(404, {"error": "not found"})
        except gnani.GnaniError as e:
            self._send(502, {"error": str(e)})
        except Exception as e:  # bad input, ffmpeg failure
            self._send(400, {"error": str(e)})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Kirana Voice Counter on http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
