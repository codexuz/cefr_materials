"""
CEFR Article Book builder -- B2 readings with a glossary.

An editorial reader built from the first N article exports (default 10),
using only each article's B2 version. Each article is a two-page spread:

    opener   the article's photograph in high-contrast black and white, set in
             one of five magazine layouts -- a colour band across the photo, a
             giant serif initial, a rotated title on a vertical strip, a circle
             split between photo and colour, or a photo grid with a title block
    reading  the text in a serif column opened by a giant initial, a solid
             pull-quote block, its key terms underlined, and a numbered
             glossary of those terms in a paper-toned panel on the right

Colour: dodgerblue (#1E90FF) leads on every page; each article also carries
one secondary accent (coral, saffron or mint, cycled) for its outline number,
pull quote and small shapes, so every spread has its own identity. Photographs
are black and white so that the colour belongs to the design. All shapes are
drawn here as SVG/CSS; nothing is fetched at build time.

If gen_article_images.py has produced an illustration for an article, it is
used in place of the photograph.

Output:
    CEFR_Article_Book.pdf
"""
import glob
import html as htmlmod
import json
import math
import os
import re
import subprocess
import sys
from urllib.parse import unquote, urlparse

import pymupdf
import segno
from PIL import Image, ImageOps

import build_cefr_book as L

ROOT = L.ROOT_DIR
ART_DIR = os.path.join(ROOT, "article")
MEDIA = os.path.join(ROOT, "media")
ILLUS_DIR = os.path.join(MEDIA, "article-illustrations")
BUILD = os.path.join(ROOT, "_build_articles")
MONO = os.path.join(BUILD, "mono")

QUESTIONS_FILE = os.path.join(ROOT, "article_questions.json")
TELEGRAM = "cefr_impulse"
TELEGRAM_URL = f"https://t.me/{TELEGRAM}"

BOOK_TITLE = "Multilevel Articles"
LEVEL = "B2"
LEVEL_NAME = "Upper-Intermediate"
DEFAULT_COUNT = 20

W, H = 595.32, 841.92                    # A4 in pt
M = 42.0                                 # outer margin

BLUE = "#1E90FF"                         # lead colour, on every page
INK = "#0E1116"
BODY = "#22262E"
GREY = "#6A707B"
GREY_SOFT = "#9AA0AA"
HAIR = "#DADDE2"
PAPER = "#F5F0E7"                        # warm paper for panels
HAIR_PAPER = "#E2D9CA"

# Each article also carries one secondary accent, cycled, with the text colour
# that reads on it. Dodgerblue stays the lead; the accent gives each spread
# its own identity.
ACCENTS = [("#FF5B3A", "#FFFFFF"),        # coral
           ("#FFC233", "#0E1116"),        # saffron
           ("#16B98F", "#FFFFFF")]        # mint


def accent(n):
    return ACCENTS[(n - 1) % len(ACCENTS)]


def tint(hex_color, amount):
    """Mix a colour with white: amount 0 is white, 1 is the colour itself."""
    h = hex_color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(round(255 + (c - 255) * amount) for c in rgb)


def glossary_colours(n):
    """The glossary panel takes a soft tint of its article's accent, with a
    slightly deeper tint for the rules between entries."""
    ac = accent(n)[0]
    return tint(ac, 0.13), tint(ac, 0.34)


FONT_DISPLAY = "C:/Windows/Fonts/bahnschrift.ttf"
FONT_SERIF = "C:/Windows/Fonts/georgia.ttf"
FONT_SERIF_I = "C:/Windows/Fonts/georgiai.ttf"
FONT_SERIF_B = "C:/Windows/Fonts/georgiab.ttf"
FONT_SERIF_BI = "C:/Windows/Fonts/georgiaz.ttf"

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


def plain(raw):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", htmlmod.unescape(raw or ""))).strip()


def title_of(art):
    return plain(art["mock_data"].get("title") or art.get("title"))


def passage(art):
    md = art["mock_data"]
    return md.get(f"passage{LEVEL}") or md.get("passage") or ""


def vocab(art):
    return art["mock_data"].get(f"vocabulary{LEVEL}") or {}


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text) if s.strip()]


def source_image(art, number):
    illus = os.path.join(ILLUS_DIR, f"article-{number:02d}.png")
    if os.path.exists(illus):
        return illus
    url = art["mock_data"].get("imageUrl")
    if not url:
        return ""
    path = os.path.join(MEDIA, unquote(urlparse(url).path).lstrip("/"))
    return path if os.path.exists(path) else ""


# --------------------------------------------------------------------------- #
# Black and white
# --------------------------------------------------------------------------- #
def mono(src, number):
    """High-contrast black and white, cached by source mtime."""
    if not src:
        return ""
    os.makedirs(MONO, exist_ok=True)
    dest = os.path.join(MONO, f"article-{number:02d}.jpg")
    if os.path.exists(dest) and os.path.getmtime(dest) >= os.path.getmtime(src):
        return furl(dest)
    img = ImageOps.autocontrast(Image.open(src).convert("L"), cutoff=1.2)
    # gentle S-curve: deeper blacks, cleaner whites
    curve = [round(255 * (0.5 - 0.5 * math.cos(math.pi * (i / 255) ** 0.96))) for i in range(256)]
    img = img.point(curve)
    if img.width > 1800:
        img = img.resize((1800, round(img.height * 1800 / img.width)), Image.LANCZOS)
    img.save(dest, quality=90, optimize=True)
    return furl(dest)


# --------------------------------------------------------------------------- #
# Small drawing helpers
# --------------------------------------------------------------------------- #
def dots(x, y, cols, rows, gap, r, fill, opacity=1.0):
    return "".join(
        f'<circle cx="{x + c * gap:.1f}" cy="{y + rr * gap:.1f}" r="{r}" fill="{fill}" '
        f'opacity="{opacity}"/>' for rr in range(rows) for c in range(cols))


def svg(content, cls="art"):
    return f'<svg class="{cls}" viewBox="0 0 {W} {H}" width="{W}pt" height="{H}pt">{content}</svg>'


def img_box(src, x, y, w, h, extra="", pos="50% 50%"):
    """Absolutely positioned photo, cropped to fill its box."""
    if not src:
        return f'<div class="ph" style="left:{x}pt;top:{y}pt;width:{w}pt;height:{h}pt;background:{INK}{extra}"></div>'
    return (f'<div class="ph" style="left:{x}pt;top:{y}pt;width:{w}pt;height:{h}pt{extra}">'
            f'<img src="{src}" style="object-position:{pos}"></div>')


def detail(src, x, y, w, h, zoom=2.2, fx=62, fy=40):
    """A zoomed-in crop of the same photograph -- a 'detail' tile."""
    if not src:
        return ""
    return (f'<div class="ph" style="left:{x}pt;top:{y}pt;width:{w}pt;height:{h}pt">'
            f'<img src="{src}" style="object-position:{fx}% {fy}%;transform:scale({zoom});'
            f'transform-origin:{fx}% {fy}%"></div>')


def qr(x, y, size, url=TELEGRAM_URL, dark=INK, light="#FFFFFF", quiet=4):
    """The QR code as vector squares inside a light tile, `size` pt wide.
    Vector rather than an image so it prints sharp at any size."""
    q = segno.make(url, error="m")
    rows = [list(r) for r in q.matrix]
    n = len(rows) + 2 * quiet
    u = size / n
    cells = "".join(
        f"M{x + (c + quiet) * u:.3f},{y + (r + quiet) * u:.3f}h{u:.3f}v{u:.3f}h-{u:.3f}z"
        for r, row in enumerate(rows) for c, v in enumerate(row) if v)
    return (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="{light}"/>'
            f'<path d="{cells}" fill="{dark}" shape-rendering="crispEdges"/>')


def block(x, y, w, h, color):
    return f'<div class="blk" style="left:{x}pt;top:{y}pt;width:{w}pt;height:{h}pt;background:{color}"></div>'


def title_html(title, accent_last=True):
    words = esc(title.upper()).split(" ")
    if accent_last and len(words) > 1:
        words[-1] = f'<span class="acc">{words[-1]}</span>'
    return " ".join(words)


def title_size(title, roomy=52, tight=34):
    n = len(title)
    if n <= 13:
        return roomy
    if n <= 18:
        return roomy - 6
    if n <= 24:
        return roomy - 12
    return tight


# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #
def rich_paragraphs(raw):
    s = raw or ""
    s = re.sub(r"(?i)<\s*(strong|b)\s*>", "@@B@@", s)
    s = re.sub(r"(?i)<\s*/\s*(strong|b)\s*>", "@@/B@@", s)
    s = re.sub(r"(?i)<\s*(em|i)\s*>", "@@I@@", s)
    s = re.sub(r"(?i)<\s*/\s*(em|i)\s*>", "@@/I@@", s)
    s = re.sub(r"(?i)</p>\s*<p[^>]*>", "\n", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = htmlmod.unescape(re.sub(r"<[^>]+>", "", s))
    out = []
    for chunk in re.split(r"\n+", s):
        t = re.sub(r"[ \t]+", " ", chunk).strip()
        if t:
            t = re.sub(r"\s+([.,;:!?])", r"\1", t)        # 'packaging .' -> 'packaging.'
            out.append(esc(t).replace("@@B@@", '<span class="term">').replace("@@/B@@", "</span>")
                       .replace("@@I@@", "<i>").replace("@@/I@@", "</i>"))
    return out


def initial(p):
    """Split off the first letter for the giant initial."""
    m = re.search(r"[A-Za-z]", re.sub(r"<[^>]+>", lambda x: "\0" * len(x.group()), p))
    if not m:
        return "", p
    i = m.start()
    return p[i], p[:i] + p[i + 1:]


def standfirst(art, limit=230):
    s = sentences(re.sub(r"\s+([.,;:!?])", r"\1", plain(passage(art))))
    text = s[0] if s else ""
    if len(text) < 100 and len(s) > 1:
        text += " " + s[1]
    return text if len(text) <= limit else text[:limit - 3].rsplit(" ", 1)[0] + "…"


def pull_quote(art):
    """A sentence from later in the article. The quote block sits beside the
    second paragraph, so quoting the opening paragraphs would repeat text the
    reader can see right next to it."""
    paras = [re.sub(r"\s+([.,;:!?])", r"\1", plain(p)) for p in rich_paragraphs(passage(art))]
    later = [x for p in paras[3:] for x in sentences(p)] or \
            [x for p in paras[2:] for x in sentences(p)]
    pool = later or sentences(" ".join(paras))
    good = [x for x in pool if 60 <= len(x) <= 140] or [x for x in pool if 50 <= len(x) <= 170]
    return good[0] if good else ""


def load_questions(arts):
    """Speaking and essay questions per article, from article_questions.json.
    Each entry names its article, so a reordered export cannot pick up
    another article's questions."""
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for n, art in enumerate(arts, 1):
        q = data["articles"].get(str(n))
        if not q:
            raise RuntimeError(f"article_questions.json has no entry for article {n}")
        if q["title"].strip().lower() != title_of(art).lower():
            raise RuntimeError(f"article {n} is '{title_of(art)}' but its questions are "
                               f"for '{q['title']}'")
        out[n] = q
    return out, data.get("essay_words", 200)


def credit_line(art):
    c = art["mock_data"].get("imageCredit") or {}
    bits = [b for b in (c.get("creator"), c.get("via"), c.get("license")) if b]
    return ("Photo · " + " · ".join(bits)) if bits else ""


def ordered_glossary(art):
    """Glossary in the order its terms appear in the text; unseen terms last."""
    text = plain(passage(art)).lower()
    items = list(vocab(art).items())

    def pos(kv):
        i = text.find(kv[0].lower())
        return (i if i >= 0 else 10 ** 6, kv[0].lower())
    return sorted(items, key=pos)


# --------------------------------------------------------------------------- #
# Shared page furniture
# --------------------------------------------------------------------------- #
def folio(page_no, label=BOOK_TITLE):
    return (f'<div class="folio"><span><i class="sq"></i>{esc(label)}</span>'
            f'<span class="pn">{page_no:02d}</span></div>')


def kicker(number, light=False, short=False):
    cls = "kicker light" if light else "kicker"
    tail = LEVEL if short else f"{LEVEL} {LEVEL_NAME}"
    sq = "" if light else f' style="background:{accent(number)[0]}"'
    return f'<div class="{cls}"><i class="sq"{sq}></i>Article {number:02d} · {tail}</div>'


def bignum(number, x, y, size=210, anchor="end", stroke=BLUE):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="bignum" '
            f'style="font-size:{size}px;stroke:{stroke}">{number:02d}</text>')


# --------------------------------------------------------------------------- #
# Opener layouts
# --------------------------------------------------------------------------- #
def opener_band(art, n, img):
    t = title_of(art)
    ac, _ = accent(n)
    return (img_box(img, 0, 0, W, 560)
            + svg(dots(W - 150, 34, 9, 6, 13, 1.7, ac, 1)
                  + bignum(n, W - 30, H - 62, stroke=ac))
            + f'<div class="band" style="bottom:{H - 560}pt">{kicker(n, light=True)}'
              f'<h1 class="t-white" style="font-size:{title_size(t, 50, 36)}pt">{esc(t.upper())}</h1></div>'
            + block(430, 560 - 28, 28, 28, ac)
            + f'<p class="standfirst" style="left:{M}pt;top:590pt;width:330pt">{esc(standfirst(art))}</p>')


def opener_initial(art, n, img):
    t = title_of(art)
    ac, _ = accent(n)
    letter = esc(t[:1].upper())
    return (svg(f'<text x="6" y="548" class="giant">{letter}</text>'
                + f'<rect x="272" y="80" width="281" height="402" fill="none" stroke="{ac}" stroke-width="2"/>'
                + dots(M, 520, 14, 2, 13, 1.6, ac, 1))
            + img_box(img, 258, 66, 281, 402)
            + f'<div class="tblock" style="top:576pt">{kicker(n)}'
              f'<h1 style="font-size:{title_size(t)}pt">{title_html(t)}</h1>'
              f'<p class="sf">{esc(standfirst(art))}</p></div>')


def opener_vertical(art, n, img):
    t = title_of(art)
    ac, _ = accent(n)
    size = min(64, 700 / max(1, len(t) * 0.5))
    return (f'<div class="strip"></div>'
            + img_box(img, 132, 0, W - 132, 548)
            + block(132, 500, 48, 48, ac)
            + f'<div class="vtitle" style="font-size:{size:.1f}pt;line-height:{size:.1f}pt;'
              f'left:{(132 - size) / 2 + size * 0.06:.1f}pt;top:{H - 52}pt">{esc(t.upper())}</div>'
            + svg(bignum(n, W - 30, H - 62, 180, stroke=ac))
            + f'<div class="tblock" style="left:162pt;top:584pt;width:276pt">{kicker(n)}'
              f'<p class="sf">{esc(standfirst(art))}</p></div>')


def opener_circle(art, n, img):
    t = title_of(art)
    ac, _ = accent(n)
    cx, cy, r = 396, 316, 236
    left_half = f"M{cx},{cy - r} A{r},{r} 0 0 0 {cx},{cy + r} Z"
    right_half = f"M{cx},{cy - r} A{r},{r} 0 0 1 {cx},{cy + r} Z"
    photo = ""
    if img:
        photo = (f'<clipPath id="lh{n}"><path d="{left_half}"/></clipPath>'
                 f'<image href="{img}" x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" '
                 f'preserveAspectRatio="xMidYMid slice" clip-path="url(#lh{n})"/>')
    return (svg(f'<circle cx="{cx}" cy="{cy}" r="{r + 22}" fill="none" stroke="{ac}" '
                f'stroke-width="1.2" stroke-dasharray="2 5"/>'
                + photo
                + f'<path d="{right_half}" fill="{BLUE}"/>'
                + f'<circle cx="{cx - r + 46}" cy="{cy + r - 40}" r="22" fill="{ac}"/>'
                + bignum(n, 30, 196, 170, anchor="start", stroke=ac)
                + dots(cx + 70, cy - 60, 6, 9, 13, 1.6, "#fff", 0.9))
            + f'<div class="tblock" style="top:584pt">{kicker(n)}'
              f'<h1 style="font-size:{title_size(t)}pt">{title_html(t)}</h1>'
              f'<p class="sf">{esc(standfirst(art))}</p></div>')


def opener_grid(art, n, img):
    t = title_of(art)
    ac, _ = accent(n)
    size = 26 if len(t) <= 20 else 21
    return (img_box(img, M, M, 330, 430)
            + block(M, M + 430 - 34, 34, 34, ac)
            + f'<div class="tbox" style="left:384pt;top:{M}pt;width:169.3pt;height:252pt">'
              f'{kicker(n, light=True, short=True)}<h1 class="t-white" style="font-size:{size}pt">{esc(t.upper())}</h1>'
              f'<i class="rule"></i></div>'
            + detail(img, 384, 306, 169.3, 166)
            + svg(bignum(n, W - 30, H - 62, 200, stroke=ac) + dots(M, 492, 14, 1, 13, 1.6, ac, 1))
            + f'<p class="standfirst big" style="left:{M}pt;top:516pt;width:360pt">{esc(standfirst(art, 210))}</p>')


OPENERS = [opener_band, opener_initial, opener_vertical, opener_circle, opener_grid]


def opener_page(art, n, page_no):
    img = mono(source_image(art, n), n)
    layout = OPENERS[(n - 1) % len(OPENERS)]
    body = layout(art, n, img)
    credit = credit_line(art)
    # the vertical layout's blue strip runs under the folio, so start it past the strip
    cls = "sheet strip-left" if layout is opener_vertical else "sheet"
    return (f'<section class="{cls}">{body}'
            + (f'<div class="credit">{esc(credit)}</div>' if credit else "")
            + folio(page_no)
            + "</section>")


# --------------------------------------------------------------------------- #
# Reading page
# --------------------------------------------------------------------------- #
def reading_page(art, n, page_no, fit):
    img = mono(source_image(art, n), n)
    ac, on = accent(n)
    paras = rich_paragraphs(passage(art))
    cap = ""
    if paras:
        cap, paras[0] = initial(paras[0])
    quote = pull_quote(art)
    body = f'<span class="cap">{esc(cap)}</span>' if cap else ""
    for i, p in enumerate(paras):
        if i == 1 and quote:
            body += (f'<blockquote class="pq" style="background:{ac};color:{on}">'
                     f'<span class="qm">“</span>{esc(quote)}</blockquote>')
        body += f"<p>{p}</p>"

    items = ordered_glossary(art)
    rows = "".join(
        f'<div class="g"><span class="gn">{i:02d}</span><div><div class="gw">{esc(w)}</div>'
        f'<div class="gd">{esc((v or {}).get("definition"))}</div></div></div>'
        for i, (w, v) in enumerate(items, 1))

    panel, rule = glossary_colours(n)
    k_main = fit.get(f"main-{n}", {}).get("k", 1)
    k_gl = fit.get(f"gloss-{n}", {}).get("k", 1)
    room = fit.get(f"gloss-{n}", {}).get("left", 0)
    crop = ""
    if img and room >= 96:
        h = min(room - 14, 230)
        crop = (f'<div class="gcrop" style="height:{h:.0f}pt">'
                f'<img src="{img}"><i class="gsq" style="background:{ac}"></i></div>')

    return f"""
<section class="sheet">
  {svg(f'<rect x="{W - 22}" y="0" width="22" height="118" fill="{ac}"/>'
       + f'<rect x="{W - 22}" y="118" width="22" height="40" fill="{BLUE}"/>')}
  <header class="rhead"><i class="sq"></i><span class="rn">{n:02d}</span>
    <span class="rt">{esc(title_of(art))}</span><span class="rl">{LEVEL} · {LEVEL_NAME}</span></header>
  <article class="main" data-fit="main-{n}" style="--k:{k_main}">{body}</article>
  <aside class="gloss" data-fit="gloss-{n}" style="--k:{k_gl};background:{panel};--rule:{rule}">
    <div class="ghead">Glossary</div><i class="gbar" style="background:{ac}"></i>
    <div class="glist">{rows}</div>{crop}
  </aside>
  {folio(page_no)}
</section>"""


# --------------------------------------------------------------------------- #
# Questions page
# --------------------------------------------------------------------------- #
WRITE_TOP, WRITE_BOTTOM, LINE_GAP = 512, 786, 23.0


def questions_page(art, n, page_no, q, essay_words):
    img = mono(source_image(art, n), n)
    ac, on = accent(n)
    cx, cy, r = 478, 196, 72
    photo = ""
    if img:
        photo = (f'<clipPath id="qc{n}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>'
                 f'<image href="{img}" x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" '
                 f'preserveAspectRatio="xMidYMid slice" clip-path="url(#qc{n})"/>')
    lines = "".join(
        f'<line x1="{M + 12}" y1="{y:.1f}" x2="{W - M}" y2="{y:.1f}" stroke="{HAIR}" stroke-width="0.7"/>'
        for y in [WRITE_TOP + i * LINE_GAP for i in range(int((WRITE_BOTTOM - WRITE_TOP) / LINE_GAP) + 1)])
    art_svg = (f'<rect x="{W - 22}" y="0" width="22" height="118" fill="{ac}"/>'
               + f'<rect x="{W - 22}" y="118" width="22" height="40" fill="{BLUE}"/>'
               + f'<circle cx="{cx}" cy="{cy}" r="{r + 14}" fill="none" stroke="{ac}" '
                 f'stroke-width="1.4" stroke-dasharray="2 5"/>'
               + photo
               + f'<circle cx="{cx - r + 8}" cy="{cy + r - 6}" r="15" fill="{BLUE}"/>'
               + dots(cx + 20, cy + r + 22, 5, 2, 12, 1.5, ac, 1)
               + f'<rect x="{M}" y="{WRITE_TOP - 1}" width="3" height="{WRITE_BOTTOM - WRITE_TOP + 2}" fill="{ac}"/>'
               + lines)
    qs = "".join(f'<div class="sq-row"><span class="sq-n" style="color:{ac}">{i}</span>'
                 f'<span class="sq-t">{esc(t)}</span></div>'
                 for i, t in enumerate(q["speaking"], 1))
    terms = [w for w, _ in ordered_glossary(art)][:5]
    chips = "".join(f'<span class="chip">{esc(t)}</span>' for t in terms)
    return f"""
<section class="sheet">
  {svg(art_svg)}
  <header class="rhead"><i class="sq"></i><span class="rn">{n:02d}</span>
    <span class="rt">{esc(title_of(art))}</span><span class="rl">Speaking · Writing</span></header>
  <div class="q-label" style="top:84pt"><i class="bar" style="background:{ac}"></i>Speaking
    <span>Discuss with a partner</span></div>
  <div class="sp">{qs}
    <div class="try"><span class="try-l">Try to use</span>{chips}</div></div>
  <div class="essay" style="top:{WRITE_TOP - 128}pt">
    <div class="e-label">Essay<span>· about {essay_words} words</span></div>
    <p>{esc(q["essay"])}</p></div>
  {folio(page_no)}
</section>"""


# --------------------------------------------------------------------------- #
# Back cover
# --------------------------------------------------------------------------- #
def back_page(arts):
    coral, saffron, mint = ACCENTS[0][0], ACCENTS[1][0], ACCENTS[2][0]
    qx, qy, qs = M, 548, 150
    shapes = (f'<circle cx="{W - 30}" cy="118" r="150" fill="{saffron}"/>'
              + f'<circle cx="{W - 30}" cy="118" r="176" fill="none" stroke="#fff" '
                f'stroke-width="1" stroke-dasharray="2 5"/>'
              + dots(M, 64, 10, 3, 13, 1.7, "#fff", 0.9)
              + f'<rect x="{W - 140}" y="{H - 168}" width="98" height="98" fill="{coral}"/>'
              + f'<rect x="{W - 140}" y="{H - 168}" width="98" height="98" fill="none" '
                f'stroke="#fff" stroke-width="1" transform="translate(12,12)"/>'
              + f'<rect x="{M}" y="{qy - 30}" width="64" height="5" fill="{mint}"/>'
              + f'<rect x="{qx - 8}" y="{qy - 8}" width="{qs + 16}" height="{qs + 16}" fill="#fff"/>'
              + qr(qx, qy, qs))
    return f"""
<section class="sheet back">
  {svg(shapes)}
  <div class="bk-kicker"><i class="sq" style="background:#fff"></i>Multilevel · CEFR · {LEVEL} {LEVEL_NAME}</div>
  <div class="bk-word">KEEP<br>READ–<br>ING.</div>
  <p class="bk-about">{len(arts)} articles, each with a glossary, speaking questions and an essay task.
    More readings, mock tests and exam tips every week on our Telegram channel.</p>
  <div class="bk-tg" style="left:{qx + qs + 28}pt;top:{qy + 14}pt">
    <div class="bk-tg-l">Join us on Telegram</div>
    <div class="bk-tg-h">@{TELEGRAM}</div>
    <div class="bk-tg-u">t.me/{TELEGRAM} · scan the code</div></div>
  <div class="bk-foot"><span>{BOOK_TITLE}</span><span>{LEVEL} · {LEVEL_NAME}</span></div>
</section>"""


# --------------------------------------------------------------------------- #
# Cover and contents
# --------------------------------------------------------------------------- #
def cover_page(arts):
    imgs = [mono(source_image(a, i + 1), i + 1) for i, a in enumerate(arts)]
    gx, gy, gw, gh, gap = M, 432, (W - 2 * M - 12) / 3, 168, 6
    tiles = ""
    photos = iter(imgs)
    for k in range(6):
        col, row = k % 3, k // 3
        x, y = gx + col * (gw + gap), gy + row * (gh + gap)
        if k == 4:
            tiles += (f'<div class="cv-block" style="left:{x:.1f}pt;top:{y:.1f}pt;width:{gw:.1f}pt;'
                      f'height:{gh}pt"><span class="cbn">{len(arts)}</span>'
                      f'<span class="cbt">{LEVEL} readings<br>with glossary</span></div>')
        else:
            tiles += img_box(next(photos, ""), round(x, 1), round(y, 1), round(gw, 1), gh)
    coral, saffron, mint = ACCENTS[0][0], ACCENTS[1][0], ACCENTS[2][0]
    shapes = (f'<rect x="0" y="0" width="{W}" height="10" fill="{BLUE}"/>'
              + dots(W - 170, 64, 10, 4, 13, 1.7, coral, 1)
              + f'<circle cx="{W - 96}" cy="338" r="44" fill="{saffron}"/>'
              + f'<circle cx="{W - 96}" cy="338" r="62" fill="none" stroke="{INK}" stroke-width="0.8"/>'
              + f'<rect x="{W - M - 96}" y="124" width="96" height="96" fill="#fff" stroke="{INK}" stroke-width="0.8"/>'
              + qr(W - M - 92, 128, 88)
              + f'<rect x="{gx}" y="{gy - 16}" width="64" height="5" fill="{mint}"/>'
              + f'<rect x="{gx + 2 * (gw + gap) + gw - 26:.1f}" y="{gy + gh + gap + gh - 26}" '
                f'width="26" height="26" fill="{coral}"/>')
    return f"""
<section class="sheet">
  {svg(shapes)}
  <div class="cv-kicker"><i class="sq" style="background:{coral}"></i>Multilevel · CEFR · {LEVEL} {LEVEL_NAME}</div>
  <div class="cv-word">ARTI–<br><span class="acc">CLES</span></div>
  <div class="cv-qr" style="left:{W - M - 96}pt;top:226pt;width:96pt">Telegram<br><b>@{TELEGRAM}</b></div>
  {tiles}
  <div class="cv-foot"><span>{len(arts)} readings · a glossary with every article</span>
    <span>{LEVEL} · {LEVEL_NAME}</span></div>
</section>"""


def contents_page(arts, page_map):
    img = mono(source_image(arts[0], 1), 1) if arts else ""
    cx, cy, r = W, 214, 196
    left_half = f"M{cx},{cy - r} A{r},{r} 0 0 0 {cx},{cy + r} Z"
    photo = ""
    if img:
        photo = (f'<clipPath id="tocc"><path d="{left_half}"/></clipPath>'
                 f'<image href="{img}" x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" '
                 f'preserveAspectRatio="xMidYMid slice" clip-path="url(#tocc)"/>')
    # Up to ten entries fit one column with a line of each article; beyond
    # that the list runs in two columns of title and page only.
    two_col = len(arts) > 10
    rows = ""
    for i, a in enumerate(arts):
        ex = "" if two_col else f'<div class="cte">{esc(standfirst(a, 104))}</div>'
        rows += (f'<div class="crow"><span class="cn" style="color:{accent(i + 1)[0]}">{i + 1:02d}</span>'
                 f'<div class="ct"><div class="ctt">{esc(title_of(a))}</div>{ex}</div>'
                 f'<span class="cp">{page_map[i]:02d}</span></div>')
    list_cls = "clist two" if two_col else "clist"
    coral, saffron = ACCENTS[0][0], ACCENTS[1][0]
    return f"""
<section class="sheet">
  {svg(f'<circle cx="{cx}" cy="{cy}" r="{r + 20}" fill="none" stroke="{BLUE}" stroke-width="0.9" stroke-dasharray="2 5"/>'
       + photo + f'<rect x="{W - 160}" y="{cy + r - 54}" width="54" height="54" fill="{coral}"/>'
       + f'<circle cx="{M + 290}" cy="236" r="16" fill="{saffron}"/>')}
  <div class="c-word">CONT–<br><span class="acc">ENTS</span></div>
  <div class="c-note">{len(arts)} articles at {LEVEL} · {LEVEL_NAME}.<br>
    Each opens on a photograph, comes with a glossary,<br>and ends with speaking and essay questions.</div>
  <div class="{list_cls}">{rows}</div>
  {folio(2)}
</section>"""


# --------------------------------------------------------------------------- #
# CSS
# --------------------------------------------------------------------------- #
def K(v):
    return f"calc({v}pt * var(--k, 1))"


CSS = f"""
@font-face {{ font-family: 'Display'; src: url('file:///{FONT_DISPLAY}');
  font-weight: 300 700; font-stretch: 75% 100%; }}
@font-face {{ font-family: 'Serif'; src: url('file:///{FONT_SERIF}'); font-weight: 400; font-style: normal; }}
@font-face {{ font-family: 'Serif'; src: url('file:///{FONT_SERIF_I}'); font-weight: 400; font-style: italic; }}
@font-face {{ font-family: 'Serif'; src: url('file:///{FONT_SERIF_B}'); font-weight: 700; font-style: normal; }}
@font-face {{ font-family: 'Serif'; src: url('file:///{FONT_SERIF_BI}'); font-weight: 700; font-style: italic; }}

@page {{ size: A4 portrait; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #fff; }}
body {{ color: {INK}; -webkit-print-color-adjust: exact; print-color-adjust: exact;
  font-family: 'Serif', Georgia, serif; font-feature-settings: 'lnum'; }}
.sheet {{ position: relative; width: {W}pt; height: {H}pt; overflow: hidden; break-after: page; background: #fff; }}
.sheet:last-child {{ break-after: auto; }}
.art {{ position: absolute; left: 0; top: 0; overflow: visible; }}
.ph {{ position: absolute; overflow: hidden; background: #111; }}
.ph img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.blk {{ position: absolute; }}
.acc {{ color: {BLUE}; }}
i.sq {{ display: inline-block; width: 6pt; height: 6pt; background: {BLUE}; margin-right: 7pt;
  vertical-align: 0.5pt; }}

/* ---------- folio / kicker ---------- */
.folio {{ position: absolute; left: {M}pt; right: {M}pt; bottom: 24pt; display: flex;
  justify-content: space-between; align-items: baseline; font-family: 'Display'; font-size: 7.2pt;
  letter-spacing: 1.8pt; text-transform: uppercase; color: {GREY_SOFT}; }}
.folio i.sq {{ width: 5pt; height: 5pt; }}
.folio .pn {{ font-size: 9pt; color: {INK}; font-variation-settings: 'wght' 700; letter-spacing: 0.4pt; }}
.kicker {{ font-family: 'Display'; font-size: 8.2pt; letter-spacing: 2.4pt; text-transform: uppercase;
  color: {INK}; font-variation-settings: 'wght' 600; }}
.kicker.light {{ color: #fff; }}
.kicker.light i.sq {{ background: #fff; }}
.credit {{ position: absolute; left: {M}pt; bottom: 40pt; font-family: 'Display'; font-size: 6.2pt;
  letter-spacing: 0.5pt; color: {GREY_SOFT}; max-width: 300pt; }}
.strip-left .folio, .strip-left .credit {{ left: 162pt; }}

/* ---------- opener type ---------- */
h1 {{ margin: 10pt 0 0; font-family: 'Display'; font-weight: normal;
  font-variation-settings: 'wght' 700, 'wdth' 78; line-height: 0.94; letter-spacing: -0.4pt;
  color: {INK}; text-transform: uppercase; }}
h1.t-white {{ color: #fff; }}
.tblock {{ position: absolute; left: {M}pt; width: 420pt; }}
.sf, .standfirst {{ font-style: italic; font-size: 13.6pt; line-height: 20pt; color: #3A3F48; margin: 14pt 0 0; }}
.standfirst {{ position: absolute; margin: 0; }}
.standfirst.big {{ font-size: 17pt; line-height: 25pt; color: {INK}; }}
.bignum {{ font-family: 'Display'; font-variation-settings: 'wght' 700, 'wdth' 78; fill: none;
  stroke-width: 1.4; letter-spacing: -6px; }}
.giant {{ font-family: 'Serif'; font-weight: 700; font-size: 720px; fill: {BLUE}; }}

.band {{ position: absolute; left: 0; width: 430pt; background: {BLUE}; padding: 22pt 28pt 24pt {M}pt; }}
.band h1 {{ margin-top: 9pt; }}
.strip {{ position: absolute; left: 0; top: 0; width: 132pt; height: {H}pt; background: {BLUE}; }}
.vtitle {{ position: absolute; transform-origin: 0 0; transform: rotate(-90deg); white-space: nowrap;
  font-family: 'Display'; font-variation-settings: 'wght' 700, 'wdth' 76; color: #fff;
  letter-spacing: 0.6pt; }}
.tbox {{ position: absolute; background: {BLUE}; padding: 18pt 16pt; display: flex; flex-direction: column; }}
.tbox h1 {{ margin-top: auto; line-height: 0.98; }}
.tbox .rule {{ display: block; width: 32pt; height: 2.4pt; background: #fff; margin-top: 12pt; }}

/* ---------- reading page ---------- */
.rhead {{ position: absolute; left: {M}pt; right: 64pt; top: 38pt; display: flex; align-items: baseline;
  gap: 8pt; padding-bottom: 10pt; border-bottom: 0.7pt solid {INK};
  font-family: 'Display'; text-transform: uppercase; }}
.rhead i.sq {{ margin-right: 0; }}
.rhead .rn {{ color: {BLUE}; font-size: 11pt; font-variation-settings: 'wght' 700; }}
.rhead .rt {{ font-size: 8.4pt; letter-spacing: 2pt; color: {INK}; font-variation-settings: 'wght' 600; }}
.rhead .rl {{ margin-left: auto; font-size: 7.2pt; letter-spacing: 1.8pt; color: {GREY_SOFT}; }}

.main {{ position: absolute; left: {M}pt; top: 82pt; width: 318pt; height: 710pt; overflow: hidden;
  font-size: {K(10)}; line-height: {K(15.6)}; color: {BODY}; }}
.main p {{ margin: 0 0 {K(7)}; text-align: justify; hyphens: auto; }}
.main .term {{ color: {INK}; font-weight: 700; text-decoration: underline; text-decoration-color: {BLUE};
  text-decoration-thickness: 1.2pt; text-underline-offset: 2.2pt; }}
.cap {{ float: left; font-family: 'Serif'; font-weight: 700; color: {BLUE};
  font-size: {K(96)}; line-height: {K(74)}; margin: {K(6)} {K(8)} {K(-2)} {K(-2)}; }}
.pq {{ float: right; width: 146pt; margin: {K(4)} 0 {K(10)} {K(14)}; padding: {K(14)} {K(14)} {K(16)};
  font-style: italic; font-size: {K(12.6)}; line-height: {K(17.4)}; }}
.pq .qm {{ display: block; font-style: normal; font-weight: 700; font-size: {K(38)}; line-height: {K(22)};
  height: {K(20)}; }}

.gloss {{ position: absolute; left: 378pt; top: 82pt; width: 175.3pt; height: 710pt; overflow: hidden;
  display: flex; flex-direction: column; background: {PAPER}; padding: {K(16)} {K(12)} {K(12)}; }}
.ghead {{ font-family: 'Serif'; font-style: italic; font-weight: 700; font-size: {K(22)};
  line-height: {K(24)}; color: {INK}; }}
.gbar {{ display: block; width: 30pt; height: 3pt; margin: {K(9)} 0 {K(8)}; flex: none; }}
.glist {{ flex: none; }}
.g {{ display: flex; gap: {K(7)}; padding: {K(6.2)} 0; border-top: 0.6pt solid var(--rule, {HAIR_PAPER}); }}
.g:first-child {{ border-top: 0; padding-top: {K(2)}; }}
.gn {{ flex: none; width: {K(14)}; font-family: 'Display'; font-size: {K(7.4)}; line-height: {K(11.6)};
  color: {BLUE}; font-variation-settings: 'wght' 700; }}
.gw {{ font-family: 'Serif'; font-weight: 700; font-size: {K(9.2)}; line-height: {K(11.6)}; color: {INK}; }}
.gd {{ font-family: 'Display'; font-size: {K(7.9)}; line-height: {K(10.6)}; color: {GREY};
  font-variation-settings: 'wght' 350; margin-top: {K(1.6)}; }}
.gcrop {{ position: relative; margin-top: auto; overflow: hidden; flex: none; }}
.gcrop img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.gcrop .gsq {{ position: absolute; left: 0; bottom: 0; width: 26pt; height: 26pt; }}

/* ---------- questions page ---------- */
.q-label {{ position: absolute; left: {M}pt; font-family: 'Display'; font-size: 15pt; letter-spacing: 2.4pt;
  text-transform: uppercase; color: {INK}; font-variation-settings: 'wght' 700; display: flex;
  align-items: center; gap: 9pt; }}
.q-label .bar {{ display: inline-block; width: 22pt; height: 4pt; }}
.q-label span {{ font-size: 7.4pt; letter-spacing: 1.8pt; color: {GREY_SOFT};
  font-variation-settings: 'wght' 500; margin-left: 4pt; }}
.sp {{ position: absolute; left: {M}pt; top: 112pt; width: 344pt; }}
.sq-row {{ display: flex; gap: 14pt; align-items: baseline; padding: 11pt 0 12pt;
  border-top: 0.6pt solid {HAIR}; }}
.sq-row:first-child {{ border-top: 0.7pt solid {INK}; }}
.sq-n {{ flex: none; width: 20pt; font-family: 'Display'; font-size: 30pt; line-height: 24pt;
  font-variation-settings: 'wght' 700, 'wdth' 78; }}
.sq-t {{ font-family: 'Serif'; font-size: 13.6pt; line-height: 19.4pt; color: {INK}; }}
.try {{ margin-top: 14pt; width: {W - 2 * M}pt; display: flex; flex-wrap: wrap; gap: 5pt 6pt; align-items: center; }}
.try-l {{ font-family: 'Display'; font-size: 7.2pt; letter-spacing: 1.8pt; text-transform: uppercase;
  color: {GREY}; margin-right: 4pt; }}
.chip {{ font-family: 'Display'; font-size: 8.4pt; color: {INK}; border: 0.8pt solid {BLUE};
  padding: 2.4pt 7pt 2pt; border-radius: 10pt; font-variation-settings: 'wght' 500; }}
.essay {{ position: absolute; left: {M}pt; width: {W - 2 * M}pt; height: 106pt; background: {BLUE};
  color: #fff; padding: 16pt 20pt; }}
.e-label {{ font-family: 'Display'; font-size: 15pt; letter-spacing: 2.4pt; text-transform: uppercase;
  font-variation-settings: 'wght' 700; }}
.e-label span {{ font-size: 7.6pt; letter-spacing: 1.6pt; margin-left: 8pt; opacity: .85;
  font-variation-settings: 'wght' 500; }}
.essay p {{ margin: 9pt 0 0; font-style: italic; font-size: 13pt; line-height: 18.6pt; }}

/* ---------- back cover ---------- */
.sheet.back {{ background: {BLUE}; }}
.bk-kicker {{ position: absolute; left: {M}pt; top: 124pt; font-family: 'Display'; font-size: 8.6pt;
  letter-spacing: 2.6pt; text-transform: uppercase; color: #fff; font-variation-settings: 'wght' 600; }}
.bk-word {{ position: absolute; left: 36pt; top: 150pt; font-family: 'Display'; font-size: 104pt;
  line-height: 96pt; letter-spacing: -2.5pt; color: #fff; font-variation-settings: 'wght' 700, 'wdth' 76; }}
.bk-about {{ position: absolute; left: {M}pt; top: 452pt; width: 330pt; margin: 0; font-style: italic;
  font-size: 13pt; line-height: 19pt; color: #fff; }}
.bk-tg {{ position: absolute; color: #fff; font-family: 'Display'; }}
.bk-tg-l {{ font-size: 9pt; letter-spacing: 2.2pt; text-transform: uppercase; font-variation-settings: 'wght' 600; }}
.bk-tg-h {{ font-size: 30pt; line-height: 34pt; margin-top: 6pt; font-variation-settings: 'wght' 700, 'wdth' 82; }}
.bk-tg-u {{ font-size: 8.4pt; letter-spacing: 1pt; margin-top: 8pt; opacity: .9; }}
.bk-foot {{ position: absolute; left: {M}pt; right: {M}pt; bottom: 24pt; display: flex;
  justify-content: space-between; font-family: 'Display'; font-size: 7.2pt; letter-spacing: 1.8pt;
  text-transform: uppercase; color: #fff; border-top: 0.7pt solid rgba(255,255,255,.6); padding-top: 9pt; }}

/* ---------- cover ---------- */
.cv-qr {{ position: absolute; text-align: center; font-family: 'Display'; font-size: 7pt; line-height: 10pt;
  letter-spacing: 1.4pt; text-transform: uppercase; color: {GREY}; padding-top: 6pt; }}
.cv-qr b {{ color: {INK}; font-variation-settings: 'wght' 700; letter-spacing: 0.4pt; font-size: 8.6pt; }}
.cv-kicker {{ position: absolute; left: {M}pt; top: 54pt; font-family: 'Display'; font-size: 8.6pt;
  letter-spacing: 2.6pt; text-transform: uppercase; color: {INK}; font-variation-settings: 'wght' 600; }}
.cv-word {{ position: absolute; left: 36pt; top: 92pt; font-family: 'Display'; font-size: 162pt;
  line-height: 148pt; letter-spacing: -4pt; color: {INK}; font-variation-settings: 'wght' 700, 'wdth' 76; }}
.cv-block {{ position: absolute; background: {BLUE}; color: #fff; padding: 14pt; display: flex;
  flex-direction: column; justify-content: space-between; }}
.cbn {{ font-family: 'Display'; font-size: 64pt; line-height: 60pt; font-variation-settings: 'wght' 700, 'wdth' 78; }}
.cbt {{ font-family: 'Serif'; font-style: italic; font-size: 12pt; line-height: 16pt; }}
.cv-foot {{ position: absolute; left: {M}pt; right: {M}pt; top: 790pt; display: flex;
  justify-content: space-between; font-family: 'Display'; font-size: 7.4pt; letter-spacing: 1.6pt;
  text-transform: uppercase; color: {GREY}; border-top: 0.7pt solid {INK}; padding-top: 9pt; }}

/* ---------- contents ---------- */
.c-word {{ position: absolute; left: 36pt; top: 52pt; font-family: 'Display'; font-size: 104pt;
  line-height: 94pt; letter-spacing: -2.5pt; color: {INK}; font-variation-settings: 'wght' 700, 'wdth' 76; }}
.c-note {{ position: absolute; left: {M}pt; top: 262pt; width: 300pt; font-style: italic; font-size: 11pt;
  line-height: 16pt; color: {GREY}; }}
.clist {{ position: absolute; left: {M}pt; right: {M}pt; top: 434pt; }}
.crow {{ display: flex; align-items: baseline; gap: 14pt; padding: 6.6pt 0; border-top: 0.6pt solid {HAIR}; }}
.crow:first-child {{ border-top: 0.7pt solid {INK}; }}
.cn {{ flex: none; width: 26pt; font-family: 'Display'; font-size: 15pt; color: {BLUE};
  font-variation-settings: 'wght' 700, 'wdth' 80; }}
.ct {{ flex: 1; min-width: 0; display: flex; align-items: baseline; gap: 12pt; }}
.ctt {{ flex: none; font-family: 'Display'; font-size: 11pt; color: {INK}; text-transform: uppercase;
  letter-spacing: 0.6pt; font-variation-settings: 'wght' 600, 'wdth' 88; }}
.cte {{ flex: 1; min-width: 0; font-size: 7.8pt; color: {GREY}; font-style: italic;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.cp {{ flex: none; font-family: 'Display'; font-size: 9pt; color: {INK}; font-variation-settings: 'wght' 700; }}
.clist.two {{ top: 404pt; display: grid; grid-template-columns: 1fr 1fr; grid-auto-flow: column;
  grid-template-rows: repeat(10, auto); column-gap: 24pt; }}
.clist.two .crow {{ padding: 7.4pt 0; }}
.clist.two .crow:nth-child(11) {{ border-top: 0.7pt solid {INK}; }}
.clist.two .ctt {{ flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  font-size: 10.4pt; }}
"""

FIT_JS = """
<script>
(async function(){
  try { await document.fonts.ready; } catch(e) {}
  await Promise.all(Array.from(document.images).map(i => i.complete ? 1 :
    new Promise(r => { i.onload = i.onerror = r; })));
  const PT = 0.75;
  for (const el of document.querySelectorAll('[data-fit]')) {
    const over = () => el.scrollHeight > el.clientHeight + 0.5;
    let k = 1.0;
    el.style.setProperty('--k', k);
    while (over() && k > 0.72) { k = Math.round((k - 0.01) * 100) / 100; el.style.setProperty('--k', k); }
    el.setAttribute('data-k', k);
    el.setAttribute('data-ok', over() ? '0' : '1');
    const list = el.querySelector('.glist');
    if (list) {
      const pad = parseFloat(getComputedStyle(el).paddingBottom) || 0;
      const left = (el.getBoundingClientRect().bottom - pad - list.getBoundingClientRect().bottom) * PT;
      el.setAttribute('data-left', left.toFixed(1));
    }
  }
  document.body.setAttribute('data-done', '1');
})();
</script>
"""


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #
def wrap(body, script=False):
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f'<title>{BOOK_TITLE}</title><style>{CSS}</style></head>'
            f'<body>{body}{FIT_JS if script else ""}</body></html>')


PAGES_PER_ARTICLE = 3        # opener, reading, questions


def page_map_for(arts):
    return [3 + PAGES_PER_ARTICLE * i for i in range(len(arts))]


def book_body(arts, fit):
    pm = page_map_for(arts)
    questions, essay_words = load_questions(arts)
    out = cover_page(arts) + contents_page(arts, pm)
    for i, a in enumerate(arts):
        n = i + 1
        out += (opener_page(a, n, pm[i]) + reading_page(a, n, pm[i] + 1, fit)
                + questions_page(a, n, pm[i] + 2, questions[n], essay_words))
    return out + back_page(arts)


def measure(arts):
    """Shrink each text box only as far as it needs to fit, and measure the
    space left under each glossary for its photo detail."""
    path = os.path.join(BUILD, "fit_probe.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(wrap(book_body(arts, {}), script=True))
    dom_path = os.path.join(BUILD, "fit_probe_dom.html")
    if os.path.exists(dom_path):
        os.remove(dom_path)
    with open(dom_path, "wb") as out:
        subprocess.run([L.EDGE_EXE, *L.BASE_FLAGS, "--window-size=794,1123",
                        "--virtual-time-budget=60000", "--dump-dom", furl(path)],
                       stdout=out, stderr=subprocess.DEVNULL)
    L.wait_for_output(dom_path, timeout=600)
    dom = open(dom_path, encoding="utf-8", errors="replace").read()
    if 'data-done="1"' not in dom:
        raise RuntimeError("fit probe did not finish")
    fit, bad = {}, []
    for m in re.finditer(r'<(?:article|aside)([^>]*data-fit="([^"]+)"[^>]*)>', dom):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        fit[m.group(2)] = {"k": float(attrs.get("data-k", 1)),
                           "left": float(attrs.get("data-left", 0) or 0)}
        if attrs.get("data-ok") != "1":
            bad.append(m.group(2))
    return fit, bad


def main():
    os.makedirs(BUILD, exist_ok=True)
    count = next((int(a) for a in sys.argv[1:] if a.isdigit()), DEFAULT_COUNT)
    arts = load_articles(count)
    print(f"Loaded {len(arts)} articles ({LEVEL})")
    for i, a in enumerate(arts):
        print(f"  {i + 1:02d} {title_of(a)}  ({len(plain(passage(a)).split())} words, "
              f"{len(vocab(a))} glossary terms)")

    print("Preparing black-and-white photographs...")
    for i, a in enumerate(arts):
        mono(source_image(a, i + 1), i + 1)

    print("Fitting text...")
    fit, bad = measure(arts)
    for key, v in sorted(fit.items()):
        note = f"scaled to {v['k']:.2f}" if v["k"] < 1 else "fits"
        extra = f", {v['left']:.0f}pt free" if key.startswith("gloss") else ""
        print(f"  {key}: {note}{extra}")
    if bad:
        print("  ! still overflowing:", ", ".join(bad))

    print("Rendering...")
    html = os.path.join(BUILD, "article_book.html")
    with open(html, "w", encoding="utf-8") as f:
        f.write(wrap(book_body(arts, fit)))
    raw = os.path.join(BUILD, "article_book.pdf")
    L.edge_pdf(html, raw)

    doc = pymupdf.open(raw)
    pm = page_map_for(arts)
    toc = [[1, "Cover", 1], [1, "Contents", 2]]
    for i, a in enumerate(arts):
        toc.append([1, f"{i + 1:02d} {title_of(a)}", pm[i]])
        toc.append([2, "Speaking and essay", pm[i] + 2])
    toc.append([1, "Back cover", doc.page_count])
    doc.set_toc(toc)
    doc.set_metadata({"title": f"CEFR Articles — {LEVEL}", "author": BOOK_TITLE,
                      "subject": f"{LEVEL} reading articles with glossary"})
    out = os.path.join(ROOT, "CEFR_Article_Book.pdf")
    doc.save(out, garbage=3, deflate=True)
    print(f"Article book: {out} ({doc.page_count} pages)")
    doc.close()


if __name__ == "__main__":
    main()
