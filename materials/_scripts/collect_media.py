"""Collect every media URL referenced by the downloaded mocks.

Walks the mock_data tree rather than regex-matching the JSON text, because many
URLs contain spaces (".../test52/PART 1.m4a") and a whitespace-delimited regex
silently drops them. Relative values are joined to the nearest declaring base:

  audio.files.<n>                      -> audio.base
  parts[].items[].options[].image      -> parts[].imageBase
  parts[].example.options[].image      -> parts[].imageBase

Writes media_urls.txt (one URL per line). Directory-only fields (audioBase,
imageBase, dictationBase, audio.base) are bases, not files, and are skipped.
"""
import json, os, glob, urllib.parse

ROOT = r"C:/temporary/multilevel_reels/materials"
RAW = os.path.join(ROOT, "raw")

MEDIA_EXT = (".mp3", ".m4a", ".wav", ".ogg",
             ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")
# Article timing tracks are .json sidecars that the player needs.
DATA_EXT = (".json",)
BASE_KEYS = {"audioBase", "imageBase", "dictationBase", "base", "topicBase"}


def join(base, rel):
    if not base:
        return None
    if not base.endswith("/"):
        base += "/"
    return base + str(rel).lstrip("/")


def is_media(s, allow_json=False):
    low = s.lower().split("?")[0]
    return low.endswith(MEDIA_EXT) or (allow_json and low.endswith(DATA_EXT))


def collect_part(part, urls):
    """Cambridge listening: option images are relative to the part's imageBase."""
    if not isinstance(part, dict):
        return
    ibase = part.get("imageBase")
    items = part.get("items")
    buckets = list(items) if isinstance(items, list) else []
    ex = part.get("example")
    if isinstance(ex, dict):
        buckets.append(ex)
    for item in buckets:
        if not isinstance(item, dict):
            continue
        cands = [item.get("image")]
        opts = item.get("options")
        for opt in (opts if isinstance(opts, list) else []):
            if isinstance(opt, dict):
                cands.append(opt.get("image"))
        for c in cands:
            if isinstance(c, str) and c and not c.startswith("http"):
                u = join(ibase, c)
                if u:
                    urls.add(u)


def walk(node, urls, audio_base=None):
    if isinstance(node, dict):
        ab = node.get("audio")
        if isinstance(ab, dict) and isinstance(ab.get("base"), str):
            base = ab["base"]
            files = ab.get("files")
            for v in (files.values() if isinstance(files, dict) else []):
                if isinstance(v, str) and not v.startswith("http"):
                    u = join(base, v)
                    if u:
                        urls.add(u)
        parts = node.get("parts")
        if isinstance(parts, list):
            for part in parts:
                collect_part(part, urls)
        for k, v in node.items():
            if k in BASE_KEYS and isinstance(v, str):
                continue  # a directory, not a file
            walk(v, urls, audio_base)
    elif isinstance(node, list):
        for v in node:
            walk(v, urls, audio_base)
    elif isinstance(node, str):
        s = node.strip()
        if s.startswith("http") and is_media(s, allow_json=True):
            urls.add(s)


def main():
    urls = set()
    per_type = {}
    for f in sorted(glob.glob(os.path.join(RAW, "*.json"))):
        t = os.path.basename(f)[:-5]
        before = len(urls)
        rows = json.load(open(f, encoding="utf-8"))
        for r in rows:
            walk(r.get("mock_data"), urls)
        per_type[t] = len(urls) - before

    out = sorted(urls)
    with open(os.path.join(ROOT, "media_urls.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))

    # How many contain a space — the ones the old regex pass dropped.
    spaced = sum(1 for u in out if " " in u or "%20" in u)
    for t in sorted(per_type):
        print("%-22s +%d new urls" % (t, per_type[t]))
    print("TOTAL unique media urls:", len(out), "| containing spaces:", spaced)


if __name__ == "__main__":
    main()
