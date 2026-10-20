"""
CEFR Article Book builder.

Builds an illustrated reader from the first N article exports (default 10).
Each article carries its own photograph; everything else on the page -- the
stat tiles, the level bars, the badges, the vocabulary cards, the drop caps and
the pattern bands -- is drawn here as vector, so the book is illustrated
without depending on any external image service.

Per article:
    opener   photo with the title over it, stat tiles, a level-length chart
    B1/B2/C1 the passage at that level, then its vocabulary cards
    Uzbek    the translation of all three levels

Like build_cefr_reading_book.py, the content is one multi-column document that
Chrome paginates natively and the page chrome is a separate layer stamped
underneath. Unlike the exam books there is no dashed column rule: this is a
magazine, not an answer sheet.

Output:
    CEFR_Article_Book.pdf
"""
import glob
import html as htmlmod
import json
import os
import re
import sys
from urllib.parse import unquote, urlparse

import pymupdf

import build_cefr_book as L

ROOT = L.ROOT_DIR
ART_DIR = os.path.join(ROOT, "article")
MEDIA = os.path.join(ROOT, "media")
BUILD = os.path.join(ROOT, "_build_articles")

BOOK_TITLE = "Multilevel Articles"
DEFAULT_COUNT = 10
WPM = 200  # for the reading-time tile

PAGE_W, PAGE_H = 595.32, 841.92
MARGIN_T, MARGIN_B = 28.94, 44.25
MARGIN_L, MARGIN_R = 31.6, 30.52
COL_GAP = 19.4
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R        # 533.2

LEVELS = [("B1", "Threshold"), ("B2", "Vantage"), ("C1", "Advanced")]
LEVEL_TINT = {"B1": "#2f8f5b", "B2": "#1f48d6", "C1": "#8a3ffc"}

esc = L.esc
furl = L.furl


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def load_articles(count):
    out = []
    for fn in sorted(glob.glob(os.path.join(ART_DIR, "*.json")))[:count]:
        with open(fn, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def local_image(url):
    if not url:
        return ""
    path = os.path.join(MEDIA, unquote(urlparse(url).path).lstrip("/"))
    return furl(os.path.abspath(path)) if os.path.exists(path) else ""


def passage(art, level):
    return art["mock_data"].get(f"passage{level}") or art["mock_data"].get("passage") or ""


def translation(art, level):
    return art["mock_data"].get(f"translation{level}") or ""


def vocab(art, level):
    return art["mock_data"].get(f"vocabulary{level}") or {}


def word_count(html):
    return len(re.sub(r"<[^>]+>", " ", html or "").split())


# --------------------------------------------------------------------------- #
# Inline markup
# --------------------------------------------------------------------------- #
def rich(raw, drop_cap=False):
    """Passage HTML -> paragraphs, keeping <strong>/<b>/<em> as accented terms."""
    s = raw or ""
    s = re.sub(r"(?i)<\s*(strong|b)\s*>", "@@B@@", s)
    s = re.sub(r"(?i)<\s*/\s*(strong|b)\s*>", "@@/B@@", s)
    s = re.sub(r"(?i)<\s*(em|i)\s*>", "@@I@@", s)
    s = re.sub(r"(?i)<\s*/\s*(em|i)\s*>", "@@/I@@", s)
    s = re.sub(r"(?i)</p>\s*<p[^>]*>", "\n", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s)

    out = []
    for chunk in re.split(r"\n+", s):
        text = re.sub(r"[ \t]+", " ", chunk).strip()
        if not text:
            continue
        body = (esc(text).replace("@@B@@", '<b class="term">').replace("@@/B@@", "</b>")
                         .replace("@@I@@", "<i>").replace("@@/I@@", "</i>"))
        if drop_cap and not out:
            m = re.match(r'^(<[^>]+>)*([A-Za-z])', body)
            if m:
                i = body.index(m.group(2))
                body = f'{body[:i]}<span class="dropcap">{body[i]}</span>{body[i + 1:]}'
        out.append(f"<p>{body}</p>")
    return "".join(out)


def plain(raw):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", htmlmod.unescape(raw or ""))).strip()


# --------------------------------------------------------------------------- #
# Graphics
# --------------------------------------------------------------------------- #
def stat_tiles(art):
    counts = {lv: word_count(passage(art, lv)) for lv, _ in LEVELS}
    total_words = sum(counts.values())
    terms = sum(len(vocab(art, lv)) for lv, _ in LEVELS)
    minutes = max(1, round(total_words / WPM))
    tiles = [("3", "levels"), (f"{total_words:,}", "words"),
             (str(terms), "key words"), (f"{minutes} min", "reading")]
    cells = "".join(f'<div class="tile"><span class="n">{esc(n)}</span>'
                    f'<span class="l">{esc(l)}</span></div>' for n, l in tiles)
    return f'<div class="stats">{cells}</div>'


def level_bars(art):
    """Horizontal bars comparing how long the passage is at each level."""
    counts = [(lv, name, word_count(passage(art, lv))) for lv, name in LEVELS]
    top = max(c for _, _, c in counts) or 1
    # inner width of .chart: content width less its 10pt padding and 0.84pt border
    w, rowh, pad = CONTENT_W - 20 - 1.68, 26.0, 2.0
    label_w, value_w = 92.0, 54.0
    track = w - label_w - value_w
    rows = ""
    for i, (lv, name, c) in enumerate(counts):
        y = i * rowh
        bw = track * (c / top)
        rows += (
            f'<rect x="0" y="{y + 5:.1f}" width="22" height="13" rx="3.5" fill="{LEVEL_TINT[lv]}"/>'
            f'<text x="11" y="{y + 14.4:.1f}" class="lv">{lv}</text>'
            f'<text x="27" y="{y + 14.6:.1f}" class="nm">{esc(name)}</text>'
            f'<rect x="{label_w}" y="{y + 7:.1f}" width="{track:.1f}" height="9" rx="4.5" fill="#e8edfa"/>'
            f'<rect x="{label_w}" y="{y + 7:.1f}" width="{bw:.1f}" height="9" rx="4.5" fill="{LEVEL_TINT[lv]}"/>'
            f'<text x="{w:.1f}" y="{y + 14.6:.1f}" class="vl">{c} words</text>')
    h = len(counts) * rowh + pad
    return (f'<div class="chart"><div class="chead">Passage length by level</div>'
            f'<svg viewBox="0 0 {w:.1f} {h:.1f}" width="100%" height="{h:.1f}pt">{rows}</svg></div>')


def hero(art, number):
    md = art["mock_data"]
    img = local_image(md.get("imageUrl"))
    cred = md.get("imageCredit") or {}
    bits = [cred.get("creator"), cred.get("via"), cred.get("license")]
    credit = " · ".join(b for b in bits if b)
    pic = f'<img src="{img}">' if img else ""
    return (f'<div class="hero">{pic}<div class="shade"></div>'
            f'<div class="htext"><div class="kicker">Article {number:02d}</div>'
            f'<h1>{esc(md.get("title") or art.get("title"))}</h1></div>'
            + (f'<div class="credit">{esc(credit)}</div>' if credit else "") +
            '</div>')


def vocab_cards(art, level):
    items = vocab(art, level)
    if not items:
        return ""
    cards = ""
    for word, v in items.items():
        v = v or {}
        cards += (f'<div class="vcard"><div class="vw">{esc(word)}</div>'
                  f'<div class="vd">{esc(v.get("definition"))}</div>'
                  + (f'<div class="ve">{esc(v.get("example"))}</div>' if v.get("example") else "")
                  + (f'<div class="vu">{esc(v.get("uzbek"))}</div>' if v.get("uzbek") else "")
                  + '</div>')
    return (f'<div class="vhead"><span class="vbadge" style="background:{LEVEL_TINT[level]}">'
            f'{level}</span> Key words <span class="vn">{len(items)}</span></div>'
            f'<div class="vgrid">{cards}</div>')


ILLUS_DIR = os.path.join(MEDIA, "article-illustrations")


def illustration(number, art):
    """Optional figure from gen_article_images.py; absent until it has run."""
    path = os.path.join(ILLUS_DIR, f"article-{number:02d}.png")
    if not os.path.exists(path):
        return ""
    title = plain(art["mock_data"].get("title") or art.get("title"))
    return (f'<figure class="illus"><img src="{furl(path)}">'
            f'<figcaption>{esc(title)} — illustration</figcaption></figure>')


def level_section(art, level, name):
    tint = LEVEL_TINT[level]
    body = rich(passage(art, level), drop_cap=True)
    return (f'<div class="lvhead" style="--tint:{tint}">'
            f'<span class="lvpill" style="background:{tint}">{level}</span>'
            f'<span class="lvname">{esc(name)}</span>'
            f'<span class="lvrule" style="background:{tint}"></span></div>'
            f'<div class="passage">{body}</div>'
            f'{vocab_cards(art, level)}')


def translations(art):
    blocks = ""
    for lv, _ in LEVELS:
        t = translation(art, lv)
        if not t:
            continue
        blocks += (f'<div class="trbl"><span class="trbadge" style="background:{LEVEL_TINT[lv]}">'
                   f'{lv}</span>{rich(t)}</div>')
    if not blocks:
        return ""
    return (f'<div class="lvhead" style="--tint:#5c6a8e">'
            f'<span class="lvpill" style="background:#5c6a8e">UZ</span>'
            f'<span class="lvname">Tarjima</span>'
            f'<span class="lvrule" style="background:#5c6a8e"></span></div>'
            f'<div class="translation">{blocks}</div>')


# --------------------------------------------------------------------------- #
# CSS
# --------------------------------------------------------------------------- #
PATTERN = L.A["banner"]

CONTENT_CSS = f"""
@font-face {{ font-family: 'Syne'; src: url('{furl(os.path.join(L.FONTS, 'Syne.ttf'))}'); font-weight: 400 800; }}
@font-face {{ font-family: 'Open Sans'; src: url('{furl(os.path.join(L.FONTS, 'OpenSans.ttf'))}'); font-weight: 300 800; font-style: normal; }}
@font-face {{ font-family: 'Open Sans'; src: url('{furl(os.path.join(L.FONTS, 'OpenSans-Italic.ttf'))}'); font-weight: 300 800; font-style: italic; }}

@page {{ size: A4 portrait; margin: {MARGIN_T}pt {MARGIN_R}pt {MARGIN_B}pt {MARGIN_L}pt; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: transparent; }}
body {{
  font-family: 'Open Sans', sans-serif; color: #131a33;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
  font-feature-settings: 'lnum'; font-size: 8.7pt; line-height: 12.9pt;
}}
.flow {{ column-count: 2; column-gap: {COL_GAP}pt; }}
.opener {{ column-span: all; break-before: page; }}
.opener.first {{ break-before: auto; }}

/* ---------- hero ---------- */
.hero {{
  position: relative; width: {CONTENT_W}pt; height: 232pt;
  border-radius: 12.5pt; overflow: hidden; background: #0b1a4a;
}}
.hero img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.hero .shade {{
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(8,18,56,.10) 0%, rgba(8,18,56,.38) 48%, rgba(8,18,56,.88) 100%);
}}
.hero .htext {{ position: absolute; left: 24pt; right: 24pt; bottom: 20pt; }}
.hero .kicker {{
  font-family: 'Syne'; font-weight: 600; font-size: 9.5pt; letter-spacing: 2.05pt;
  color: #cfdbff; text-transform: uppercase; margin-bottom: 5pt;
}}
.hero h1 {{
  margin: 0; font-family: 'Syne'; font-weight: 800; font-size: 30pt; line-height: 33pt;
  color: #fff; letter-spacing: -0.3pt;
}}
.hero .credit {{
  position: absolute; right: 12pt; top: 10pt; font-size: 6.2pt; line-height: 1.2;
  color: rgba(255,255,255,.72); background: rgba(8,18,56,.34);
  padding: 2.4pt 6pt; border-radius: 7pt; max-width: 210pt; text-align: right;
}}

/* ---------- stat tiles ---------- */
.stats {{ display: flex; gap: 9pt; margin-top: 10pt; }}
.tile {{
  flex: 1; background: #eef3ff; border: 0.84pt solid #c9d6f5; border-radius: 8pt;
  padding: 7pt 9pt 6.4pt; display: flex; flex-direction: column;
}}
.tile .n {{ font-family: 'Syne'; font-weight: 700; font-size: 15pt; line-height: 17pt; color: #1a3fc4; }}
.tile .l {{ font-size: 7.2pt; line-height: 9pt; color: #5c6a8e; text-transform: uppercase; letter-spacing: 0.5pt; }}

/* ---------- level chart ---------- */
.chart {{
  margin-top: 9pt; padding: 8pt 10pt 7pt; border: 0.84pt solid #c9d6f5;
  border-radius: 8pt; background: #fff;
}}
.chead {{
  font-size: 7.2pt; letter-spacing: 0.5pt; text-transform: uppercase;
  color: #5c6a8e; margin-bottom: 4pt;
}}
.chart svg {{ display: block; }}
.chart text {{ font-family: 'Open Sans', sans-serif; }}
.chart .lv {{ fill: #fff; font-size: 7.6pt; font-weight: 700; text-anchor: middle; }}
.chart .nm {{ fill: #131a33; font-size: 8.2pt; }}
.chart .vl {{ fill: #5c6a8e; font-size: 7.6pt; text-anchor: end; }}

/* ---------- level heading ---------- */
.lvhead {{
  display: flex; align-items: center; gap: 6pt; margin: 13pt 0 6pt;
  break-after: avoid; break-inside: avoid;
}}
.opener + .lvhead, .stats + .lvhead {{ margin-top: 11pt; }}
.lvpill {{
  color: #fff; font-family: 'Syne'; font-weight: 700; font-size: 9pt;
  padding: 2pt 7pt; border-radius: 5pt; line-height: 1.25;
}}
.lvname {{
  font-family: 'Syne'; font-weight: 600; font-size: 9.6pt; color: var(--tint);
  text-transform: uppercase; letter-spacing: 0.6pt; white-space: nowrap;
}}
.lvrule {{ flex: 1; height: 1.4pt; border-radius: 1pt; opacity: .5; }}

/* ---------- passage ---------- */
.passage p {{ margin: 0 0 4.4pt 0; text-align: justify; }}
.passage p:last-child {{ margin-bottom: 0; }}
.term {{ color: #1a3fc4; font-weight: 700; }}
.dropcap {{
  float: left; font-family: 'Syne'; font-weight: 800; font-size: 29pt; line-height: 23pt;
  color: #1a3fc4; padding: 2pt 4pt 0 0;
}}

/* ---------- generated illustration (optional) ---------- */
.illus {{ margin: 10pt 0 2pt; break-inside: avoid; }}
.illus img {{ width: 100%; display: block; border-radius: 8pt; border: 0.84pt solid #c9d6f5; }}
.illus figcaption {{
  font-size: 7pt; line-height: 9.4pt; color: #6b7590; margin-top: 3pt;
  letter-spacing: 0.3pt; text-transform: uppercase;
}}

/* ---------- vocabulary ---------- */
.vhead {{
  display: flex; align-items: center; gap: 5pt; margin: 9pt 0 5pt;
  font-family: 'Syne'; font-weight: 600; font-size: 8.8pt; color: #0b1a4a;
  text-transform: uppercase; letter-spacing: 0.6pt; break-after: avoid;
}}
.vbadge {{ color: #fff; font-size: 7.4pt; padding: 1.4pt 5pt; border-radius: 4pt; letter-spacing: 0; }}
.vn {{ color: #5c6a8e; font-weight: 400; letter-spacing: 0; }}
.vcard {{
  background: #f6f8ff; border: 0.72pt solid #dce5fa; border-left: 2.2pt solid #1f48d6;
  border-radius: 5pt; padding: 4.6pt 6.4pt 5pt; margin-bottom: 4.4pt; break-inside: avoid;
}}
.vw {{ font-weight: 700; color: #0b1a4a; font-size: 8.6pt; line-height: 11.4pt; }}
.vd {{ font-size: 8.1pt; line-height: 11.2pt; }}
.ve {{ font-size: 8.1pt; line-height: 11.2pt; font-style: italic; color: #4a5675; margin-top: 1.4pt; }}
.vu {{ font-size: 8.1pt; line-height: 11.2pt; color: #2f5bea; margin-top: 1.4pt; }}

/* ---------- translation ---------- */
.translation .trbl {{ margin-bottom: 6pt; break-inside: auto; }}
.trbadge {{
  float: left; color: #fff; font-family: 'Syne'; font-weight: 700; font-size: 7.4pt;
  padding: 1.4pt 5pt; border-radius: 4pt; margin: 1.4pt 5pt 1pt 0;
}}
.translation p {{ margin: 0 0 3.6pt 0; text-align: justify; color: #35405e; }}

/* ---------- contents ---------- */
/* 10 entries read better as one column than split across two */
.toclist {{ column-count: 1; }}
.toc-row {{ display: flex; align-items: baseline; font-size: 10pt; line-height: 27pt; break-inside: avoid; }}
.toc-row .tn {{ font-weight: 700; color: #131a33; white-space: nowrap; }}
.toc-row .tl {{ color: #6b7590; font-size: 8.4pt; margin-left: 6pt; white-space: nowrap; }}
.toc-row .dots {{ flex: 1; border-bottom: 0.9pt dotted #b8c6ee; margin: 0 6pt; transform: translateY(-2.5pt); }}
.toc-row .pg {{
  display: inline-block; min-width: 20.3pt; height: 10.6pt; line-height: 10.6pt; padding: 0 4pt;
  border-radius: 6pt; background: #edf2ff; color: #1f48d6; text-align: center;
  font-family: 'Syne'; font-weight: 700; font-size: 7.6pt;
}}
.headspace {{ column-span: all; height: 37.1pt; }}
"""

CHROME_CSS = L.CSS + f"""
.cover-art {{
  position: absolute; left: 31.4pt; top: 28.3pt; width: 533.4pt; height: 430pt;
  border-radius: 16pt; overflow: hidden; background: #0b1a4a;
}}
.cover-art .grid {{ position: absolute; inset: 0; display: grid;
  grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(2, 1fr); }}
.cover-art .grid img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.cover-art .wash {{ position: absolute; inset: 0;
  background: linear-gradient(170deg, rgba(31,72,214,.82) 0%, rgba(11,26,74,.90) 62%, rgba(8,18,56,.96) 100%); }}
.cover-art .pat {{ position: absolute; inset: 0; opacity: .25;
  background: url('{PATTERN}') center / cover no-repeat; mix-blend-mode: screen; }}
.cv2-kicker {{ position: absolute; left: 34pt; top: 54pt; font-family: 'Syne'; font-weight: 600;
  font-size: 13pt; letter-spacing: 3.2pt; color: #dfe6fb; }}
.cv2-title {{ position: absolute; left: 34pt; top: 96pt; font-family: 'Syne'; font-weight: 800;
  font-size: 52pt; line-height: 56pt; color: #fff; letter-spacing: -0.8pt; }}
.cv2-sub {{ position: absolute; left: 34pt; top: 232pt; font-family: 'Syne'; font-weight: 600;
  font-size: 20pt; color: #cfdbff; }}
.cv2-line {{ position: absolute; left: 34pt; top: 268pt; width: 420pt; font-size: 11pt;
  line-height: 1.65; color: #e5ebff; }}
.cv2-chips {{ position: absolute; left: 34pt; bottom: 28pt; display: flex; gap: 8pt; }}
.cv2-chip {{ background: rgba(255,255,255,.14); border: 0.8pt solid rgba(255,255,255,.35);
  color: #fff; border-radius: 20pt; padding: 4pt 11pt; font-size: 9pt; font-weight: 600; }}
.cv2-body {{ position: absolute; left: 31.6pt; top: 478pt; width: 533.2pt;
  display: grid; grid-template-columns: 1fr 1fr; gap: 12pt 19.4pt; }}
.cv2-more {{ position: absolute; left: 31.6pt; top: 636pt; width: 533.2pt;
  font-size: 9.4pt; line-height: 17pt; color: #35405e; }}
.cv2-more .ml {{ font-family: 'Syne'; font-weight: 600; font-size: 8.4pt; letter-spacing: 1.2pt;
  text-transform: uppercase; color: #5c6a8e; display: block; margin-bottom: 4pt; }}
.cv2-more b {{ color: #0b1a4a; font-weight: 700; }}
"""


# --------------------------------------------------------------------------- #
# Documents
# --------------------------------------------------------------------------- #
def wrap(body, css):
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f'<title>{BOOK_TITLE}</title><style>{css}</style></head>'
            f"<body>{body}</body></html>")


def article_body(art, number, first):
    out = (f'<div class="opener{" first" if first else ""}">'
           f'{hero(art, number)}{stat_tiles(art)}{level_bars(art)}</div>')
    for lv, name in LEVELS:
        if lv == "C1":
            out += illustration(number, art)
        out += level_section(art, lv, name)
    return out + translations(art)


def articles_html(arts):
    body = '<div class="flow">' + "".join(
        article_body(a, i + 1, i == 0) for i, a in enumerate(arts)) + "</div>"
    return wrap(body, CONTENT_CSS)


def toc_html(arts, page_map):
    rows = ""
    for i, a in enumerate(arts):
        md = a["mock_data"]
        words = sum(word_count(passage(a, lv)) for lv, _ in LEVELS)
        rows += (f'<div class="toc-row"><span class="tn">{i + 1:02d} · '
                 f'{esc(md.get("title") or a.get("title"))}</span>'
                 f'<span class="tl">{words:,} words</span>'
                 f'<span class="dots"></span>'
                 f'<span class="pg">{page_map[i]}</span></div>')
    body = f'<div class="flow toclist"><div class="headspace"></div>{rows}</div>'
    return wrap(body, CONTENT_CSS)


def cover_html(arts):
    total_words = sum(word_count(passage(a, lv)) for a in arts for lv, _ in LEVELS)
    total_terms = sum(len(vocab(a, lv)) for a in arts for lv, _ in LEVELS)
    thumbs = "".join(f'<img src="{local_image(a["mock_data"].get("imageUrl"))}">'
                     for a in arts[:6])
    cards = "".join(
        f'<div class="card"><div class="cv-h">{i + 1:02d} · '
        f'{esc(a["mock_data"].get("title") or a.get("title"))}</div>'
        f'{esc(plain(passage(a, "B1"))[:118])}…</div>' for i, a in enumerate(arts[:4]))
    rest = arts[4:]
    more = ""
    if rest:
        items = " · ".join(
            f'<b>{i + 5:02d}</b> {esc(a["mock_data"].get("title") or a.get("title"))}'
            for i, a in enumerate(rest))
        more = f'<div class="cv2-more"><span class="ml">Also inside</span>{items}</div>'
    return f"""
<section class="sheet">
  <img class="stripe" src="{L.A['stripe']}">
  <div class="cover-art">
    <div class="grid">{thumbs}</div><div class="wash"></div><div class="pat"></div>
    <div class="cv2-kicker">MULTILEVEL · CEFR</div>
    <div class="cv2-title">ARTICLES</div>
    <div class="cv2-sub">{len(arts)} readings · B1 · B2 · C1</div>
    <div class="cv2-line">Every article at three levels, with key words, examples and an
      Uzbek translation.<br>{total_words:,} words · {total_terms} key words</div>
    <div class="cv2-chips"><span class="cv2-chip">Three levels</span>
      <span class="cv2-chip">Key words</span><span class="cv2-chip">Tarjima</span></div>
  </div>
  <div class="cv2-body">{cards}</div>
  {more}
  {L.footer(f"{BOOK_TITLE} · CEFR Reading", None)}
</section>"""


def chrome_html(pages):
    out = []
    for label, page_no, head in pages:
        out.append(f'<section class="sheet"><img class="stripe" src="{L.A["stripe"]}">'
                   f'{head}{L.footer(label, page_no)}</section>')
    return wrap("".join(out), CHROME_CSS)


def section_head(title, right):
    return (f'<div class="cols" style="top:28.9pt;height:40pt;column-count:1">'
            f'<div class="ph"><span class="pill">{esc(title)}</span>'
            f'<span class="qr">{esc(right)}</span></div></div>')


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #
def render(html, name):
    path = os.path.join(BUILD, name + ".html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    pdf = os.path.join(BUILD, name + ".pdf")
    L.edge_pdf(path, pdf)
    return pdf


def article_start_pages(pdf, arts):
    """Which page each article opens on -- the pages carrying a hero photo."""
    doc = pymupdf.open(pdf)
    titles = [plain(a["mock_data"].get("title") or a.get("title")) for a in arts]
    starts, seen = [], 0
    for i in range(doc.page_count):
        # the kicker is letter-spaced and uppercased, so it extracts as
        # "A R T I C L E  0 1" -- strip the spacing and match in upper case
        tight = re.sub(r"\s+", "", doc[i].get_text()).upper()
        want = "ARTICLE%02d" % (seen + 1)
        if seen < len(titles) and want in tight:
            starts.append(i + 1)
            seen += 1
    doc.close()
    if len(starts) != len(arts):
        raise RuntimeError(f"found {len(starts)} article openers, expected {len(arts)}")
    return starts


def main():
    os.makedirs(BUILD, exist_ok=True)
    count = next((int(a) for a in sys.argv[1:] if a.isdigit()), DEFAULT_COUNT)
    arts = load_articles(count)
    print(f"Loaded {len(arts)} articles")
    for i, a in enumerate(arts):
        print(f"  {i + 1:02d} {a['mock_data'].get('title') or a.get('title')}")

    print("Rendering articles...")
    body_pdf = render(articles_html(arts), "articles")
    n_body = pymupdf.open(body_pdf).page_count

    starts = article_start_pages(body_pdf, arts)
    first = 3                                     # cover, contents, then body
    page_map = [first + (s - 1) for s in starts]

    toc_pdf = render(toc_html(arts, page_map), "toc")
    n_toc = pymupdf.open(toc_pdf).page_count
    if n_toc > 1:
        page_map = [p + (n_toc - 1) for p in page_map]
        toc_pdf = render(toc_html(arts, page_map), "toc")

    labels = {}
    for i, a in enumerate(arts):
        title = plain(a["mock_data"].get("title") or a.get("title"))
        for p in range(starts[i], (starts[i + 1] if i + 1 < len(arts) else n_body + 1)):
            labels[p] = f"{BOOK_TITLE} · {i + 1:02d} · {title}"

    print("Rendering chrome...")
    pages = [(f"{BOOK_TITLE} · Contents", 2 + i,
              section_head("CONTENTS", f"{len(arts)} articles") if i == 0 else "")
             for i in range(n_toc)]
    base = 2 + n_toc
    pages += [(labels.get(p, BOOK_TITLE), base + p - 1, "") for p in range(1, n_body + 1)]
    chrome_pdf = render(chrome_html(pages), "chrome")

    print("Assembling...")
    book = pymupdf.open(render(wrap(cover_html(arts), CHROME_CSS), "cover"))
    rest = pymupdf.open()
    rest.insert_pdf(pymupdf.open(toc_pdf))
    rest.insert_pdf(pymupdf.open(body_pdf))
    chm = pymupdf.open(chrome_pdf)
    for i in range(rest.page_count):
        rest[i].show_pdf_page(rest[i].rect, chm, i, overlay=False)
    book.insert_pdf(rest)

    toc = [[1, "Cover", 1], [1, "Contents", 2]]
    for i, a in enumerate(arts):
        toc.append([1, f"{i + 1:02d} {plain(a['mock_data'].get('title') or a.get('title'))}",
                    page_map[i]])
    book.set_toc(toc)
    book.set_metadata({"title": "CEFR Articles", "author": BOOK_TITLE,
                       "subject": "CEFR Reading articles at B1, B2 and C1"})
    out = os.path.join(ROOT, "CEFR_Article_Book.pdf")
    book.save(out, garbage=3, deflate=True)
    print(f"Article book: {out} ({book.page_count} pages)")
    book.close()


if __name__ == "__main__":
    main()
