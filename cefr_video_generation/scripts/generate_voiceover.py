"""Generate one MP3 per scene with ElevenLabs and write durations + timing to a JSON manifest.

Usage (from multilevel-video/):
  python scripts/generate_voiceover.py [--force]                       # explainer video
  python scripts/generate_voiceover.py scripts/speaking_mock1.voice.json  # speaking mock
A config may set "out_dir" / "manifest" (default public/voiceover, src/voiceover.json),
and any scene may override "elevenlabs" settings (e.g. a different voice or language).
Reads ELEVENLABS_API from ../.env (or the environment). Requires ffprobe on PATH.
A scene is re-generated only when its text, voice, model or settings change (or with --force).
"""
import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_args = argparse.ArgumentParser()
_args.add_argument("config", nargs="?", default=str(Path(__file__).parent / "scenes.json"))
_args.add_argument("--force", action="store_true")
ARGS = _args.parse_args()
CONFIG = json.loads(Path(ARGS.config).read_text(encoding="utf-8"))
OUT_DIR = ROOT / CONFIG.get("out_dir", "public/voiceover")
MANIFEST = ROOT / CONFIG.get("manifest", "src/voiceover.json")
CACHE_DIR = Path(__file__).parent / ".tts-cache" / Path(ARGS.config).stem
FORCE = ARGS.force


def api_key() -> str:
    if os.environ.get("ELEVENLABS_API"):
        return os.environ["ELEVENLABS_API"]
    for env in (ROOT / ".env", ROOT.parent / ".env"):
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("ELEVENLABS_API="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    sys.exit("ELEVENLABS_API not found")


KEY = api_key()


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return round(float(out.stdout.strip()), 3)


def synthesize(text: str, EL: dict) -> dict:
    """POST /with-timestamps -> {audio_base64, alignment:{characters, character_start_times_seconds, ...}}"""
    body = {
        "text": text,
        "model_id": EL["model_id"],
        "language_code": EL["language_code"],
        "voice_settings": EL["voice_settings"],
    }
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{EL['voice_id']}/with-timestamps"
        f"?output_format={EL['output_format']}"
    )
    for attempt in range(1, 5):
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"xi-api-key": KEY, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as res:
                return json.loads(res.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            if e.code in (429, 500, 502, 503) and attempt < 4:
                print(f"  HTTP {e.code}, retrying… {detail[:200]}")
                time.sleep(3 * attempt)
                continue
            sys.exit(f"ElevenLabs HTTP {e.code}: {detail}")
    sys.exit("ElevenLabs: gave up after retries")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    public = ROOT / "public"
    manifest = []
    for scene in CONFIG["scenes"]:
        text = scene["tts"]
        EL = {**CONFIG["elevenlabs"], **scene.get("elevenlabs", {})}
        fingerprint = hashlib.sha256(json.dumps([text, EL], sort_keys=True).encode()).hexdigest()
        audio = OUT_DIR / f"{scene['id']}.mp3"
        cache = CACHE_DIR / f"{scene['id']}.json"
        cached = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else None

        if FORCE or not audio.exists() or not cached or cached.get("fingerprint") != fingerprint:
            res = synthesize(text, EL)
            audio.write_bytes(base64.b64decode(res["audio_base64"]))
            al = res.get("normalized_alignment") or res["alignment"]
            cached = {
                "fingerprint": fingerprint,
                "characters": "".join(al["characters"]),
                "starts": [round(t, 3) for t in al["character_start_times_seconds"]],
            }
            cache.write_text(json.dumps(cached, ensure_ascii=False), encoding="utf-8")
            print(f"generated {scene['id']}")
        else:
            print(f"cached    {scene['id']}")

        manifest.append({
            "id": scene["id"],
            "text": text,
            "file": audio.relative_to(public).as_posix(),
            "durationInSeconds": duration(audio),
            # Per-character start times; lets scenes cue reveals on the exact spoken word.
            "alignment": {"characters": cached["characters"], "starts": cached["starts"]},
        })

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for m in manifest:
        print(f"{m['id']:<10} {m['durationInSeconds']:6.2f}s")
    print(f"total      {sum(m['durationInSeconds'] for m in manifest):6.2f}s")


main()
