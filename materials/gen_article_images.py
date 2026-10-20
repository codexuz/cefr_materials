"""
Generate one editorial illustration per article with the OpenAI images API.

Needs a key in the environment -- nothing is written and nothing is charged
without it:

    setx OPENAI_API_KEY "sk-..."      # Windows, then reopen the shell
    export OPENAI_API_KEY="sk-..."    # bash

    python gen_article_images.py            # first 10 articles
    python gen_article_images.py 10 --force # redo ones already generated

Images land in media/article-illustrations/article-NN.png and are picked up by
build_article_book.py automatically on the next build. Existing files are
skipped, so a re-run costs nothing.

Each image costs money on your OpenAI account. Pass --dry-run to print the
prompts and the image count without calling the API.
"""
import base64
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
ART_DIR = os.path.join(ROOT, "article")
OUT_DIR = os.path.join(ROOT, "media", "article-illustrations")

API_URL = "https://api.openai.com/v1/images/generations"
MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")
SIZE = os.environ.get("OPENAI_IMAGE_SIZE", "1536x1024")   # 3:2, matches the figure
DEFAULT_COUNT = 10

# The book's palette, so generated art sits beside the brand rather than fighting it.
# The book prints every picture in high-contrast black and white and lets its
# colour blocks carry the colour, so ask for a strong tonal photograph rather
# than a colour scheme.
STYLE = (
    "Editorial magazine photograph, documentary style, strong directional light, deep "
    "shadows and clean highlights so it reads well in black and white, simple uncluttered "
    "composition with room around the subject. No text, no words, no letters, no numbers, "
    "no logos, no watermarks. Wide landscape framing."
)


def plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def load(count):
    out = []
    for fn in sorted(glob.glob(os.path.join(ART_DIR, "*.json")))[:count]:
        with open(fn, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def build_prompt(art):
    md = art["mock_data"]
    title = md.get("title") or art.get("title") or ""
    gist = plain(md.get("passageB1") or md.get("passage"))[:320]
    return (f'Editorial illustration for an English-learning magazine article titled '
            f'"{title}". The article is about: {gist} '
            f"Illustrate the idea conceptually, not literally. {STYLE}")


def generate(prompt, key):
    body = json.dumps({"model": MODEL, "prompt": prompt, "size": SIZE, "n": 1}).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        payload = json.load(resp)
    item = payload["data"][0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    with urllib.request.urlopen(item["url"], timeout=300) as img:   # dall-e-3 style
        return img.read()


def main():
    args = sys.argv[1:]
    count = next((int(a) for a in args if a.isdigit()), DEFAULT_COUNT)
    force = "--force" in args
    dry = "--dry-run" in args

    key = os.environ.get("OPENAI_API_KEY")
    if not key and not dry:
        print("OPENAI_API_KEY is not set -- nothing generated, nothing charged.")
        print("Set it and re-run, or use --dry-run to see the prompts.")
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    arts = load(count)
    todo = []
    for i, art in enumerate(arts, 1):
        dest = os.path.join(OUT_DIR, f"article-{i:02d}.png")
        if os.path.exists(dest) and not force:
            print(f"  {i:02d} already generated, skipping")
            continue
        todo.append((i, art, dest))

    if dry:
        print(f"Would generate {len(todo)} image(s) with {MODEL} at {SIZE}:\n")
        for i, art, _ in todo:
            print(f"--- {i:02d} {art['mock_data'].get('title')}")
            print(build_prompt(art)[:400], "\n")
        return 0

    print(f"Generating {len(todo)} image(s) with {MODEL} at {SIZE}...")
    failed = 0
    for i, art, dest in todo:
        title = art["mock_data"].get("title") or art.get("title")
        try:
            data = generate(build_prompt(art), key)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            print(f"  {i:02d} {title}: HTTP {e.code} {detail}")
            failed += 1
            continue
        except Exception as e:                                   # noqa: BLE001
            print(f"  {i:02d} {title}: {e}")
            failed += 1
            continue
        with open(dest, "wb") as f:
            f.write(data)
        print(f"  {i:02d} {title} -> {os.path.relpath(dest, ROOT)} ({len(data) // 1024} KB)")

    print(f"Done. {len(todo) - failed} generated, {failed} failed.")
    print("Re-run build_article_book.py to place them in the book.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
