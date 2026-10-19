"""Per-category coverage: for each mock, is every asset it references on disk?"""
import json, os, glob, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect_media import walk as collect_walk
from fetch_media import dest_for

ROOT = r"C:/temporary/multilevel_reels/materials"
RAW = os.path.join(ROOT, "raw")

print("%-22s %6s %7s %7s %s" % ("category", "items", "assets", "missing", "incomplete mocks"))
grand_a = grand_m = 0
for f in sorted(glob.glob(os.path.join(RAW, "*.json"))):
    t = os.path.basename(f)[:-5]
    rows = json.load(open(f, encoding="utf-8"))
    assets = missing = 0
    bad = []
    for r in rows:
        urls = set()
        collect_walk(r.get("mock_data"), urls)
        m = 0
        for u in urls:
            d = dest_for(u)
            if os.path.exists(d) and os.path.getsize(d) > 0:
                assets += 1
            else:
                m += 1
        missing += m
        if m:
            bad.append("#%s" % r.get("mock_number"))
    grand_a += assets
    grand_m += missing
    print("%-22s %6d %7d %7d %s" % (t, len(rows), assets, missing, " ".join(bad[:6])))
print("\nTOTAL assets resolved: %d   missing: %d" % (grand_a, grand_m))

# spot-check the mock the user flagged
rows = json.load(open(os.path.join(RAW, "cefr-listening.json"), encoding="utf-8"))
for r in rows:
    urls = set()
    collect_walk(r.get("mock_data"), urls)
    if any("/test52/" in u for u in urls):
        on = sum(1 for u in urls if os.path.exists(dest_for(u)))
        print("\ncefr-listening mock #%s (test52): %d/%d assets on disk"
              % (r.get("mock_number"), on, len(urls)))
        for u in sorted(urls):
            if "/test52/" in u:
                d = dest_for(u)
                sz = os.path.getsize(d) if os.path.exists(d) else 0
                print("   %9d bytes  %s" % (sz, os.path.relpath(d, ROOT)))
