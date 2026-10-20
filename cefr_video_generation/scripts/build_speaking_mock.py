"""Extract the questions of Speaking mock <n> into src/speaking/mock<n>.json
(prompt, part, timings, local media paths + measured audio durations) and create any missing sfx.

Usage (from the project root):  python scripts/build_speaking_mock.py [n]   (default 1)
Mock 1 is read from data/speaking_mock1.json, any other from the repo's
materials/cefr-speaking/<nnn>-*.json export. Question audio and images are downloaded into
public/speaking-mock<n>/ when missing (they are not committed, matching the repo's
materials/media/ convention).
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
N = int(sys.argv[1]) if len(sys.argv) > 1 else 1
SOURCE = (
    ROOT / "data" / "speaking_mock1.json"
    if N == 1
    else next((ROOT.parent / "materials" / "cefr-speaking").glob(f"{N:03d}-*.json"))
)
MOCK = json.loads(SOURCE.read_text(encoding="utf-8"))
MEDIA_DIR = f"speaking-mock{N}"
MEDIA = ROOT / "public" / MEDIA_DIR
SFX = ROOT / "public" / "sfx"

# Fixes for tags the export leaves as placeholders.
TOPIC_OVERRIDES = {2: {"p2Topic": "A personal achievement"}}


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return round(float(out.stdout.strip()), 3)


def fetch(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=180) as res:
                dest.write_bytes(res.read())
            print(f"downloaded {dest.name}")
            return
        except OSError as e:
            if attempt == 3:
                raise
            print(f"  retry {attempt} for {dest.name}: {e}")
            time.sleep(3 * attempt)


def fetch_media(data: dict) -> None:
    for q in data["questions"]:
        fetch(q["audioFile"], MEDIA / f"q{q['number']}.mp3")
        if q.get("contextImage"):
            fetch(q["contextImage"], MEDIA / f"q{q['number']}-context.jpg")
    fetch(data["images"]["img1"], MEDIA / "img1.png")
    fetch(data["images"]["img2"], MEDIA / "img2.png")


def part_of(q: dict) -> str:
    if q["part"].startswith("Part 1"):
        return "1.2" if q.get("hasImages") else "1.1"
    return "2" if q["part"].startswith("Part 2") else "3"


def make_sfx() -> None:
    # The noise burst in click.wav is random, so only synthesise what is missing.
    if all((SFX / f).exists() for f in ("start.wav", "end.wav", "click.wav", "logo.wav")):
        return
    SFX.mkdir(parents=True, exist_ok=True)
    tone = "sine=f={f}:d={d}:sample_rate=48000,afade=t=in:d=0.01,afade=t=out:st={fo}:d={fd},volume={v}"
    # Two-note rising chime = "start speaking"; single low tone = "time is up".
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", tone.format(f=880, d=0.22, fo=0.12, fd=0.1, v=0.5),
        "-f", "lavfi", "-i", tone.format(f=1320, d=0.45, fo=0.15, fd=0.3, v=0.5),
        "-filter_complex", "[0][1]concat=n=2:v=0:a=1", str(SFX / "start.wav"),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", tone.format(f=520, d=0.6, fo=0.2, fd=0.4, v=0.5),
        str(SFX / "end.wav"),
    ], check=True)
    # Short filtered noise burst = mouse click (outro subscribe/save buttons).
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "anoisesrc=d=0.03:c=white:a=0.6:r=48000",
        "-af", "highpass=f=1800,afade=t=out:st=0.005:d=0.025",
        str(SFX / "click.wav"),
    ], check=True)
    # Soft bell (C6 + G6, long decay) under the logo reveal.
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "sine=f=1046.5:d=2.4:sample_rate=48000",
        "-f", "lavfi", "-i", "sine=f=1568:d=2.4:sample_rate=48000",
        "-filter_complex",
        "[0]volume=0.35,afade=t=in:d=0.01,afade=t=out:st=0.05:d=2.3:curve=exp[a];"
        "[1]volume=0.18,adelay=90|90,afade=t=in:st=0.09:d=0.01,afade=t=out:st=0.15:d=2.2:curve=exp[b];"
        "[a][b]amix=inputs=2:normalize=0",
        str(SFX / "logo.wav"),
    ], check=True)


def main() -> None:
    data = MOCK["mock_data"]
    fetch_media(data)
    questions = []
    for q in data["questions"]:
        n = q["number"]
        audio = MEDIA / f"q{n}.mp3"
        item = {
            "number": n,
            "part": part_of(q),
            "prompt": q["prompt"].strip(),
            "audio": f"{MEDIA_DIR}/q{n}.mp3",
            "audioDuration": duration(audio),
            "prepTime": q["prepTime"],
            "speakTime": q["speakTime"],
        }
        if q.get("hasImages"):
            item["images"] = [f"{MEDIA_DIR}/img1.png", f"{MEDIA_DIR}/img2.png"]
        if q.get("contextImage"):
            item["contextImage"] = f"{MEDIA_DIR}/q{n}-context.jpg"
        if q.get("bulletPoints"):
            item["bulletPoints"] = q["bulletPoints"]
        if q.get("debatePoints"):
            item["debatePoints"] = q["debatePoints"]
        questions.append(item)

    out = {
        "number": N,
        "title": MOCK["title"],
        "topics": {**data["tags"], **TOPIC_OVERRIDES.get(N, {})},
        "questions": questions,
    }
    dest = ROOT / "src" / "speaking" / f"mock{N}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    make_sfx()
    for q in questions:
        print(f"Q{q['number']} {q['part']:<4} audio {q['audioDuration']:5.2f}s prep {q['prepTime']:>3}s speak {q['speakTime']:>3}s")


main()
