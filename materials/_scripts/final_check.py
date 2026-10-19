"""Final verification: every referenced asset has a local file; report totals."""
import json, os, collections, urllib.parse

ROOT = r"C:/temporary/multilevel_reels/materials"
MEDIA = os.path.join(ROOT, "media")


def dest_for(url):
    u = urllib.parse.urlsplit(url)
    rel = urllib.parse.unquote(u.path).lstrip("/").replace(":", "-")
    return os.path.join(MEDIA, rel.replace("/", os.sep))


def load(name):
    p = os.path.join(ROOT, name)
    return [l.strip() for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []


missing = []
present = 0
byext = collections.Counter()
bytes_by_ext = collections.Counter()
urls = list(dict.fromkeys(load("media_urls.txt") + load("audio_urls.txt") + load("image_urls.txt")))
for url in urls:
    d = dest_for(url)
    if os.path.exists(d) and os.path.getsize(d) > 0:
        present += 1
        ext = os.path.splitext(d)[1].lower()
        byext[ext] += 1
        bytes_by_ext[ext] += os.path.getsize(d)
    else:
        missing.append(url)

print("referenced assets present: %d   missing: %d" % (present, len(missing)))
if missing:
    with open(os.path.join(ROOT, "media_missing.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(missing))
for e, n in byext.most_common():
    print("   %-6s %5d files  %8.1f MB" % (e, n, bytes_by_ext[e] / 1e6))
if missing:
    for m in missing[:10]:
        print("   MISSING", m)

# JSON mocks on disk
man = json.load(open(os.path.join(ROOT, "manifest.json"), encoding="utf-8"))
ok = sum(1 for m in man if os.path.exists(os.path.join(ROOT, m["file"])))
print("\nmock JSON files on disk: %d / %d" % (ok, len(man)))

total = 0
for dirpath, _, files in os.walk(ROOT):
    for f in files:
        total += os.path.getsize(os.path.join(dirpath, f))
print("materials/ total size: %.2f GB" % (total / 1e9))
