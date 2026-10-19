"""Split downloaded mock_tests rows into per-item JSON files + build manifest.json.

Media URLs are collected by collect_media.walk, which walks the data tree;
an earlier regex over the JSON text silently dropped every URL containing a
space (".../test52/PART 1.m4a").
"""
import json, os, re, glob, sys

# -I drops the script's own directory from sys.path; add it back explicitly
# (this directory holds only our scripts, never the downloaded data).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect_media import walk as collect_walk

ROOT = r"C:/temporary/multilevel_reels/materials"
RAW = os.path.join(ROOT, "raw")


def safe(s):
    s = re.sub(r'[\\/:*?"<>|]+', "-", str(s)).strip()
    return re.sub(r"\s+", " ", s)[:90]


manifest = []
counts = {}

for f in sorted(glob.glob(os.path.join(RAW, "*.json"))):
    mtype = os.path.basename(f)[:-5]
    rows = json.load(open(f, encoding="utf-8"))
    outdir = os.path.join(ROOT, mtype)
    os.makedirs(outdir, exist_ok=True)
    # Purge stale per-item files so a rename upstream leaves no orphans.
    for old in glob.glob(os.path.join(outdir, "*.json")):
        os.remove(old)
    for r in rows:
        num = r.get("mock_number")
        # id keeps the name unique for the Learn types, where mock_number
        # repeats or is null across hundreds of rows.
        name = "%s-%s-id%s.json" % (
            str(num if num is not None else 0).zfill(3),
            safe(r.get("title") or "untitled"),
            r.get("id"))
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as fh:
            json.dump(r, fh, ensure_ascii=False, indent=1)
        md = r.get("mock_data")
        urls = set()
        collect_walk(md, urls)
        manifest.append({
            "id": r.get("id"),
            "mock_type": mtype,
            "mock_number": num,
            "title": r.get("title"),
            "status": r.get("status"),
            "file": "%s/%s" % (mtype, name),
            "media_count": len(urls),
            "bytes": len(json.dumps(md, ensure_ascii=False)),
        })
    counts[mtype] = len(rows)

with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, ensure_ascii=False, indent=1)

for k in sorted(counts):
    print("%-22s %4d items" % (k, counts[k]))
print("TOTAL items", len(manifest))
