"""
CEFR Reading Mock Test Book builder.

Companion to build_cefr_book.py (Listening), which this imports for the shared
page chrome, CSS and Edge plumbing. Geometry is measured from demo_book.pdf
pages 4-7, the "Reading" section of Mock Test 1 (units: pt).

Reading differs from Listening in one structural way: the demo flows a test's
five parts continuously across however many pages it needs, two columns a page,
rather than pinning parts to a fixed page. So the content is rendered as one
multi-column document that Chrome paginates natively, and the page chrome
(stripe, banner, dashed divider, footer) is rendered as a separate layer and
stamped underneath -- which keeps the chrome pixel-identical to the Listening
book instead of reimplementing it with drawing primitives.

Outputs:
  * CEFR_Reading_Mock_Test_Book.pdf        (cover + contents + 71 tests + keys)
  * cefr-reading-pdfs/NNN-<title>.pdf      (one test + its answer key)
"""
import glob
import html as htmlmod
import json
import os
import re
import sys

import pymupdf

import build_cefr_book as L

ROOT_DIR = L.ROOT_DIR
READ_DIR = os.path.join(ROOT_DIR, "cefr-reading")
PDF_OUT_DIR = os.path.join(ROOT_DIR, "cefr-reading-pdfs")
BUILD_DIR = os.path.join(ROOT_DIR, "_build_reading")

BOOK_TITLE = L.BOOK_TITLE
SUBTEXT = "Vaqt: 60 daqiqa. Javoblarni javoblar varaqasiga o‘tkazishni unutmang."

esc = L.esc
furl = L.furl
dash = L.dash

A = dict(L.A)
A["book"] = furl(os.path.join(L.ASSETS, "book_banner.png"))

# --------------------------------------------------------------------------- #
# Geometry (measured off demo_book.pdf pages 4-7)
# --------------------------------------------------------------------------- #
PAGE_W, PAGE_H = 595.32, 841.92
MARGIN_T, MARGIN_B = 28.94, 44.25          # content box 28.94 .. 797.67
MARGIN_L, MARGIN_R = 31.6, 30.52
COL_GAP = 19.4
HEAD_SPACE = 87.08                          # banner + subtext band on page 1
BANNER_TOP = 116.02                         # divider/content top on a test's p1
BODY_TOP = 28.94                            # divider top on continuation pages
SECTION_TOP = 66.0                          # divider top under a section header
CONTENT_BOTTOM = 797.67


# --------------------------------------------------------------------------- #
# CSS
# --------------------------------------------------------------------------- #
CONTENT_CSS = f"""
@font-face {{ font-family: 'Syne'; src: url('{furl(os.path.join(L.FONTS, 'Syne.ttf'))}'); font-weight: 400 800; }}
@font-face {{ font-family: 'Open Sans'; src: url('{furl(os.path.join(L.FONTS, 'OpenSans.ttf'))}'); font-weight: 300 800; font-style: normal; }}
@font-face {{ font-family: 'Open Sans'; src: url('{furl(os.path.join(L.FONTS, 'OpenSans-Italic.ttf'))}'); font-weight: 300 800; font-style: italic; }}

@page {{ size: A4 portrait; margin: {MARGIN_T}pt {MARGIN_R}pt {MARGIN_B}pt {MARGIN_L}pt; }}
* {{ box-sizing: border-box; }}
/* transparent: the chrome layer is stamped underneath these pages */
html, body {{ margin: 0; padding: 0; background: transparent; }}
body {{
  font-family: 'Open Sans', sans-serif; color: #131a33;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
  font-feature-settings: 'lnum'; font-size: 8.53pt; line-height: 12.4pt;
}}
.flow {{ column-count: 2; column-gap: {COL_GAP}pt; }}
/* reserves the banner band on the first page of a test */
.headspace {{ column-span: all; height: {HEAD_SPACE}pt; }}
.newtest {{ break-before: page; }}

/* ---------- part header (identical to Listening) ---------- */
.part {{ margin-top: 10.3pt; }}
.part.first {{ margin-top: 0; }}
.ph {{ display: flex; justify-content: space-between; align-items: flex-end;
      border-bottom: 1.6pt solid #2f5bea; break-after: avoid; }}
.pill {{ background: #1f48d6; color: #fff; font-family: 'Syne'; font-weight: 600; font-size: 10.5pt;
        height: 18pt; line-height: 18pt; padding: 0 10.6pt 0 10.3pt; border-radius: 5.7pt 5.7pt 0 0;
        white-space: nowrap; }}
.qr {{ font-family: 'Syne'; font-weight: 600; font-size: 9.47pt; line-height: 1.2; color: #1f48d6;
      margin-bottom: 4.6pt; white-space: nowrap; }}
/* Reading instructions carry no icon -- Listening's headphone is absent here.
   break-inside: a two-line instruction split across the gutter reads as two
   unrelated fragments, so keep these short blocks whole. */
.inst {{ font-weight: 700; font-size: 8.28pt; line-height: 11.3pt; margin: 4.6pt 0 5.5pt;
        break-after: avoid; break-inside: avoid; }}

/* ---------- passages ---------- */
.ptitle {{ font-family: 'Syne'; font-weight: 600; font-size: 10.4pt; line-height: 1.25; color: #0c2a89;
          text-align: center; text-transform: uppercase; margin: 3pt 0 2.6pt;
          break-after: avoid; break-inside: avoid; }}
.passage p {{ margin: 0 0 4pt 0; text-align: justify; }}
.passage p:last-child {{ margin-bottom: 0; }}
.passage ul {{ margin: 0 0 4pt 0; padding-left: 11pt; }}
.intro {{ font-style: italic; color: #0c2a89; margin-bottom: 3pt; break-inside: avoid; }}
.para {{ margin: 0 0 4pt 0; text-align: justify; }}

/* ---------- inline gap blanks ---------- */
.gn {{ color: #1f48d6; font-weight: 700; font-size: 8.8pt; }}
.blank {{ display: inline-block; width: 56.4pt; height: 0; border-bottom: 0.8pt solid #141b33;
         vertical-align: baseline; margin-left: 1pt; }}

/* ---------- part 2: statements + numbered text cards ---------- */
.stmt {{ padding-left: 11.5pt; text-indent: -11.5pt; margin-bottom: 3.2pt; break-inside: avoid; }}
.tcard {{ background: #fff; border: 0.84pt solid #c9d6f5; border-radius: 7.5pt;
         padding: 6.4pt 8.4pt 7.2pt 8.4pt; margin-top: 5.3pt; break-inside: avoid; }}
.tbadge {{ display: inline-block; min-width: 12.8pt; height: 10.6pt; line-height: 10.6pt; padding: 0 3.4pt;
          background: #1f48d6; color: #fff; border-radius: 5.3pt; text-align: center;
          font-family: 'Syne'; font-weight: 700; font-size: 7.9pt; margin-bottom: 2.6pt; }}
.ttitle {{ font-weight: 700; color: #0c2a89; }}
.tcard p {{ margin: 0; text-align: justify; }}
.tcard ul {{ margin: 0; padding-left: 10pt; }}

/* ---------- part 3: headings list ---------- */
.hcard {{ background: #eef3ff; border: 0.84pt solid #c9d6f5; border-radius: 7.5pt;
         padding: 5.5pt 8.4pt 6.4pt 8.4pt; break-inside: avoid; }}
.hcard .hh {{ font-weight: 700; margin-bottom: 1.4pt; }}
.hrow {{ padding-left: 11pt; text-indent: -11pt; break-inside: avoid; }}
.hsplit {{ border-top: 0.72pt dashed #b8c6ee; margin: 4.6pt 0 4pt; }}
.hqs {{ font-weight: 700; line-height: 13.2pt; }}
.hqs span {{ display: inline-block; min-width: 78pt; }}

/* ---------- questions (identical to Listening) ---------- */
.q {{ break-inside: avoid; margin-bottom: 4.6pt; }}
.badge {{ display: inline-block; min-width: 10.6pt; height: 12pt; line-height: 12pt; padding: 0 3pt;
         background: #edf2ff; color: #1f48d6; border-radius: 2.6pt; text-align: center;
         font-weight: 700; font-size: 8.7pt; }}
.qline {{ display: flex; align-items: flex-start; }}
.qline .badge {{ flex: none; margin-right: 4pt; margin-top: 0.4pt; }}
.qline .qt {{ font-weight: 700; font-size: 8.56pt; line-height: 12.4pt; }}
.opts {{ padding-left: 13.9pt; font-size: 8.53pt; line-height: 12.4pt; }}

/* ---------- part 5 gap-fill summary card ---------- */
.sumcard {{ background: #eef3ff; border: 0.84pt solid #c9d6f5; border-radius: 7.5pt;
           padding: 5.5pt 8.4pt 6.4pt 8.4pt; margin-bottom: 5pt; break-inside: avoid; }}
.sumcard p {{ margin: 0 0 4.4pt 0; }}
.sumcard p:last-child {{ margin-bottom: 0; }}

/* ---------- answer keys ---------- */
.akey {{ break-inside: avoid; margin-bottom: 9.5pt; }}
.akey .card {{ background: #eef3ff; border: 0.84pt solid #c9d6f5; border-radius: 7.5pt;
              padding: 5pt 8.4pt 6pt 8.4pt; }}
/* columns, not a grid: reading answers wrap, and a row grid would stretch
   every column to the tallest cell in the row */
.ak-grid {{ column-count: 3; column-gap: 6pt; font-size: 7.6pt; line-height: 10.4pt; }}
.ak-grid div {{ padding-left: 13pt; text-indent: -13pt; break-inside: avoid; }}
.ak-grid b {{ color: #1f48d6; display: inline-block; min-width: 13pt; text-indent: 0; }}

/* ---------- contents ---------- */
.toc-row {{ display: flex; align-items: baseline; font-size: 9.2pt; line-height: 19.6pt; break-inside: avoid; }}
.toc-row .tn {{ font-weight: 700; color: #131a33; white-space: nowrap; }}
.toc-row .tl {{ color: #6b7590; font-size: 8pt; margin-left: 5pt; white-space: nowrap; }}
.toc-row .dots {{ flex: 1; border-bottom: 0.9pt dotted #b8c6ee; margin: 0 6pt; transform: translateY(-2.5pt); }}
.toc-row .pg {{ display: inline-block; min-width: 20.3pt; height: 10.6pt; line-height: 10.6pt; padding: 0 4pt;
               border-radius: 6pt; background: #edf2ff; color: #1f48d6; text-align: center;
               font-family: 'Syne'; font-weight: 700; font-size: 7.6pt; }}
"""

# The chrome layer reuses the Listening sheet CSS verbatim, plus a Reading banner.
CHROME_CSS = L.CSS + f"""
.banner.read {{ top: 28.3pt; height: 66.3pt; }}
.banner.read .b-book {{ left: 19.8pt; top: 25.9pt; width: 26.3pt; height: 25.2pt; }}
.banner.read .b-title {{ top: 25.4pt; }}
.banner.read .b-parts {{ top: 18.3pt; }}
.banner.read .b-time {{ top: 33.9pt; }}
.subtext.read {{ top: 98.2pt; }}
"""


# --------------------------------------------------------------------------- #
# HTML helpers
# --------------------------------------------------------------------------- #
def wrap(body, css):
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<title>CEFR Reading Mock Tests</title>'
            f"<style>{css}</style></head><body>{body}</body></html>")


def blank(gid, prefix=""):
    return f'<span class="gn">{prefix}{gid}</span><span class="blank"></span>'


def clean_html(raw, gap_prefix=""):
    """Passage HTML -> our markup: gaps become numbered blanks, emphasis and
    bullet lists survive, everything else is dropped."""
    s = raw or ""
    s = re.sub(r'<span[^>]*data-gap="(\d+)"[^>]*>.*?</span>',
               lambda m: f"@@GAP{m.group(1)}@@", s, flags=re.S)
    s = re.sub(r"(?i)<\s*(strong|b)\s*>", "@@B@@", s)
    s = re.sub(r"(?i)<\s*/\s*(strong|b)\s*>", "@@/B@@", s)
    s = re.sub(r"(?i)<\s*(em|i)\s*>", "@@I@@", s)
    s = re.sub(r"(?i)<\s*/\s*(em|i)\s*>", "@@/I@@", s)
    s = re.sub(r"(?i)<\s*li\s*>", "\n@@LI@@", s)
    s = re.sub(r"(?i)<\s*/?\s*(li|ul)\s*>", "\n", s)
    s = re.sub(r"(?i)</p>\s*<p[^>]*>", "\n", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)<h4[^>]*>", "\n@@B@@", s)
    s = re.sub(r"(?i)</h4>", "@@/B@@\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s)

    out, bullets = [], []

    def flush():
        if bullets:
            out.append("<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    for chunk in re.split(r"\n+", s):
        text = re.sub(r"[ \t]+", " ", chunk).strip()
        if not text:
            continue
        is_bullet = text.startswith("@@LI@@")
        body = esc(text[6:].strip() if is_bullet else text)
        body = (body.replace("@@B@@", "<b>").replace("@@/B@@", "</b>")
                    .replace("@@I@@", "<i>").replace("@@/I@@", "</i>"))
        body = re.sub(r"@@GAP(\d+)@@", lambda m: blank(m.group(1), gap_prefix), body)
        if is_bullet:
            bullets.append(body)
        else:
            flush()
            out.append(f"<p>{body}</p>")
    flush()
    return "".join(out)


def inline_html(raw):
    """Statements, stems and titles sometimes carry inline <strong>/<em>
    markup. Escaping them whole prints the tags, so keep the emphasis and drop
    everything else."""
    s = str(raw or "")
    if "<" not in s and "&" not in s:
        return esc(s)
    s = re.sub(r"(?i)<\s*(strong|b)\s*>", "@@B@@", s)
    s = re.sub(r"(?i)<\s*/\s*(strong|b)\s*>", "@@/B@@", s)
    s = re.sub(r"(?i)<\s*(em|i)\s*>", "@@I@@", s)
    s = re.sub(r"(?i)<\s*/\s*(em|i)\s*>", "@@/I@@", s)
    s = re.sub(r"(?i)<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", htmlmod.unescape(s)).strip()
    return (esc(s).replace("@@B@@", "<b>").replace("@@/B@@", "</b>")
                  .replace("@@I@@", "<i>").replace("@@/I@@", "</i>"))


def lettered_line(letter, text):
    """'A) <text>' -- unless the source already opens with its own letter, as
    the lettered descriptions in a few tests do."""
    body = inline_html(text)
    plain = re.sub(r"<[^>]+>", "", body).lstrip()
    if letter and re.match(rf"{re.escape(letter)}[\s).\].\-–—]", plain):
        return body
    return f"{esc(letter)}) {body}"


def part_header(part, first=False):
    rng = dash(part.get("questionRange"))
    inst = inline_html(part.get("instruction"))
    return (f'<div class="part{" first" if first else ""}">'
            f'<div class="ph"><span class="pill">PART {part.get("partNumber")}</span>'
            f'<span class="qr">{"Questions " + rng if rng else ""}</span></div>'
            f'<div class="inst">{inst}</div>')


def dedupe_lettered(items, extra):
    """options/headings/statements plus their 'extra' list, which is either the
    full entry or (more often) just the letter of one already listed."""
    out, seen = [], set()
    for o in list(items or []) + list(extra or []):
        letter, text = (o.get("letter"), o.get("text")) if isinstance(o, dict) else (str(o).strip(), "")
        if not letter or letter in seen:
            continue
        seen.add(letter)
        out.append((letter, text))
    return out


# --------------------------------------------------------------------------- #
# Part renderers
# --------------------------------------------------------------------------- #
def render_part1(part, first=False):
    h = part_header(part, first)
    pas = part.get("passage") or {}
    if pas.get("title"):
        h += f'<div class="ptitle">{inline_html(pas["title"])}</div>'
    h += f'<div class="passage">{clean_html(pas.get("content"), gap_prefix="Q")}</div>'
    return h + "</div>"


def render_part2(part, first=False):
    h = part_header(part, first)
    stmts = "".join(
        f'<div class="stmt">{lettered_line(letter, text)}</div>'
        for letter, text in dedupe_lettered(part.get("statements"), part.get("extraStatements")))
    cards = ""
    for t in part.get("texts") or []:
        cards += f'<div class="tcard"><div class="tbadge">{esc(t.get("number"))}</div>'
        if t.get("title"):
            cards += f'<div class="ttitle">{inline_html(t["title"])}</div>'
        cards += clean_html(t.get("content")) + "</div>"
    # statementsFirst defaults to the demo's order: statements, then the texts
    h += (stmts + cards) if part.get("statementsFirst") is not False else (cards + stmts)
    return h + "</div>"


def para_label(q):
    if q.get("text"):
        return inline_html(q["text"])
    return "Paragraph " + esc(q.get("paragraphNumber") or q.get("paragraphLetter") or "")


def render_part3(part, first=False):
    h = part_header(part, first)
    rows = "".join(f'<div class="hrow">{lettered_line(l, t)}</div>'
                   for l, t in dedupe_lettered(part.get("headings"), part.get("extraHeadings")))
    qs = "".join(f'<span>{q.get("id")}. {para_label(q)}</span> '
                 for q in part.get("questions") or [])
    h += (f'<div class="hcard"><div class="hh">List of Headings:</div>{rows}'
          f'<div class="hsplit"></div><div class="hqs">{qs}</div></div>')
    pas = part.get("passage") or {}
    if pas.get("title"):
        h += f'<div class="ptitle">{inline_html(pas["title"])}</div>'
    if pas.get("intro"):
        h += f'<div class="intro">{inline_html(pas["intro"])}</div>'
    for p in pas.get("paragraphs") or []:
        num = esc(p.get("number") or "")
        body = clean_html(p.get("content"))
        body = re.sub(r"^<p>", f'<p><b>{num}.</b> ' if num else "<p>", body, count=1)
        h += f'<div class="passage para">{body}</div>'
    return h + "</div>"


LETTERS = "ABCDEFGHIJ"


def as_options(raw):
    """Question options are {letter, text}; a section's shared True/False/Not
    Given list is plain strings, which get lettered in order."""
    out = []
    for i, o in enumerate(raw or []):
        if isinstance(o, dict):
            out.append((o.get("letter") or LETTERS[i], o.get("text") or ""))
        else:
            out.append((LETTERS[i], str(o)))
    return out


def render_mcq(q):
    stem = (q.get("text") or q.get("question") or "").strip()
    opts = "".join(f'<div>{esc(letter)}) {inline_html(text)}</div>'
                   for letter, text in as_options(q.get("options")))
    if stem:
        return (f'<div class="q"><div class="qline"><span class="badge">{q.get("id")}</span>'
                f'<span class="qt">{inline_html(stem)}</span></div><div class="opts">{opts}</div></div>')
    return f'<div class="q"><span class="badge">{q.get("id")}</span><div class="opts">{opts}</div></div>'


TFNI_DEFAULT = ["True", "False", "No Information"]


def render_section(sec):
    kind = sec.get("type")
    h = ""
    if sec.get("instruction"):
        h += f'<div class="inst">{inline_html(sec["instruction"])}</div>'
    if kind == "gap-fill":
        if sec.get("summaryTitle"):
            h += f'<div class="ptitle">{inline_html(sec["summaryTitle"])}</div>'
        h += f'<div class="sumcard">{clean_html(sec.get("summaryText"))}</div>'
        return h
    shared = sec.get("options") or (TFNI_DEFAULT if kind == "tfni" else None)
    for q in sec.get("questions") or []:
        if not q.get("options") and shared:
            q = dict(q, options=shared)
        h += render_mcq(q)
    return h


def render_rc(part, first=False):
    h = part_header(part, first)
    pas = part.get("passage") or {}
    if pas.get("title"):
        h += f'<div class="ptitle">{inline_html(pas["title"])}</div>'
    h += f'<div class="passage">{clean_html(pas.get("content"))}</div>'
    for sec in part.get("questionSections") or []:
        h += render_section(sec)
    return h + "</div>"


RENDER = {
    "gap-fill-text": render_part1,
    "matching": render_part2,
    "matching-headings": render_part3,
    "reading-comprehension": render_rc,
}


def render_part(part, first=False):
    if not part:
        return ""
    return RENDER.get(part.get("type"), render_rc)(part, first)


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def test_answers(mock_data):
    out = {}
    for p in mock_data.get("parts", []):
        for k, v in (p.get("answers") or {}).items():
            try:
                qid = int(k)
            except (TypeError, ValueError):
                continue
            vals = v if isinstance(v, list) else [v]
            uniq, seen = [], set()
            for x in vals:
                text = " ".join(str(x).split())
                if text and text.casefold() not in seen:
                    seen.add(text.casefold())
                    uniq.append(text)
            out[qid] = " / ".join(uniq)
    return dict(sorted(out.items()))


def load_tests():
    tests = []
    for fn in sorted(glob.glob(os.path.join(READ_DIR, "*.json"))):
        with open(fn, encoding="utf-8") as f:
            tests.append(json.load(f))
    tests.sort(key=lambda x: x.get("mock_number", 0))
    return tests


# --------------------------------------------------------------------------- #
# Content documents
# --------------------------------------------------------------------------- #
def test_content_html(test):
    parts = sorted(test.get("mock_data", {}).get("parts", []),
                   key=lambda p: p.get("partNumber") or 0)
    body = '<div class="flow"><div class="headspace"></div>'
    for i, p in enumerate(parts):
        body += render_part(p, first=(i == 0))
    return wrap(body + "</div>", CONTENT_CSS)


def answer_card(test):
    num = test.get("mock_number", 0)
    ans = test_answers(test.get("mock_data", {}))
    rows = (len(ans) + 2) // 3
    cells = "".join(f"<div><b>{q}</b>{esc(v)}</div>" for q, v in ans.items())
    return (f'<div class="akey"><div class="ph"><span class="pill">MOCK TEST {num}</span>'
            f'<span class="qr">{len(ans)} answers</span></div>'
            f'<div style="height:5pt"></div><div class="card">'
            f'<div class="ak-grid" style="--rows:{rows}">{cells}</div></div></div>')


def answers_content_html(tests, head=True):
    body = '<div class="flow">'
    if head:
        body += ('<div class="headspace" style="height:37.1pt"></div>')
    body += "".join(answer_card(t) for t in tests)
    return wrap(body + "</div>", CONTENT_CSS)


# --------------------------------------------------------------------------- #
# Chrome layer
# --------------------------------------------------------------------------- #
def banner(test):
    n = test.get("mock_number", 0)
    info = test.get("mock_data", {}).get("testInfo", {}) or {}
    nparts = len(test.get("mock_data", {}).get("parts", [])) or info.get("parts", 5)
    nq = len(test_answers(test.get("mock_data", {}))) or info.get("totalQuestions", 35)
    mins = info.get("totalTime", 60)
    return (f'<div class="banner read">'
            f'<div class="abs b-mock">MOCK TEST {n}</div>'
            f'<img class="abs b-book" src="{A["book"]}">'
            f'<div class="abs b-title">READING</div>'
            f'<div class="abs b-right b-parts">{nparts} parts · {nq} questions</div>'
            f'<div class="abs b-right b-info b-time"><img src="{A["timer"]}">{mins} minutes</div>'
            f'</div>'
            f'<div class="subtext read">{esc(SUBTEXT)}</div>')


def chrome_sheet(label, page_no, top, head_html=""):
    h = PAGE_H - MARGIN_B - top
    return (f'<section class="sheet">'
            f'<img class="stripe" src="{A["stripe"]}">'
            f'{head_html}'
            f'{L.divider(top, h)}'
            f'{L.footer(label, page_no)}'
            f'</section>')


def chrome_html(pages):
    """pages: list of (label, page_no, top, head_html)."""
    return wrap("".join(chrome_sheet(*p) for p in pages), CHROME_CSS)


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render(html, name):
    path = os.path.join(BUILD_DIR, name + ".html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    pdf = os.path.join(BUILD_DIR, name + ".pdf")
    L.edge_pdf(path, pdf)
    return pdf


def stamp(doc, chrome_pdf):
    """Draw the chrome layer underneath each page of doc."""
    chm = pymupdf.open(chrome_pdf)
    if chm.page_count < doc.page_count:
        raise RuntimeError(f"chrome has {chm.page_count} pages, content {doc.page_count}")
    for i in range(doc.page_count):
        doc[i].show_pdf_page(doc[i].rect, chm, i, overlay=False)
    chm.close()


def test_label(test):
    return f"{BOOK_TITLE} · Mock Test {test.get('mock_number')} · Reading"


def build_test_pages(test, idx):
    """Render one test's content once; return (content_pdf, page_count)."""
    pdf = render(test_content_html(test), f"content_{idx}")
    n = pymupdf.open(pdf).page_count
    return pdf, n


def chrome_pages_for(test, n_pages, start_page):
    out = []
    for i in range(n_pages):
        out.append((test_label(test), start_page + i,
                    BANNER_TOP if i == 0 else BODY_TOP,
                    banner(test) if i == 0 else ""))
    return out


# --------------------------------------------------------------------------- #
# Cover / contents
# --------------------------------------------------------------------------- #
def cover_sheet(tests):
    total_q = sum(len(test_answers(t.get("mock_data", {}))) for t in tests)
    return f"""
<section class="sheet">
  <img class="stripe" src="{A['stripe']}">
  <div class="cover-banner">
    <div class="cv-kicker">MULTILEVEL · CEFR</div>
    <img class="cv-hp" src="{A['book']}">
    <div class="cv-title">READING</div>
    <div class="cv-sub">{len(tests)} Mock Tests · {total_q:,} questions</div>
    <div class="cv-line">5 parts per test · gap-fill, matching, headings &amp; comprehension<br>60 minutes per test</div>
    <div class="cv-chips"><span class="cv-chip">B1 · B2 · C1</span><span class="cv-chip">Full passages</span><span class="cv-chip">Full answer keys</span></div>
  </div>
  <div class="cv-body"><div class="cv-grid">
    <div class="card"><div class="cv-h">Part 1 · Part 2</div>Fill each gap with ONE word from the text (Q1–6), then match statements to the short texts (Q7–14).</div>
    <div class="card"><div class="cv-h">Part 3</div>Choose the correct heading for each paragraph (Q15–20). There are always more headings than paragraphs.</div>
    <div class="card"><div class="cv-h">Part 4 · Part 5</div>Two longer texts with multiple choice, True / False / No Information and gap-fill sections (Q21–35).</div>
    <div class="card"><div class="cv-h">How to use</div>Give yourself 60 minutes per test. Write your answers on the answer sheet and check them with the keys at the back.</div>
  </div></div>
  {L.footer(f"{BOOK_TITLE} · CEFR Reading", None)}
</section>"""


def toc_rows(tests, page_map, ans_page):
    rows = ""
    for t in tests:
        n = t.get("mock_number")
        lvl = t.get("mock_data", {}).get("testInfo", {}).get("level") or ""
        rows += (f'<div class="toc-row"><span class="tn">Mock Test {n}</span>'
                 f'<span class="tl">{esc(lvl)}</span><span class="dots"></span>'
                 f'<span class="pg">{page_map[n]}</span></div>')
    rows += (f'<div class="toc-row"><span class="tn" style="color:#0c2a89">Answer Keys</span>'
             f'<span class="dots"></span><span class="pg">{ans_page}</span></div>')
    return rows


def toc_content_html(tests, page_map, ans_page):
    body = ('<div class="flow"><div class="headspace" style="height:37.1pt"></div>'
            + toc_rows(tests, page_map, ans_page) + "</div>")
    return wrap(body, CONTENT_CSS)


def section_head(title, right):
    return (f'<div class="cols" style="top:28.9pt;height:40pt;column-count:1">'
            f'<div class="ph"><span class="pill">{esc(title)}</span>'
            f'<span class="qr">{esc(right)}</span></div></div>')


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(PDF_OUT_DIR, exist_ok=True)
    tests = load_tests()
    only = [int(a) for a in sys.argv[1:] if a.isdigit()]
    if only:
        tests = [t for t in tests if t.get("mock_number") in only]
    print(f"Loaded {len(tests)} tests")

    # ---- pass 1: render each test's content, learn its page count ----------
    print("Rendering test content...")
    content, counts = [], []
    for i, t in enumerate(tests):
        pdf, n = build_test_pages(t, t.get("mock_number"))
        content.append(pdf)
        counts.append(n)
        print(f"  Mock {t.get('mock_number')}: {n} pages")

    # ---- answer-key + contents content, to learn their page counts ---------
    ans_content = render(answers_content_html(tests), "content_answers")
    ans_n = pymupdf.open(ans_content).page_count

    first_page = 3
    page_map, p = {}, first_page
    for t, n in zip(tests, counts):
        page_map[t.get("mock_number")] = p
        p += n
    ans_page = p

    toc_content = render(toc_content_html(tests, page_map, ans_page), "content_toc")
    toc_n = pymupdf.open(toc_content).page_count
    if toc_n > 1:                       # contents spilled: shift everything down
        shift = toc_n - 1
        page_map = {k: v + shift for k, v in page_map.items()}
        ans_page += shift
        toc_content = render(toc_content_html(tests, page_map, ans_page), "content_toc")

    # ---- chrome for the book ----------------------------------------------
    print("Rendering book chrome...")
    nums = [t.get("mock_number") for t in tests]
    pages = [(f"{BOOK_TITLE} · Contents", 2 + i, SECTION_TOP if i == 0 else BODY_TOP,
              section_head("CONTENTS", f"{len(tests)} mock tests") if i == 0 else "")
             for i in range(toc_n)]
    for t, n in zip(tests, counts):
        pages += chrome_pages_for(t, n, page_map[t.get("mock_number")])
    pages += [(f"{BOOK_TITLE} · Answer Keys", ans_page + i, SECTION_TOP if i == 0 else BODY_TOP,
               section_head("ANSWER KEYS", f"Mock Tests {nums[0]}–{nums[-1]}") if i == 0 else "")
              for i in range(ans_n)]
    book_chrome = render(chrome_html(pages), "chrome_book")

    # ---- assemble ----------------------------------------------------------
    print("Assembling book...")
    cover = render(wrap(cover_sheet(tests), CHROME_CSS), "cover")
    book = pymupdf.open(cover)
    body = pymupdf.open()
    body.insert_pdf(pymupdf.open(toc_content))
    for pdf in content:
        body.insert_pdf(pymupdf.open(pdf))
    body.insert_pdf(pymupdf.open(ans_content))
    stamp(body, book_chrome)
    book.insert_pdf(body)

    toc = [[1, "Cover", 1], [1, "Contents", 2]]
    for t in tests:
        toc.append([1, f"Mock Test {t.get('mock_number')}", page_map[t.get("mock_number")]])
    toc.append([1, "Answer Keys", ans_page])
    book.set_toc(toc)
    book.set_metadata({"title": "CEFR Reading Mock Tests", "author": BOOK_TITLE,
                       "subject": "CEFR Reading"})
    out = os.path.join(ROOT_DIR, "CEFR_Reading_Mock_Test_Book%s.pdf" % ("_subset" if only else ""))
    book.save(out, garbage=3, deflate=True)
    print(f"Master book: {out} ({book.page_count} pages)")
    book.close()

    # ---- individual PDFs ---------------------------------------------------
    if "--no-single" in sys.argv:
        return
    print("Rendering individual test PDFs...")
    for t, pdf, n in zip(tests, content, counts):
        num = t.get("mock_number")
        one_ans = render(answers_content_html([t], head=False), f"content_ans_{num}")
        one_ans_n = pymupdf.open(one_ans).page_count
        pages = chrome_pages_for(t, n, 1)
        pages += [(f"{BOOK_TITLE} · Mock Test {num} · Answer Key", n + 1 + i, BODY_TOP, "")
                  for i in range(one_ans_n)]
        chrome = render(chrome_html(pages), f"chrome_{num}")
        merged = pymupdf.open(pdf)
        merged.insert_pdf(pymupdf.open(one_ans))
        stamp(merged, chrome)
        safe = re.sub(r'[\\/:*?"<>|]+', "-", t.get("title", f"Test {num}")).strip()
        dest = os.path.join(PDF_OUT_DIR, f"{str(num).zfill(3)}-{safe}.pdf")
        merged.save(dest, garbage=3, deflate=True)
        merged.close()
        print(f"  {os.path.basename(dest)}")


if __name__ == "__main__":
    main()
