"""Verify the built book against demo_book.pdf's measured layout."""
import glob
import os
import re
import sys

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cefr_book as B

ROOT = B.ROOT_DIR
BOOK = os.path.join(ROOT, "CEFR_Listening_Mock_Test_Book.pdf")
DEMO = os.path.join(ROOT, "demo_book.pdf")
TOL = 0.6  # Chrome snaps to a 0.75pt grid, so allow sub-point drift

fails, notes = [], []


def check(ok, msg):
    (notes if ok else fails).append(("PASS" if ok else "FAIL") + "  " + msg)


def near(c, t, tol=0.02):
    return c is not None and all(abs(a - b) < tol for a, b in zip(c, t))


C9, BLUE = (0.788, 0.839, 0.961), (0.122, 0.282, 0.839)


def chrome(page):
    """Measured structural elements of one page."""
    out = {"dashes": [], "pill": None, "rule": None, "pagepill": None}
    for g in page.get_drawings():
        r, f = g["rect"], g.get("fill")
        if near(f, C9):
            if r.width < 2 and r.height < 4:
                out["dashes"].append(r)
            elif r.width > 400:
                out["rule"] = r
        elif near(f, BLUE):
            if 50 < r.width < 70 and 16 < r.height < 20 and r.x0 < 40:
                out["pill"] = r
            elif r.width < 25 and 9 < r.height < 12 and r.x0 > 500:
                out["pagepill"] = r
    return out


def main():
    tests = B.load_tests()
    demo = chrome(pymupdf.open(DEMO)[0])

    doc = pymupdf.open(BOOK)
    # attach_covers.py optionally wraps the book in its A3 covers, scaled to A4
    toc0 = doc.get_toc()
    covers = bool(toc0) and toc0[0][1] == "Front cover"
    lead = 2 + (1 if covers else 0)      # front cover, overview, contents
    tail = 1 if covers else 0            # back cover
    n_ans = doc.page_count - lead - tail - 2 * len(tests)
    check(doc.page_count == lead + tail + 2 * len(tests) + n_ans,
          f"page count {doc.page_count} = {'2 covers + ' if covers else ''}"
          f"cover+contents + {len(tests)}x2 + {n_ans} answer pages")
    check(len(toc0) == len(tests) + 3 + (2 if covers else 0), f"bookmarks: {len(toc0)}")
    if covers:
        check({(round(p.rect.width), round(p.rect.height)) for p in doc} == {(595, 842)},
              "every page, covers included, is A4")

    # --- chrome parity on every test page -------------------------------
    bad_dash = bad_rule = bad_pill = raster = 0
    for i in range(lead, lead + 2 * len(tests)):
        pg = doc[i]
        c = chrome(pg)
        first = (i - lead) % 2 == 0
        want_n, want_top = (181, 118.3) if first else (205, 28.9)
        if len(c["dashes"]) != want_n:
            bad_dash += 1
        else:
            ys = sorted(d.y0 for d in c["dashes"])
            per = (ys[-1] - ys[0]) / (len(ys) - 1)
            if abs(per - B.DASH_PERIOD) > 0.05 or abs(ys[0] - want_top) > TOL:
                bad_dash += 1
        if not c["rule"] or abs(c["rule"].x0 - demo["rule"].x0) > TOL or abs(c["rule"].y0 - demo["rule"].y0) > TOL:
            bad_rule += 1
        if first and (not c["pill"] or abs(c["pill"].y0 - demo["pill"].y0) > TOL
                      or abs(c["pill"].height - demo["pill"].height) > TOL):
            bad_pill += 1
        if any(295 < b["bbox"][0] < 302 for b in pg.get_image_info()):
            raster += 1
    check(bad_dash == 0, f"divider: vector dashes at demo rhythm on all {2 * len(tests)} test pages ({bad_dash} bad)")
    check(raster == 0, f"divider is never a rasterised image ({raster} pages)")
    check(bad_rule == 0, f"footer rule matches demo x/y on all test pages ({bad_rule} bad)")
    check(bad_pill == 0, f"PART pill matches demo y/height on all page-1s ({bad_pill} bad)")

    # --- divider geometry vs demo, exactly ------------------------------
    d0, g0 = demo["dashes"], chrome(doc[2])["dashes"]
    if d0 and g0:
        dd, gg = sorted(d.y0 for d in d0), sorted(d.y0 for d in g0)
        check(len(dd) == len(gg), f"divider dash count demo={len(dd)} book={len(gg)}")
        check(abs(d0[0].width - g0[0].width) <= TOL,
              f"dash width demo={d0[0].width:.2f} book={g0[0].width:.2f}")
        check(abs(d0[0].height - g0[0].height) <= TOL,
              f"dash length demo={d0[0].height:.2f} book={g0[0].height:.2f}")

    # --- answer keys complete and untruncated ---------------------------
    ans_text = re.sub(r"\s+", " ", "\n".join(
        doc[i].get_text()
        for i in range(lead + 2 * len(tests), doc.page_count - (1 if covers else 0))))
    missing = []
    for t in tests:
        num = t.get("mock_number")
        if f"MOCK TEST {num}" not in ans_text:
            missing.append(f"card {num}")
            continue
        for q, v in B.extract_test_answers(t.get("mock_data", {})).items():
            first = re.sub(r"\s+", " ", v.split(" / ")[0]).strip()
            if first and first not in ans_text:
                missing.append(f"{num}.q{q}")
    check(not missing, f"every answer printed in full ({len(missing)} missing){'' if not missing else ': ' + str(missing[:6])}")
    check("…" not in ans_text and "..." not in ans_text.replace("....", ""),
          "no ellipsis truncation in answer keys")

    # --- test content present -------------------------------------------
    book_text = re.sub(r"\s+", " ", "\n".join(
        doc[i].get_text() for i in range(lead, lead + 2 * len(tests))))
    # The banner is letter-spaced, so it extracts as "M O C K T E S T 1";
    # compare with all whitespace removed.
    tight = re.sub(r"\s+", "", book_text)
    gaps = [t.get("mock_number") for t in tests
            if f"MOCKTEST{t.get('mock_number')}LISTENING" not in tight]
    check(not gaps, f"every test's banner present ({len(gaps)} missing)")
    for p in range(1, 7):
        c = book_text.count(f"PART {p}")
        check(c >= len(tests), f"PART {p} appears {c}x (>= {len(tests)})")

    # --- individual PDFs --------------------------------------------------
    pdfs = sorted(glob.glob(os.path.join(B.PDF_OUT_DIR, "*.pdf")))
    check(len(pdfs) == len(tests), f"{len(pdfs)} individual test PDFs")
    wrong = [os.path.basename(p) for p in pdfs if pymupdf.open(p).page_count != 3]
    check(not wrong, f"each individual PDF is 3 pages ({len(wrong)} wrong)")

    print("\n".join(notes))
    print()
    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} CHECK(S) FAILED")
        return 1
    print(f"ALL {len(notes)} CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
