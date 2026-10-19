"""Download the audio/image assets referenced by the downloaded mock JSON files.

Saves each URL under materials/media/<host-path>, skipping files already present.
Run:  python -I fetch_media.py [--probe]
"""
import os, sys, json, time
import urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

ROOT = r"C:/temporary/multilevel_reels/materials"
MEDIA = os.path.join(ROOT, "media")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def load(name):
    p = os.path.join(ROOT, name)
    if not os.path.exists(p):
        return []
    return [l.strip() for l in open(p, encoding="utf-8") if l.strip()]


def encode(url):
    """Percent-encode the path so URLs holding spaces are requestable.

    Already-encoded URLs must survive untouched, so unquote first and
    re-quote once rather than escaping an existing % sequence twice.
    """
    u = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(urllib.parse.unquote(u.path), safe="/")
    return urllib.parse.urlunsplit((u.scheme, u.netloc, path, u.query, u.fragment))


def dest_for(url):
    u = urllib.parse.urlsplit(url)
    rel = urllib.parse.unquote(u.path).lstrip("/")
    rel = rel.replace(":", "-")
    return os.path.join(MEDIA, rel.replace("/", os.sep))


def probe(url):
    req = urllib.request.Request(encode(url), headers=UA, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return int(r.headers.get("Content-Length") or 0)
    except Exception as e:
        return -1


def fetch(url):
    dst = dest_for(url)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return ("skip", url, os.path.getsize(dst))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    req = urllib.request.Request(encode(url), headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            tmp = dst + ".part"
            with open(tmp, "wb") as fh:
                fh.write(data)
            os.replace(tmp, dst)
            return ("ok", url, len(data))
        except Exception as e:
            if attempt == 2:
                return ("fail:%s" % e, url, 0)
            time.sleep(1.5 * (attempt + 1))


def main():
    # media_urls.txt is produced by collect_media.py, which walks the data
    # tree; the older audio/image lists came from a regex that dropped any
    # URL containing a space. Keep both so nothing already found is lost.
    urls = load("media_urls.txt") + load("audio_urls.txt") + load("image_urls.txt")
    urls = list(dict.fromkeys(urls))
    if "--probe" in sys.argv:
        sample = urls[:8]
        with ThreadPoolExecutor(8) as ex:
            for u, n in zip(sample, ex.map(probe, sample)):
                print("%12s  %s" % (n, u))
        return
    print("to fetch:", len(urls))
    ok = skip = 0
    total = 0
    failures = []
    with ThreadPoolExecutor(14) as ex:
        for i, (status, url, n) in enumerate(ex.map(fetch, urls), 1):
            if status == "ok":
                ok += 1
                total += n
            elif status == "skip":
                skip += 1
                total += n
            else:
                failures.append((url, status))
            if i % 500 == 0:
                print("  %d/%d  ok=%d skip=%d fail=%d  %.1f MB" %
                      (i, len(urls), ok, skip, len(failures), total / 1e6), flush=True)
    print("DONE ok=%d skip=%d fail=%d  total %.1f MB" % (ok, skip, len(failures), total / 1e6))
    if failures:
        with open(os.path.join(ROOT, "media_failures.txt"), "w", encoding="utf-8") as fh:
            for u, s in failures:
                fh.write("%s\t%s\n" % (u, s))
        for u, s in failures[:10]:
            print("FAIL", s, u)


if __name__ == "__main__":
    main()
