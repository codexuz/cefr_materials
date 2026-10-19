"""
CEFR Listening Mock Test Book builder.

Renders every cefr-listening/*.json test into a pixel-faithful replica of the
demo_book.pdf "Listening" layout (2 pages per test, 2 columns with a dashed
vertical split), then assembles:
  * CEFR_Listening_Mock_Test_Book.pdf   (cover + contents + 57 tests + answer keys)
  * cefr-listening-pdfs/NNN-<title>.pdf (one 2-page PDF + answer page per test)

All geometry below was measured directly from demo_book.pdf (units: pt).
"""
import glob
import html as htmlmod
import json
import os
import re
import atexit
import shutil
import subprocess
import tempfile
import time
import sys
from urllib.parse import unquote, urlparse

import pymupdf

ROOT_DIR = os.path.abspath(r"C:\temporary\multilevel_reels\materials")
CEFR_DIR = os.path.join(ROOT_DIR, "cefr-listening")
MEDIA_DIR = os.path.join(ROOT_DIR, "media")
ASSETS = os.path.join(MEDIA_DIR, "assets")
FONTS = os.path.join(ASSETS, "fonts")
PDF_OUT_DIR = os.path.join(ROOT_DIR, "cefr-listening-pdfs")
BUILD_DIR = os.path.join(ROOT_DIR, "_build")
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_EXE):
    EDGE_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

BOOK_TITLE = "Multilevel Mock Tests"
AUDIO_LINK = "t.me/multilevel_express"


def furl(path):
    return "file:///" + path.replace("\\", "/")


A = {k: furl(os.path.join(ASSETS, v)) for k, v in {
    "stripe": "x4.jpeg",          # full-bleed gradient top stripe
    "banner": "x7.jpeg",          # banner background with geometric pattern
    "hp_banner": "x8.jpeg",       # big headphone emoji in banner
    "timer": "x10.jpeg",          # stopwatch emoji
    "hp_small": "x12.jpeg",       # small headphone emoji (audio line)
    "hp_inst": "x13.jpeg",        # instruction headphone icon
}.items()}


# --------------------------------------------------------------------------- #
# Data helpers
# --------------------------------------------------------------------------- #
def esc(s):
    return htmlmod.escape(str(s or ""), quote=False)


def resolve_image(url):
    if not url:
        return ""
    path_part = unquote(urlparse(url).path).lstrip("/")
    local_path = os.path.abspath(os.path.join(MEDIA_DIR, path_part))
    return furl(local_path) if os.path.exists(local_path) else ""


def dash(rng):
    return str(rng or "").replace("-", "–")


def extract_test_answers(mock_data):
    out = {}
    for p in mock_data.get("parts", []):
        for k, v in (p.get("answers") or {}).items():
            try:
                qid = int(k)
            except (TypeError, ValueError):
                continue
            # Keys list every accepted spelling, including pure case variants
            # ("water / Water / WATER"); keep one of each so the printed key
            # stays readable without dropping a genuine alternative.
            vals = v if isinstance(v, list) else [v]
            uniq, seen = [], set()
            for x in vals:
                text = " ".join(str(x).split())
                key = text.casefold()
                if text and key not in seen:
                    seen.add(key)
                    uniq.append(text)
            out[qid] = " / ".join(uniq)
    return dict(sorted(out.items()))


def get_parts(data):
    parts = data.get("mock_data", {}).get("parts", [])
    by_num = {p.get("partNumber"): p for p in parts}
    return [by_num.get(i) or (parts[i - 1] if len(parts) >= i else None) for i in range(1, 7)]


# --------------------------------------------------------------------------- #
# CSS  (sizes are multiplied by --k, the per-page fit factor; 1 = demo size)
# --------------------------------------------------------------------------- #
def K(v):
    return f"calc({v}pt * var(--k))"


# Dashed column divider, measured off demo_book.pdf (181 dashes over 679.36pt
# on page 1, 205 over 768.73pt on page 2).
DASH_LEN = 2.25
DASH_PERIOD = 3.758


def divider(top, height):
    # round, not floor: the demo runs the dashes right down to the column
    # bottom (181 over 679.4pt, 205 over 768.8pt).
    n = round((height - DASH_LEN) / DASH_PERIOD) + 1
    dashes = "".join(f'<i style="top:{i * DASH_PERIOD:.2f}pt"></i>' for i in range(n))
    return f'<div class="divider" style="top:{top}pt;height:{height}pt">{dashes}</div>'


CSS = f"""
@font-face {{ font-family: 'Syne'; src: url('{furl(os.path.join(FONTS, 'Syne.ttf'))}'); font-weight: 400 800; }}
@font-face {{ font-family: 'Open Sans'; src: url('{furl(os.path.join(FONTS, 'OpenSans.ttf'))}'); font-weight: 300 800; font-style: normal; }}
@font-face {{ font-family: 'Open Sans'; src: url('{furl(os.path.join(FONTS, 'OpenSans-Italic.ttf'))}'); font-weight: 300 800; font-style: italic; }}

@page {{ size: A4 portrait; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #fff; }}
body {{
  font-family: 'Open Sans', sans-serif; color: #131a33;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
  font-feature-settings: 'lnum';
}}
.sheet {{
  --k: 1;
  position: relative; width: 210mm; height: 297mm; overflow: hidden;
  page-break-after: always; break-after: page; background: #fff;
}}
.sheet:last-child {{ page-break-after: auto; break-after: auto; }}
.stripe {{ position: absolute; left: 0.1pt; top: 0.7pt; width: 595.6pt; height: 10.9pt; display: block; }}

/* ---------- banner ---------- */
.banner {{
  position: absolute; left: 31.4pt; top: 28.3pt; width: 533.4pt; height: 68.3pt;
  border-radius: 12.5pt; overflow: hidden;
  background: url('{A['banner']}') center / 100% 100% no-repeat;
}}
.banner .abs {{ position: absolute; white-space: nowrap; }}
.b-mock {{
  left: 19.8pt; top: 17.2pt; font-family: 'Syne'; font-weight: 600; font-size: 9.5pt; line-height: 1;
  letter-spacing: 2.05pt; color: #dfe6fb;
}}
.b-hp {{ left: 19.8pt; top: 27.4pt; width: 26.3pt; height: 25.2pt; }}
.b-title {{
  left: 52.4pt; top: 26.2pt; font-family: 'Syne'; font-weight: 600; font-size: 25pt; line-height: 1;
  color: #fff; letter-spacing: 0;
}}
.b-right {{ right: 20pt; text-align: right; }}
.b-parts {{ top: 13.2pt; font-family: 'Syne'; font-weight: 600; font-size: 12.7pt; line-height: 1; color: #fff; }}
.b-info {{ font-size: 8.65pt; line-height: 1; color: #fff; display: flex; align-items: center; justify-content: flex-end; }}
.b-info img {{ width: 10.5pt; height: 10.1pt; margin-right: 2.4pt; }}
.b-time {{ top: 28.6pt; }}
.b-audio {{ top: 42.3pt; }}
.subtext {{
  position: absolute; left: 34.2pt; top: 101.2pt; font-style: italic; font-size: 8pt; line-height: 1.3;
  color: #6b7590; white-space: nowrap;
}}

/* ---------- columns + divider ---------- */
.cols {{
  position: absolute; left: 31.6pt; width: 533.2pt;
  column-count: 2; column-gap: 19.4pt; column-fill: auto; orphans: 1; widows: 1;
}}
/* Dashes are real elements, not a repeating gradient: Chrome rasterises a
   gradient on a 0.72pt-wide box into a 2px image, which quantises the rhythm.
   Measured from demo_book.pdf: dash 2.25pt, period 3.758pt, width 0.72pt. */
.divider {{ position: absolute; left: 298.24pt; width: 0.72pt; }}
.divider i {{
  position: absolute; left: 0; width: 0.72pt; height: {DASH_LEN}pt;
  background: #c9d6f5; display: block;
}}
.colbreak {{ break-before: column; }}
.sentinel {{ height: 0; }}

/* ---------- part header ---------- */
.part {{ margin-top: {K(10.3)}; }}
.part.first {{ margin-top: 0; }}
.ph {{ display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1.6pt solid #2f5bea; break-after: avoid; }}
.pill {{
  background: #1f48d6; color: #fff; font-family: 'Syne'; font-weight: 600; font-size: {K(10.5)};
  height: {K(18)}; line-height: {K(18)}; padding: 0 {K(10.6)} 0 {K(10.3)}; border-radius: 5.7pt 5.7pt 0 0;
  white-space: nowrap;
}}
.qr {{ font-family: 'Syne'; font-weight: 600; font-size: {K(9.47)}; line-height: 1.2; color: #1f48d6; margin-bottom: {K(4.6)}; white-space: nowrap; }}
.inst {{ display: flex; align-items: flex-start; margin-top: {K(4.2)}; margin-bottom: {K(5.5)}; break-after: avoid; }}
.inst img {{ width: {K(12)}; height: {K(12)}; flex: none; margin-top: {K(1.3)}; margin-left: 0.3pt; }}
.inst div {{ padding-left: {K(3.9)}; font-weight: 700; font-size: {K(8.28)}; line-height: {K(11.3)}; }}

/* ---------- part 1 / generic MCQ ---------- */
.q {{ break-inside: avoid; margin-bottom: {K(4.1)}; }}
.badge {{
  display: inline-block; min-width: {K(10.6)}; height: {K(12)}; line-height: {K(12)}; padding: 0 {K(3)};
  background: #edf2ff; color: #1f48d6; border-radius: {K(2.6)}; text-align: center;
  font-weight: 700; font-size: {K(8.7)};
}}
.opts {{ padding-left: {K(13.9)}; font-size: {K(8.53)}; line-height: {K(12.55)}; }}
.qline {{ display: flex; align-items: flex-start; }}
.qline .badge {{ flex: none; margin-right: {K(4)}; margin-top: {K(0.4)}; }}
.qline .qt {{ font-weight: 700; font-size: {K(8.56)}; line-height: {K(12.4)}; }}
.q5 .opts {{ line-height: {K(12.4)}; }}

/* ---------- cards ---------- */
.card {{
  background: #eef3ff; border: 0.84pt solid #c9d6f5; border-radius: {K(7.5)};
  padding: {K(5.5)} {K(8.4)} {K(7.6)} {K(8.4)}; font-size: {K(8.53)}; line-height: {K(12.6)};
}}
.ctitle {{
  font-family: 'Syne'; font-weight: 600; font-size: {K(10.4)}; line-height: 1.2; color: #0c2a89;
  text-align: center; text-transform: uppercase; margin-bottom: {K(1.5)};
}}
.frow {{ margin-bottom: {K(1.6)}; }}
.frow.lab {{ display: grid; grid-template-columns: {K(72)} 1fr; column-gap: {K(5)}; }}
.frow.lab .l {{ font-weight: 700; }}
.fhead {{ font-weight: 700; color: #0c2a89; margin-top: {K(2.5)}; }}
.fex {{ font-style: italic; color: #4a5470; }}
.gn {{ color: #1f48d6; font-weight: 700; font-size: {K(8.8)}; }}
.blank {{ display: inline-block; width: {K(56.4)}; height: 0; border-bottom: 0.8pt solid #141b33; vertical-align: baseline; margin-left: {K(1)}; }}
.match {{ display: grid; grid-template-columns: {K(72)} 1fr; column-gap: {K(5)}; line-height: {K(13.85)}; }}

/* ---------- part 4 ---------- */
.maptitle {{ font-weight: 700; font-size: {K(8.73)}; line-height: {K(12)}; color: #0c2a89; text-transform: uppercase; margin-bottom: {K(2.4)}; break-after: avoid; }}
.mapframe {{ border: 0.84pt solid #c9d6f5; border-radius: {K(6)}; overflow: hidden; break-inside: avoid; line-height: 0; text-align: center; background: #fff; }}
.mapframe img {{ width: 100%; max-height: var(--maph, 277pt); object-fit: contain; display: block; margin: 0 auto; }}
.mapqs {{ margin-top: {K(6.8)}; font-weight: 700; font-size: {K(8.51)}; line-height: {K(13.85)}; break-before: avoid; }}

/* ---------- part 5 ---------- */
.ext {{ break-inside: avoid; }}
.ext + .ext {{ margin-top: {K(5.6)}; }}
.etitle {{ font-weight: 700; font-size: {K(8.78)}; line-height: {K(12.6)}; color: #0c2a89; }}
.ectx {{ font-style: italic; font-size: {K(8.87)}; line-height: {K(12.4)}; color: #0c2a89; margin-bottom: {K(2.6)}; }}
.q5 {{ margin-bottom: {K(4.6)}; }}

/* ---------- part 6 ---------- */
.passage p {{ margin: 0 0 {K(2.8)} 0; line-height: {K(12.2)}; }}
.passage p:last-child {{ margin-bottom: 0; }}

/* ---------- footer ---------- */
.frule {{ position: absolute; left: 31.6pt; top: 803.6pt; width: 533.2pt; height: 0.9pt; background: #c9d6f5; }}
.ftext {{ position: absolute; left: 31.6pt; top: 810.6pt; font-size: 7.04pt; line-height: 1.2; color: #6b7590; white-space: nowrap; }}
.fpill {{
  position: absolute; right: 30.4pt; top: 809.7pt; min-width: 20.3pt; height: 10.6pt; padding: 0 5pt;
  border-radius: 6pt; background: #1f48d6; color: #fff; text-align: center;
  font-family: 'Syne'; font-weight: 700; font-size: 8pt; line-height: 10.6pt;
}}

/* ---------- cover ---------- */
.cover-banner {{
  position: absolute; left: 31.4pt; top: 28.3pt; width: 533.4pt; height: 400pt; border-radius: 16pt; overflow: hidden;
  background: url('{A['banner']}') left center / auto 100% repeat-x, linear-gradient(110deg, #3b6cf2, #1d3fc9 55%, #13289a);
}}
.cv-kicker {{ position: absolute; left: 34pt; top: 46pt; font-family: 'Syne'; font-weight: 600; font-size: 13pt; letter-spacing: 3.2pt; color: #dfe6fb; }}
.cv-hp {{ position: absolute; left: 34pt; top: 78pt; width: 74pt; height: 71pt; }}
.cv-title {{ position: absolute; left: 118pt; top: 80pt; font-family: 'Syne'; font-weight: 600; font-size: 62pt; line-height: 1; color: #fff; }}
.cv-sub {{ position: absolute; left: 34pt; top: 178pt; font-family: 'Syne'; font-weight: 600; font-size: 22pt; color: #fff; }}
.cv-line {{ position: absolute; left: 34pt; top: 216pt; font-size: 11pt; color: #e5ebff; line-height: 1.6; }}
.cv-chips {{ position: absolute; left: 34pt; bottom: 30pt; display: flex; gap: 8pt; }}
.cv-chip {{ background: rgba(255,255,255,.14); border: 0.8pt solid rgba(255,255,255,.35); color: #fff; border-radius: 20pt; padding: 4pt 11pt; font-size: 9pt; font-weight: 600; }}
.cv-body {{ position: absolute; left: 31.6pt; top: 452pt; width: 533.2pt; }}
.cv-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12pt 19.4pt; }}
.cv-grid .card {{ --k: 1; }}
.cv-h {{ font-family: 'Syne'; font-weight: 600; font-size: 10.4pt; color: #0c2a89; margin-bottom: 3pt; text-transform: uppercase; }}

/* ---------- contents ---------- */
.toc-row {{ display: flex; align-items: baseline; font-size: 9.2pt; line-height: 19.6pt; break-inside: avoid; }}
.toc-row a {{ color: inherit; text-decoration: none; display: flex; align-items: baseline; width: 100%; }}
.toc-row .tn {{ font-weight: 700; color: #131a33; white-space: nowrap; }}
.toc-row .tl {{ color: #6b7590; font-size: 8pt; margin-left: 5pt; white-space: nowrap; }}
.toc-row .dots {{ flex: 1; border-bottom: 0.9pt dotted #b8c6ee; margin: 0 6pt; transform: translateY(-2.5pt); }}
.toc-row .pg {{ display: inline-block; min-width: 20.3pt; height: 10.6pt; line-height: 10.6pt; padding: 0 4pt; border-radius: 6pt; background: #edf2ff; color: #1f48d6; text-align: center; font-family: 'Syne'; font-weight: 700; font-size: 7.6pt; }}

/* ---------- answer keys ---------- */
.akey {{ break-inside: avoid; margin-bottom: 9.5pt; }}
.akey .card {{ --k: 1; padding: 5pt 8.4pt 6pt 8.4pt; }}
.ak-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); grid-auto-flow: column; grid-template-rows: repeat(var(--rows), auto); column-gap: 6pt; font-size: 7.6pt; line-height: 10.4pt; }}
/* Answers wrap rather than being clipped: a truncated key is unusable.
   Wrapped lines hang under the answer, clear of the question number. */
.ak-grid div {{ padding-left: 13pt; text-indent: -13pt; }}
.ak-grid b {{ color: #1f48d6; display: inline-block; min-width: 13pt; text-indent: 0; }}
"""

FIT_JS = """
<script>
(async function(){
  try { await document.fonts.ready; } catch(e) {}
  const imgs = Array.from(document.images);
  await Promise.all(imgs.map(i => i.complete ? 1 : new Promise(r => { i.onload = i.onerror = r; })));
  for (const sheet of document.querySelectorAll('.sheet[data-fit]')) {
    const cols = sheet.querySelector('.cols');
    const sen = sheet.querySelector('.sentinel');
    const fits = () => {
      const cr = cols.getBoundingClientRect(), sr = sen.getBoundingClientRect();
      return sr.left < cr.right - 2 && sr.top <= cr.bottom + 0.5;
    };
    let k = 1.0, maph = 277;
    sheet.style.setProperty('--maph', maph + 'pt');
    while (!fits() && maph > 200) { maph -= 7; sheet.style.setProperty('--maph', maph + 'pt'); }
    while (!fits() && k > 0.74) { k = Math.round((k - 0.01) * 100) / 100; sheet.style.setProperty('--k', k); }
    sheet.setAttribute('data-k', k);
    sheet.setAttribute('data-maph', maph);
    sheet.setAttribute('data-ok', fits() ? '1' : '0');
  }
  document.body.setAttribute('data-done', '1');
})();
</script>
"""


# --------------------------------------------------------------------------- #
# Part renderers
# --------------------------------------------------------------------------- #
def blank(gid, paren=False):
    label = f"({gid})" if paren else f"{gid}"
    return f'<span class="gn">{label}</span><span class="blank"></span>'


def part_header(part, first=False):
    pnum = part.get("partNumber")
    rng = dash(part.get("questionRange"))
    inst = esc(part.get("instruction") or part.get("instructions") or "")
    return (f'<div class="part{" first" if first else ""}">'
            f'<div class="ph"><span class="pill">PART {pnum}</span>'
            f'<span class="qr">{"Questions " + rng if rng else ""}</span></div>'
            f'<div class="inst"><img src="{A["hp_inst"]}"><div>{inst}</div></div>')


def render_mcq_question(q, bold_stem=True):
    qid = q.get("id")
    stem = (q.get("text") or q.get("question") or "").strip()
    opts = "".join(f'<div>{esc(o.get("letter"))}) {esc(o.get("text"))}</div>' for o in q.get("options", []))
    if stem:
        return (f'<div class="q q5"><div class="qline"><span class="badge">{qid}</span>'
                f'<span class="qt">{esc(stem)}</span></div><div class="opts">{opts}</div></div>')
    return f'<div class="q"><span class="badge">{qid}</span><div class="opts">{opts}</div></div>'


def render_part1(part, first=False):
    h = part_header(part, first)
    for q in part.get("questions", []):
        h += render_mcq_question(q)
    return h + "</div>"


def split_label(text):
    """'Price:' / 'Book types: school subject books,' -> (label, rest) if short label."""
    m = re.match(r"^([^:]{1,40}:)\s*(.*)$", text)
    if m and len(m.group(1).split()) <= 6 and not re.search(r"\d[:.]\d", text[:len(m.group(1)) + 2]):
        return m.group(1), m.group(2)
    return None, text


def render_part2(part, first=False):
    h = part_header(part, first)
    title = part.get("formTitle") or ""
    h += '<div class="card">'
    if title:
        h += f'<div class="ctitle">{esc(title)}</div>'
    rows = []  # list of dict(kind, label, html)
    for it in part.get("formContent", []):
        t = it.get("type")
        text = re.sub(r"^\(\d+\)\s*", "", (it.get("text") or "").strip())
        if t in ("heading", "section-header"):
            rows.append({"kind": "head", "html": esc(text)})
            continue
        if t == "example":
            lab, rest = split_label(text)
            val = f'<span class="fex">{esc(rest)} {esc(it.get("answer", ""))}</span>'
            rows.append({"kind": "lab", "label": esc(lab or text), "html": val} if lab else {"kind": "p", "html": esc(text) + " " + val})
            continue
        if t == "label":
            rows.append({"kind": "lab", "label": esc(text), "html": ""})
            continue
        if t == "item-gap":
            prefix = re.sub(r"^\(\d+\)\s*", "", (it.get("gapPrefix") or "").strip())
            suffix = (it.get("gapSuffix") or "").strip()
            lab, rest = split_label(text)
            body = " ".join(x for x in [esc(rest), esc(prefix)] if x)
            body = (body + " " if body else "") + blank(it.get("gapId"))
            if suffix:
                body += ("" if suffix[0] in ",.;:!?)" else " ") + esc(suffix)
            if lab:
                # attach to a dangling label row created by a 'label' item
                rows.append({"kind": "lab", "label": esc(lab), "html": body})
            elif rows and rows[-1]["kind"] == "lab" and not rows[-1]["html"]:
                rows[-1]["html"] = body
            elif rows and rows[-1]["kind"] == "p" and re.match(r"^(And|and|but|or)\b", text):
                prev = rows[-1]["html"].rstrip()
                if prev and prev[-1] not in ".!?":
                    prev += "."
                rows[-1]["html"] = prev + " " + body
            else:
                rows.append({"kind": "p", "html": body})
            continue
        # item / text / anything else
        lab, rest = split_label(text)
        if lab and t == "item":
            rows.append({"kind": "lab", "label": esc(lab), "html": esc(rest)})
        else:
            rows.append({"kind": "p", "html": esc(text)})
    for r in rows:
        if r["kind"] == "head":
            h += f'<div class="frow fhead">{r["html"]}</div>'
        elif r["kind"] == "lab":
            h += f'<div class="frow lab"><span class="l">{r["label"]}</span><span>{r["html"]}</span></div>'
        else:
            h += f'<div class="frow">{r["html"]}</div>'
    return h + "</div></div>"


def lc_first(s):
    s = (s or "").strip()
    if len(s) > 1 and s[0].isupper() and s[1].islower() and not s.split()[0] in ("I", "I'm", "I've"):
        return s[0].lower() + s[1:]
    return s


def render_part3(part, first=False):
    h = part_header(part, first)
    spk = "".join(f'<div>{s.get("id")}. {esc(s.get("label"))} ....</div>' for s in part.get("speakers", []))
    opts = list(part.get("options", [])) + list(part.get("extraOptions") or [])
    seen, ol = set(), []
    for o in opts:
        # extraOptions is either the full distractor option (letter + text) or,
        # in 11 of the tests, just the letter of an option already in options.
        key, text = (o.get("letter"), o.get("text")) if isinstance(o, dict) else (str(o).strip(), "")
        if not key or key in seen:
            continue
        seen.add(key)
        ol.append(f'<div>{esc(key)}) {esc(lc_first(text))}</div>')
    h += f'<div class="card match"><div>{spk}</div><div>{"".join(ol)}</div></div>'
    return h + "</div>"


def render_part4(part, first=False):
    h = part_header(part, first)
    title = part.get("mapTitle") or ""
    if title:
        h += f'<div class="maptitle">{esc(title)}</div>'
    img = resolve_image(part.get("mapImage"))
    if img:
        h += f'<div class="mapframe"><img src="{img}"></div>'
    qs = "".join(
        f'<div>{q.get("id")}. {esc((q.get("place") or q.get("text") or "").strip().rstrip(".").rstrip())} ...</div>'
        for q in part.get("questions", []))
    h += f'<div class="mapqs">{qs}</div>'
    return h + "</div>"


def render_part5(part, first=False):
    h = part_header(part, first)
    exts = part.get("extracts") or []
    if exts:
        for e in exts:
            h += '<div class="ext">'
            if e.get("title"):
                h += f'<div class="etitle">{esc(e.get("title"))}</div>'
            if e.get("context"):
                h += f'<div class="ectx">{esc(e.get("context"))}</div>'
            for q in e.get("questions", []):
                h += render_mcq_question(q)
            h += "</div>"
    else:
        for q in part.get("questions", []):
            h += render_mcq_question(q)
    return h + "</div>"


def clean_passage(raw):
    s = raw or ""
    s = re.sub(r'<span[^>]*data-gap="(\d+)"[^>]*>.*?</span>', lambda m: f"@@GAP{m.group(1)}@@", s, flags=re.S)
    s = re.sub(r"(?i)</p>\s*<p[^>]*>", "<br><br>", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s)
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n|\n", s)]
    out = []
    for p in paras:
        if not p:
            continue
        p = esc(p)
        p = re.sub(r"@@GAP(\d+)@@", lambda m: blank(m.group(1), paren=True), p)
        out.append(f"<p>{p}</p>")
    return "".join(out)


def render_part6(part, first=False):
    h = part_header(part, first)
    title = part.get("passageTitle") or ""
    h += '<div class="card passage">'
    if title:
        h += f'<div class="ctitle">{esc(title)}</div>'
    h += clean_passage(part.get("passageContent")) + "</div>"
    return h + "</div>"


RENDER = {
    "mcq-reply": render_part1, "mcq": render_part5, "gap-fill-form": render_part2,
    "matching-speakers": render_part3, "map-labeling": render_part4,
    "mcq-extracts": render_part5, "sentence-completion": render_part6,
}


def render_any(part, first=False):
    if not part:
        return ""
    return RENDER.get(part.get("type"), render_part5)(part, first)


# --------------------------------------------------------------------------- #
# Sheets
# --------------------------------------------------------------------------- #
def footer(label, page_no):
    pill = f'<div class="fpill">{page_no}</div>' if page_no is not None else ""
    return f'<div class="frule"></div><div class="ftext">{esc(label)}</div>{pill}'


def test_sheets(data, page1, page2, fit=None, anchor=True):
    num = data.get("mock_number", 0)
    ans = extract_test_answers(data.get("mock_data", {}))
    total_q = len(ans) or data.get("mock_data", {}).get("testInfo", {}).get("totalQuestions", 35)
    p = get_parts(data)
    flabel = f"{BOOK_TITLE} · Mock Test {num} · Listening"
    fit = fit or {}

    def style(idx):
        f = fit.get((num, idx))
        if not f:
            return ""
        return f' style="--k:{f[0]};--maph:{f[1]}pt"'

    aid = f' id="test-{num}"' if anchor else ""
    s1 = f"""
<section class="sheet" data-fit="1" data-test="{num}" data-idx="1"{style(1)}{aid}>
  <img class="stripe" src="{A['stripe']}">
  <div class="banner">
    <div class="abs b-mock">MOCK TEST {num}</div>
    <img class="abs b-hp" src="{A['hp_banner']}">
    <div class="abs b-title">LISTENING</div>
    <div class="abs b-right b-parts">{len([x for x in p if x])} parts · {total_q} questions</div>
    <div class="abs b-right b-info b-time"><img src="{A['timer']}">approx. 35 minutes</div>
    <div class="abs b-right b-info b-audio"><img src="{A['hp_small']}">Audio: {AUDIO_LINK}</div>
  </div>
  <div class="subtext">Har bir audio ikki marta eshittiriladi. Javoblarni javoblar varaqasiga yozing.</div>
  <div class="cols" style="top:118.3pt;height:679.4pt">
    {render_any(p[0], first=True)}
    <div class="colbreak"></div>
    {render_any(p[1], first=True)}
    {render_any(p[2])}
    <div class="sentinel"></div>
  </div>
  {divider(118.3, 679.4)}
  {footer(flabel, page1)}
</section>
<section class="sheet" data-fit="1" data-test="{num}" data-idx="2"{style(2)}>
  <img class="stripe" src="{A['stripe']}">
  <div class="cols" style="top:28.9pt;height:768.8pt">
    {render_any(p[3], first=True)}
    {render_any(p[4])}
    {render_any(p[5])}
    <div class="sentinel"></div>
  </div>
  {divider(28.9, 768.8)}
  {footer(flabel, page2)}
</section>"""
    return s1


def answer_card(data, idx=None):
    num = data.get("mock_number", 0)
    ans = extract_test_answers(data.get("mock_data", {}))
    rows = (len(ans) + 2) // 3
    cells = "".join(f"<div><b>{q}</b>{esc(v)}</div>" for q, v in ans.items())
    mark = f' data-i="{idx}"' if idx is not None else ""
    return (f'<div class="akey"{mark}><div class="ph"><span class="pill">MOCK TEST {num}</span>'
            f'<span class="qr">{len(ans)} answers</span></div>'
            f'<div style="height:5pt"></div><div class="card"><div class="ak-grid" style="--rows:{rows}">{cells}</div></div></div>')


ANS_PROBE_JS = """
<script>
(async function(){
  try { await document.fonts.ready; } catch(e) {}
  for (const el of document.querySelectorAll('.akey')) {
    const mb = parseFloat(getComputedStyle(el).marginBottom) || 0;
    el.setAttribute('data-h', ((el.getBoundingClientRect().height + mb) * 0.75).toFixed(2));
  }
  document.body.setAttribute('data-done', '1');
})();
</script>
"""

COL_W = 256.9  # (533.2 - 19.4 gap) / 2


def measure_answer_cards(tests):
    """Answer cards vary in height once answers wrap, so pack them by measured
    height instead of a fixed count per page -- a card that does not fit is
    silently clipped by the sheet's overflow, losing a whole key."""
    body = f'<div style="width:{COL_W}pt">' + "".join(
        answer_card(t, i) for i, t in enumerate(tests)) + "</div>"
    path = os.path.join(BUILD_DIR, "ans_measure.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(wrap(body) .replace("</body>", ANS_PROBE_JS + "</body>"))
    dom_path = os.path.join(BUILD_DIR, "ans_measure_dom.html")
    if os.path.exists(dom_path):
        os.remove(dom_path)
    with open(dom_path, "wb") as out:
        subprocess.run([EDGE_EXE, *BASE_FLAGS, "--window-size=794,1123",
                        "--virtual-time-budget=60000", "--dump-dom", furl(path)],
                       stdout=out, stderr=subprocess.DEVNULL)
    wait_for_output(dom_path, timeout=600)
    dom = open(dom_path, encoding="utf-8", errors="replace").read()
    if 'data-done="1"' not in dom:
        raise RuntimeError("answer-card measurement did not finish")
    heights = {}
    for m in re.finditer(r'<div class="akey"([^>]*)>', dom):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        if "data-i" in attrs and "data-h" in attrs:
            heights[int(attrs["data-i"])] = float(attrs["data-h"])
    if len(heights) != len(tests):
        raise RuntimeError(f"measured {len(heights)} of {len(tests)} answer cards")
    return [heights[i] for i in range(len(tests))]


def pack_answer_pages(heights, first_h, rest_h, cols=2):
    pages, i, n = [], 0, len(heights)
    while i < n:
        limit = first_h if not pages else rest_h
        page = []
        for _ in range(cols):
            col, used = [], 0.0
            while i < n and (not col or used + heights[i] <= limit):
                col.append(i)
                used += heights[i]
                i += 1
            page.append(col)
            if i >= n:
                break
        pages.append(page)
    return pages


def answer_sheets(tests, start_page, heights=None, label=f"{BOOK_TITLE} · Answer Keys"):
    head_h = 797.7 - 66
    body_h = 797.7 - 28.9
    if heights is None:                      # single-test key: always one page
        pages = [[[i], []] for i in range(len(tests))]
    else:
        pages = pack_answer_pages(heights, head_h, body_h)
    out = []
    for ci, page in enumerate(pages):
        top, head = 28.9, ""
        if ci == 0 and heights is not None:
            head = (f'<div class="cols" style="top:28.9pt;height:40pt;column-count:1">'
                    f'<div class="ph"><span class="pill">ANSWER KEYS</span><span class="qr">Mock Tests '
                    f'{tests[0].get("mock_number")}–{tests[-1].get("mock_number")}</span></div></div>')
            top = 66
        cols = page + [[]] * (2 - len(page))
        left = "".join(answer_card(tests[i]) for i in cols[0])
        right = "".join(answer_card(tests[i]) for i in cols[1])
        h = 797.7 - top
        aid = ' id="answers"' if ci == 0 and heights is not None else ""
        out.append(f"""
<section class="sheet"{aid}>
  <img class="stripe" src="{A['stripe']}">
  {head}
  <div class="cols" style="top:{top}pt;height:{h}pt">{left}<div class="colbreak"></div>{right}</div>
  {divider(top, h)}
  {footer(label, start_page + ci)}
</section>""")
    return out


def cover_sheet(tests):
    total_q = sum(len(extract_test_answers(t.get("mock_data", {}))) for t in tests)
    return f"""
<section class="sheet" id="cover">
  <img class="stripe" src="{A['stripe']}">
  <div class="cover-banner">
    <div class="cv-kicker">MULTILEVEL · CEFR</div>
    <img class="cv-hp" src="{A['hp_banner']}">
    <div class="cv-title">LISTENING</div>
    <div class="cv-sub">{len(tests)} Mock Tests · {total_q:,} questions</div>
    <div class="cv-line">6 parts per test · maps, forms, extracts &amp; sentence completion<br>Audio for every test: {AUDIO_LINK}</div>
    <div class="cv-chips"><span class="cv-chip">B1 · B2 · C1</span><span class="cv-chip">2 pages per test</span><span class="cv-chip">Full answer keys</span></div>
  </div>
  <div class="cv-body"><div class="cv-grid">
    <div class="card"><div class="cv-h">Part 1 · Part 2</div>Short replies (Q1–8) and form / note completion (Q9–14). Write ONE WORD and / or A NUMBER.</div>
    <div class="card"><div class="cv-h">Part 3 · Part 4</div>Match speakers to statements and label places on a map or plan.</div>
    <div class="card"><div class="cv-h">Part 5 · Part 6</div>Three extracts with two questions each, then complete a lecture summary.</div>
    <div class="card"><div class="cv-h">How to use</div>Each audio is played twice. Write your answers on the answer sheet and check them with the keys at the back.</div>
  </div></div>
  {footer(f"{BOOK_TITLE} · CEFR Listening", None)}
</section>"""


def toc_sheet(tests, page_map, ans_page, page_no):
    rows = ""
    for t in tests:
        n = t.get("mock_number")
        lvl = t.get("mock_data", {}).get("testInfo", {}).get("level") or ""
        rows += (f'<div class="toc-row"><a href="#test-{n}"><span class="tn">Mock Test {n}</span>'
                 f'<span class="tl">{esc(lvl)}</span><span class="dots"></span><span class="pg">{page_map[n]}</span></a></div>')
    rows += (f'<div class="toc-row"><a href="#answers"><span class="tn" style="color:#0c2a89">Answer Keys</span>'
             f'<span class="dots"></span><span class="pg">{ans_page}</span></a></div>')
    return f"""
<section class="sheet" id="contents">
  <img class="stripe" src="{A['stripe']}">
  <div class="cols" style="top:28.9pt;height:40pt;column-count:1">
    <div class="ph"><span class="pill">CONTENTS</span><span class="qr">{len(tests)} mock tests</span></div>
  </div>
  <div class="cols" style="top:66pt;height:731.7pt">{rows}</div>
  {divider(66, 731.7)}
  {footer(f"{BOOK_TITLE} · Contents", page_no)}
</section>"""


def wrap(body, script=False):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>CEFR Listening Mock Tests</title>'
            f'<style>{CSS}</style></head><body>{body}{FIT_JS if script else ""}</body></html>')


# --------------------------------------------------------------------------- #
# Rendering helpers
# --------------------------------------------------------------------------- #
# Without a private --user-data-dir, Edge hands the command to an already
# running instance and exits at once, so subprocess.run returns before the PDF
# exists and we would read a stale file from the previous build. The directory
# is per-process so two builders running at once cannot block each other.
PROFILE_DIR = tempfile.mkdtemp(prefix="edge-profile-")
atexit.register(shutil.rmtree, PROFILE_DIR, True)

BASE_FLAGS = [
    "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
    "--no-first-run", "--no-default-browser-check", "--disable-extensions",
    f"--user-data-dir={PROFILE_DIR}",
]


def wait_for_output(path, timeout=600):
    """msedge.exe is a GUI binary that hands the work to a detached child, so
    subprocess.run returns long before the file is finished. Poll until it
    exists and its size has stopped growing."""
    deadline = time.time() + timeout
    last, stable = -1, 0
    while time.time() < deadline:
        size = os.path.getsize(path) if os.path.exists(path) else -1
        stable = stable + 1 if size > 0 and size == last else 0
        if stable >= 3:
            return size
        last = size
        time.sleep(0.25)
    raise RuntimeError(f"Edge did not finish writing {path}")


def run_edge(extra, out_path):
    if os.path.exists(out_path):
        os.remove(out_path)
    subprocess.run([EDGE_EXE, *BASE_FLAGS, *extra],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wait_for_output(out_path)


def edge_pdf(html_path, pdf_path):
    run_edge(["--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
              "--virtual-time-budget=20000", f"--print-to-pdf={pdf_path}", furl(html_path)],
             pdf_path)


def measure_fit(tests):
    """Lay out every test page in Edge, shrink pages that overflow, return {(num, idx): (k, maph)}."""
    body = "".join(test_sheets(t, 0, 0, anchor=False) for t in tests)
    path = os.path.join(BUILD_DIR, "fit_probe.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(wrap(body, script=True))
    dom_path = os.path.join(BUILD_DIR, "fit_probe_dom.html")
    if os.path.exists(dom_path):
        os.remove(dom_path)
    with open(dom_path, "wb") as out:
        subprocess.run([EDGE_EXE, *BASE_FLAGS, "--window-size=794,1123",
                        "--virtual-time-budget=120000", "--dump-dom", furl(path)],
                       stdout=out, stderr=subprocess.DEVNULL)
    wait_for_output(dom_path, timeout=900)
    with open(dom_path, encoding="utf-8", errors="replace") as f:
        dom = f.read()
    if 'data-done="1"' not in dom:
        raise RuntimeError("fit probe did not finish; page sizes would be wrong")
    fit = {}
    for m in re.finditer(r'<section class="sheet"([^>]*)>', dom):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        if "data-k" not in attrs:
            continue
        key = (int(attrs["data-test"]), int(attrs["data-idx"]))
        k, maph, ok = float(attrs["data-k"]), float(attrs["data-maph"]), attrs.get("data-ok") == "1"
        if k < 1 or maph < 277:
            fit[key] = (k, maph)
        if not ok:
            print(f"  ! Mock {key[0]} page {key[1]} still overflows at k={k}")
    return fit


def load_tests():
    tests = []
    for fn in sorted(glob.glob(os.path.join(CEFR_DIR, "*.json"))):
        with open(fn, encoding="utf-8") as f:
            tests.append(json.load(f))
    tests.sort(key=lambda x: x.get("mock_number", 0))
    return tests


def main():
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(PDF_OUT_DIR, exist_ok=True)
    tests = load_tests()
    only = [int(a) for a in sys.argv[1:] if a.isdigit()]
    if only:
        tests = [t for t in tests if t.get("mock_number") in only]
    print(f"Loaded {len(tests)} tests")

    print("Measuring page fit...")
    fit = measure_fit(tests)
    for (n, i), (k, mh) in sorted(fit.items()):
        print(f"  Mock {n} p{i}: scale {k:.2f}, map max-height {mh:.0f}pt")

    print("Measuring answer cards...")
    ans_heights = measure_answer_cards(tests)

    # ---------------- master book ----------------
    first_test_page = 3
    page_map = {t.get("mock_number"): first_test_page + 2 * i for i, t in enumerate(tests)}
    ans_page = first_test_page + 2 * len(tests)
    sheets = [cover_sheet(tests), toc_sheet(tests, page_map, ans_page, 2)]
    for t in tests:
        p1 = page_map[t.get("mock_number")]
        sheets.append(test_sheets(t, p1, p1 + 1, fit))
    sheets += answer_sheets(tests, ans_page, ans_heights)
    book_html = os.path.join(BUILD_DIR, "cefr_listening_book.html")
    with open(book_html, "w", encoding="utf-8") as f:
        f.write(wrap("".join(sheets)))
    suffix = "" if not only else "_subset"
    raw_pdf = os.path.join(BUILD_DIR, "book_raw.pdf")
    out_pdf = os.path.join(ROOT_DIR, f"CEFR_Listening_Mock_Test_Book{suffix}.pdf")
    print("Rendering master book...")
    edge_pdf(book_html, raw_pdf)
    doc = pymupdf.open(raw_pdf)
    toc = [[1, "Cover", 1], [1, "Contents", 2]]
    for t in tests:
        n = t.get("mock_number")
        toc.append([1, f"Mock Test {n}", page_map[n]])
    toc.append([1, "Answer Keys", ans_page])
    doc.set_toc(toc)
    doc.set_metadata({"title": "CEFR Listening Mock Tests", "author": BOOK_TITLE, "subject": "CEFR Listening"})
    doc.save(out_pdf, garbage=3, deflate=True)
    print(f"Master book: {out_pdf} ({doc.page_count} pages)")
    doc.close()

    # ---------------- individual PDFs ----------------
    if "--no-single" in sys.argv:
        return
    print("Rendering individual test PDFs...")
    for t in tests:
        n = t.get("mock_number")
        title_safe = re.sub(r'[\\/:*?"<>|]+', "-", t.get("title", f"Test {n}")).strip()
        body = test_sheets(t, 1, 2, fit, anchor=False) + "".join(
            answer_sheets([t], 3, label=f"{BOOK_TITLE} · Mock Test {n} · Answer Key"))
        hp = os.path.join(BUILD_DIR, f"single_{n}.html")
        with open(hp, "w", encoding="utf-8") as f:
            f.write(wrap(body))
        pdf = os.path.join(PDF_OUT_DIR, f"{str(n).zfill(3)}-{title_safe}.pdf")
        edge_pdf(hp, pdf)
        print(f"  {os.path.basename(pdf)}")


if __name__ == "__main__":
    main()
