"""
Front/back covers for the CEFR Listening and Reading mock test books.

Reproduces the Cover_front_back.pdf design (A3 portrait, 841.92 x 1191.12pt).
That reference is almost entirely vector with Type3 subset fonts, which cannot
be re-typeset, so the parts that never change -- the masthead band with the 3D
hero, the corner ornament and the back's contact band with its QR -- are
cropped from it at 4x and reused as artwork. Everything that differs per book
is typeset here.

Text geometry below is measured from the reference's own spans.

Outputs:
  * CEFR_Listening_Cover.pdf
  * CEFR_Reading_Cover.pdf
"""
import os
import sys

import pymupdf

import build_cefr_book as L

ROOT = L.ROOT_DIR
ART = os.path.join(ROOT, "cover_assets")
BUILD = os.path.join(ROOT, "_build_covers")
REF = os.path.join(ROOT, "Cover_front_back.pdf")

PAGE_W, PAGE_H = 841.92, 1191.12
MARGIN_X = 68.0

furl = L.furl
esc = L.esc


def art(name):
    return furl(os.path.join(ART, name))


# --------------------------------------------------------------------------- #
# Artwork: crop the parts of the reference that are the same on every cover
# --------------------------------------------------------------------------- #
CROPS = {
    "front_top.png": (0, (0, 0, PAGE_W, 732)),        # logo, pill, band, hero
    "front_orn.png": (0, (540, 960, PAGE_W, PAGE_H)),  # faint corner ornament
    "back_band.png": (1, (0, 838, PAGE_W, PAGE_H)),    # contact band + QR
}


# the centred logo mark is an embedded image with an alpha channel; cropping it
# would bake in the reference page's own background gradient
LOGO_XREF = 35
LOGO_FILE = "logo_mark_alpha.png"


def ensure_artwork(scale=4):
    os.makedirs(ART, exist_ok=True)
    missing = [n for n in CROPS if not os.path.exists(os.path.join(ART, n))]
    need_logo = not os.path.exists(os.path.join(ART, LOGO_FILE))
    if not missing and not need_logo:
        return
    ref = pymupdf.open(REF)
    if need_logo:
        info = ref.extract_image(LOGO_XREF)
        pix = pymupdf.Pixmap(ref, LOGO_XREF)
        if info.get("smask"):
            pix = pymupdf.Pixmap(pix, pymupdf.Pixmap(ref, info["smask"]))
        pix.save(os.path.join(ART, LOGO_FILE))
        print(f"  extracted {LOGO_FILE} ({pix.width}x{pix.height}, alpha)")
    for name in missing:
        page, rect = CROPS[name]
        pix = ref[page].get_pixmap(matrix=pymupdf.Matrix(scale, scale),
                                   clip=pymupdf.Rect(*rect))
        pix.save(os.path.join(ART, name))
        print(f"  cropped {name} ({pix.width}x{pix.height})")
    ref.close()


# --------------------------------------------------------------------------- #
# CSS
# --------------------------------------------------------------------------- #
CSS = f"""
@font-face {{ font-family: 'Syne'; src: url('{furl(os.path.join(L.FONTS, 'Syne.ttf'))}'); font-weight: 400 800; }}
@font-face {{ font-family: 'Open Sans'; src: url('{furl(os.path.join(L.FONTS, 'OpenSans.ttf'))}'); font-weight: 300 800; }}

@page {{ size: {PAGE_W}pt {PAGE_H}pt; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{ font-family: 'Open Sans', sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}

.page {{
  position: relative; width: {PAGE_W}pt; height: {PAGE_H}pt; overflow: hidden;
  background: linear-gradient(#f6f7fa 0%, #f0f2f7 64%, #ecEFF5 100%);
  page-break-after: always; break-after: page;
}}
.page:last-child {{ page-break-after: auto; break-after: auto; }}
img {{ display: block; }}

/* ---------- front ---------- */
.band {{ position: absolute; left: 0; top: 0; width: {PAGE_W}pt; }}
.orn {{ position: absolute; right: 0; bottom: 0; width: {PAGE_W - 540}pt; }}
.kicker {{
  position: absolute; left: {MARGIN_X}pt; top: 758pt;
  font-family: 'Syne'; font-weight: 600; font-size: 24pt; line-height: 30pt; color: #7ea0f5;
}}
.title {{
  position: absolute; left: {MARGIN_X}pt; top: 782pt;
  font-family: 'Syne'; font-weight: 800; font-size: 74pt; line-height: 84pt; color: #1a3fc4;
  letter-spacing: -1pt; white-space: nowrap;
}}
.sub {{
  position: absolute; left: {MARGIN_X}pt; top: 884pt;
  font-size: 17pt; line-height: 23pt; color: #5c6a8e;
}}
.sub b {{ font-weight: 700; color: #0b1a4a; }}
.feat {{
  position: absolute; left: {MARGIN_X}pt; top: 928pt;
  font-size: 13pt; line-height: 18pt; color: #1a3fc4; font-weight: 600;
}}

/* ---------- back ---------- */
.bhead {{
  position: absolute; left: 0; top: 126pt; width: {PAGE_W}pt; text-align: center;
  font-family: 'Syne'; font-weight: 600; font-size: 20pt; line-height: 26pt; color: #2f5bea;
}}
.mark {{ position: absolute; left: 279pt; top: 215pt; width: 283.5pt; }}
.blurb {{
  position: absolute; left: 128pt; top: 654pt; width: {PAGE_W - 256}pt; text-align: center;
  font-size: 12.5pt; line-height: 20.3pt; color: #4a5675;
}}
.blurb b {{ color: #1a3fc4; font-weight: 700; }}
.bband {{ position: absolute; left: 0; bottom: 0; width: {PAGE_W}pt; }}
"""


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
def front(spec):
    return f"""
<section class="page">
  <img class="band" src="{art('front_top.png')}">
  <img class="orn" src="{art('front_orn.png')}">
  <div class="kicker">Milliy sertifikat · CEFR</div>
  <div class="title">{esc(spec['title'])}</div>
  <div class="sub">{esc(spec['sub_lead'])} <b>{esc(spec['sub_bold'])}</b></div>
  <div class="feat">{esc(spec['features'])}</div>
</section>"""


def back(spec):
    return f"""
<section class="page">
  <div class="bhead">{esc(spec['back_head'])}</div>
  <img class="mark" src="{art(LOGO_FILE)}">
  <div class="blurb">{spec['blurb']}</div>
  <img class="bband" src="{art('back_band.png')}">
</section>"""


def wrap(body):
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f'<title>Cover</title><style>{CSS}</style></head><body>{body}</body></html>')


# --------------------------------------------------------------------------- #
# Specs
# --------------------------------------------------------------------------- #
def count_tests(folder):
    import glob
    return len(glob.glob(os.path.join(ROOT, folder, "*.json")))


def specs():
    n_listen = count_tests("cefr-listening")
    n_read = count_tests("cefr-reading")
    return {
        "Listening": {
            "title": "LISTENING",
            "sub_lead": "Multilevel Mock Tests:",
            "sub_bold": f"{n_listen} full tests",
            "features": "6 parts per test · Audio · Answer key",
            "back_head": "Multilevel · Listening Mock Tests",
            "blurb": (f"{n_listen} full-length Multilevel <b>(CEFR)</b> listening tests in the real exam "
                      "format — all six parts, from short replies and form completion to maps, "
                      "extracts and sentence completion, with a complete answer key and the audio "
                      "for every test on our Telegram channel."),
            "out": "CEFR_Listening_Cover.pdf",
        },
        "Reading": {
            "title": "READING",
            "sub_lead": "Multilevel Mock Tests:",
            "sub_bold": f"{n_read} full tests",
            "features": "5 parts per test · Full passages · Answer key",
            "back_head": "Multilevel · Reading Mock Tests",
            "blurb": (f"{n_read} full-length Multilevel <b>(CEFR)</b> reading tests in the real exam "
                      "format — all five parts, from gap-fill and text matching to paragraph "
                      "headings and long-text comprehension, with every passage in full and a "
                      "complete answer key at the back."),
            "out": "CEFR_Reading_Cover.pdf",
        },
    }


def main():
    os.makedirs(BUILD, exist_ok=True)
    print("Preparing cover artwork...")
    ensure_artwork()

    wanted = [a for a in sys.argv[1:] if not a.startswith("-")]
    for name, spec in specs().items():
        if wanted and name.lower() not in [w.lower() for w in wanted]:
            continue
        html = wrap(front(spec) + back(spec))
        path = os.path.join(BUILD, f"cover_{name.lower()}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        raw = os.path.join(BUILD, f"cover_{name.lower()}.pdf")
        L.edge_pdf(path, raw)
        doc = pymupdf.open(raw)
        doc.set_metadata({"title": f"CEFR {name} Mock Tests — Cover",
                          "author": L.BOOK_TITLE, "subject": f"CEFR {name}"})
        out = os.path.join(ROOT, spec["out"])
        doc.save(out, garbage=3, deflate=True)
        print(f"  {spec['out']} ({doc.page_count} pages, "
              f"{doc[0].rect.width:.0f}x{doc[0].rect.height:.0f}pt)")
        doc.close()


if __name__ == "__main__":
    main()
