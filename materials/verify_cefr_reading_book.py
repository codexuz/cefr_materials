"""Verify the Reading book against demo_book.pdf's measured Reading layout."""
import glob
import os
import re
import sys

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cefr_reading_book as R  # noqa: E402
import build_cefr_book as L  # noqa: E402

BOOK = os.path.join(R.ROOT_DIR, "CEFR_Reading_Mock_Test_Book.pdf")
DEMO = os.path.join(R.ROOT_DIR, "demo_book.pdf")
DEMO_P1 = 2          # demo page 3 == Reading page 1 of Mock Test 1
TOL = 0.8

fails, notes = [], []


def check(ok, msg):
    (notes if ok else fails).append(("PASS" if ok else "FAIL") + "  " + msg)


def near(c, t, tol=0.03):
    return c is not None and all(abs(a - b) < tol for a, b in zip(c, t))


C9, BLUE = (0.788, 0.839, 0.961), (0.122, 0.282, 0.839)


def chrome(page):
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
            # the pill grows leftwards for 3-digit page numbers, so match on
            # its right edge and height, not its width
            elif r.x1 > 560 and 9 < r.height < 12 and r.x0 > 500:
                out["pagepill"] = r
    return out


def demo_divider(page):
    for g in page.get_drawings():
        r = g["rect"]
        if near(g.get("fill"), C9) and r.width < 2 and r.height > 100:
            tops = sorted({round(i[1].y, 3) for i in g["items"]
                           if i[0] == "l" and abs(i[1].x - r.x1) < 0.01 and i[2].y > i[1].y})
            return r, tops
    return None, []


def main():
    tests = R.load_tests()
    demo = pymupdf.open(DEMO)
    dchrome = chrome(demo[DEMO_P1])
    drect, dtops = demo_divider(demo[DEMO_P1])

    doc = pymupdf.open(BOOK)
    nums = [t.get("mock_number") for t in tests]

    # ---- page map, rebuilt the same way the builder does -------------------
    toc = doc.get_toc()
    # attach_covers.py optionally wraps the book in its A3 covers, scaled to A4
    covers = bool(toc) and toc[0][1] == "Front cover"
    extra = 2 if covers else 0
    check(len(toc) == len(tests) + 3 + extra,
          f"bookmarks: {len(toc)} ({'covers + ' if covers else ''}cover + contents "
          f"+ {len(tests)} + keys)")
    if covers:
        check({(round(p.rect.width), round(p.rect.height)) for p in doc} == {(595, 842)},
              "every page, covers included, is A4")
    starts = {e[1]: e[2] for e in toc if e[1].startswith("Mock Test ")}
    ans_page = [e[2] for e in toc if e[1] == "Answer Keys"][0]

    # page ranges per test
    ordered = sorted(((starts[f"Mock Test {n}"], n) for n in nums))
    ranges = []
    for i, (p0, n) in enumerate(ordered):
        p1 = ordered[i + 1][0] if i + 1 < len(ordered) else ans_page
        ranges.append((n, p0, p1))
    check(all(p1 > p0 for _, p0, p1 in ranges), "every test occupies at least one page")
    check(ordered[0][0] == 3 + (1 if covers else 0),
          f"first test starts on page {ordered[0][0]}")

    # ---- chrome parity on every test page ----------------------------------
    bad_dash = bad_rule = bad_pill = bad_banner = 0
    first_pages = set()
    for n, p0, p1 in ranges:
        first_pages.add(p0)
        for pno in range(p0, p1):
            pg = doc[pno - 1]
            c = chrome(pg)
            is_first = pno == p0
            want_top = R.BANNER_TOP if is_first else R.BODY_TOP
            want_n = round((R.PAGE_H - R.MARGIN_B - want_top - L.DASH_LEN) / L.DASH_PERIOD) + 1
            if len(c["dashes"]) != want_n:
                bad_dash += 1
            else:
                ys = sorted(d.y0 for d in c["dashes"])
                per = (ys[-1] - ys[0]) / (len(ys) - 1)
                if abs(per - L.DASH_PERIOD) > 0.05 or abs(ys[0] - want_top) > TOL:
                    bad_dash += 1
            if not c["rule"] or abs(c["rule"].x0 - dchrome["rule"].x0) > TOL \
                    or abs(c["rule"].y0 - dchrome["rule"].y0) > TOL:
                bad_rule += 1
            if not c["pagepill"] or abs(c["pagepill"].y0 - dchrome["pagepill"].y0) > TOL \
                    or abs(c["pagepill"].x1 - dchrome["pagepill"].x1) > TOL:
                bad_pill += 1
            if is_first:
                imgs = pg.get_image_info()
                has_banner = any(w["width"] == 4435 for w in imgs)
                has_book = any(w["width"] == 219 for w in imgs)
                tight = re.sub(r"\s+", "", pg.get_text())
                if not (has_banner and has_book and f"MOCKTEST{n}READING" in tight):
                    bad_banner += 1
    total_pages = sum(p1 - p0 for _, p0, p1 in ranges)
    check(bad_dash == 0, f"divider at demo rhythm on all {total_pages} test pages ({bad_dash} bad)")
    check(bad_rule == 0, f"footer rule matches demo on all test pages ({bad_rule} bad)")
    check(bad_pill == 0, f"page pill matches demo on all test pages ({bad_pill} bad)")
    check(bad_banner == 0, f"banner + book icon on every test's first page ({bad_banner} bad)")

    # ---- divider vs demo, exactly ------------------------------------------
    # first page of the first test, wherever the covers have pushed it to
    g0 = sorted(chrome(doc[ordered[0][0] - 1])["dashes"], key=lambda r: r.y0)
    check(len(g0) == len(dtops), f"divider dash count demo={len(dtops)} book={len(g0)}")
    if g0 and drect:
        check(abs(g0[0].width - drect.width) <= TOL,
              f"dash width demo={drect.width:.2f} book={g0[0].width:.2f}")
        check(abs(g0[0].y0 - dtops[0]) <= TOL,
              f"divider top demo={dtops[0]:.2f} book={g0[0].y0:.2f}")

    # ---- nothing crosses the gutter between the demo's two columns ---------
    # left column 31.6..288.5, right column 307.9..564.8 (indented and centred
    # blocks start further in, so only the column bands are asserted)
    strays = []
    for n, p0, p1 in ranges:
        for pno in range(p0, p1):
            for b in doc[pno - 1].get_text("blocks"):
                if b[3] > 800:
                    continue
                in_left = b[0] >= 31.0 and b[2] <= 289.5
                in_right = b[0] >= 307.0 and b[2] <= 565.5
                if not (in_left or in_right):
                    strays.append((n, pno, round(b[0], 1), round(b[2], 1)))
    check(not strays, f"no text crosses the column gutter ({len(strays)} blocks){'' if not strays else ': ' + str(strays[:4])}")

    # ---- content completeness ----------------------------------------------
    missing_parts, missing_q = [], []
    for n, p0, p1 in ranges:
        text = re.sub(r"\s+", " ", "\n".join(doc[i - 1].get_text() for i in range(p0, p1)))
        for p in range(1, 6):
            if f"PART {p}" not in text:
                missing_parts.append(f"{n}.P{p}")
    check(not missing_parts, f"all 5 parts on every test ({len(missing_parts)} missing)")

    # ---- answer keys --------------------------------------------------------
    ans_text = re.sub(r"\s+", " ", "\n".join(doc[i].get_text()
                                             for i in range(ans_page - 1,
                                                            doc.page_count - (1 if covers else 0))))
    miss = []
    for t in tests:
        n = t.get("mock_number")
        if f"MOCK TEST {n}" not in ans_text:
            miss.append(f"card {n}")
            continue
        for q, v in R.test_answers(t.get("mock_data", {})).items():
            first = re.sub(r"\s+", " ", v.split(" / ")[0]).strip()
            if first and first not in ans_text:
                miss.append(f"{n}.q{q}")
    check(not miss, f"every answer printed in full ({len(miss)} missing){'' if not miss else ': ' + str(miss[:6])}")
    check("…" not in ans_text, "no ellipsis truncation in answer keys")

    # ---- individual PDFs ----------------------------------------------------
    pdfs = sorted(glob.glob(os.path.join(R.PDF_OUT_DIR, "*.pdf")))
    check(len(pdfs) == len(tests), f"{len(pdfs)} individual test PDFs")
    short = [os.path.basename(p) for p in pdfs if pymupdf.open(p).page_count < 2]
    check(not short, f"every individual PDF has its test pages + key ({len(short)} too short)")

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
