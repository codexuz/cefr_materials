"""Verify the article book: structure, chrome, and that nothing was dropped."""
import os
import re
import sys

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_article_book as A  # noqa: E402

BOOK = os.path.join(A.ROOT, "CEFR_Article_Book.pdf")
TOL = 0.8

fails, notes = [], []


def check(ok, msg):
    (notes if ok else fails).append(("PASS" if ok else "FAIL") + "  " + msg)


def near(c, t, tol=0.03):
    return c is not None and all(abs(a - b) < tol for a, b in zip(c, t))


C9, BLUE = (0.788, 0.839, 0.961), (0.122, 0.282, 0.839)


def main():
    arts = A.load_articles(A.DEFAULT_COUNT)
    doc = pymupdf.open(BOOK)
    toc = doc.get_toc()

    check(len(arts) == 10, f"{len(arts)} articles loaded")
    check(len(toc) == len(arts) + 2, f"bookmarks: {len(toc)} (cover + contents + {len(arts)})")
    check({(round(p.rect.width), round(p.rect.height)) for p in doc} == {(595, 842)},
          "every page is A4")

    starts = [e[2] for e in toc[2:]]
    check(starts == sorted(starts) and starts[0] == 3,
          f"articles start in order from page {starts[0]}")

    # --- each bookmark lands on that article's opener -----------------------
    bad_open = []
    for i, p in enumerate(starts, 1):
        tight = re.sub(r"\s+", "", doc[p - 1].get_text()).upper()
        if f"ARTICLE{i:02d}" not in tight:
            bad_open.append(i)
    check(not bad_open, f"every bookmark lands on its opener ({len(bad_open)} wrong)")

    # --- opener carries the photograph --------------------------------------
    no_photo = [i for i, p in enumerate(starts, 1)
                if not any(b["width"] > 400 and b["height"] > 300
                           for b in doc[p - 1].get_image_info())]
    check(not no_photo, f"every opener carries its photo ({len(no_photo)} missing)")

    # --- chrome on every page but the cover ---------------------------------
    bad_rule = bad_pill = bad_stripe = 0
    for i in range(1, doc.page_count):
        pg = doc[i]
        rule = [g["rect"] for g in pg.get_drawings()
                if near(g.get("fill"), C9) and g["rect"].width > 400]
        pill = [g["rect"] for g in pg.get_drawings()
                if near(g.get("fill"), BLUE) and g["rect"].x1 > 560 and 9 < g["rect"].height < 12]
        if not rule or abs(rule[0].y0 - 803.64) > TOL:
            bad_rule += 1
        if not pill or abs(pill[0].y0 - 809.68) > TOL:
            bad_pill += 1
        if not any(b["width"] == 4956 for b in pg.get_image_info()):
            bad_stripe += 1
    check(bad_rule == 0, f"footer rule on every body page ({bad_rule} missing)")
    check(bad_pill == 0, f"page pill on every body page ({bad_pill} missing)")
    check(bad_stripe == 0, f"top stripe on every body page ({bad_stripe} missing)")

    # --- content completeness ------------------------------------------------
    ranges = []
    for i, p in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else doc.page_count + 1
        ranges.append((p, end))

    missing_lv, missing_vocab, missing_tr, missing_terms = [], [], [], []
    for idx, (art, (p0, p1)) in enumerate(zip(arts, ranges), 1):
        text = re.sub(r"\s+", " ", "\n".join(doc[i - 1].get_text() for i in range(p0, p1)))
        tight = re.sub(r"\s+", "", text)
        for lv, name in A.LEVELS:
            if name.upper() not in text.upper():
                missing_lv.append(f"{idx}.{lv}")
            # a sample of each level's vocabulary must be printed
            words = list(A.vocab(art, lv))
            if not words:
                continue
            for w in words[:3]:
                if re.sub(r"\s+", "", w).lower() not in tight.lower():
                    missing_vocab.append(f"{idx}.{lv}.{w}")
        if A.translation(art, "B1") and "TARJIMA" not in text.upper():
            missing_tr.append(str(idx))
        # a sample from each passage must appear -- taken from the middle,
        # since the floated drop cap extracts away from the first word
        for lv, _ in A.LEVELS:
            body = A.plain(A.passage(art, lv))
            sample = body[120:190]
            if sample and re.sub(r"\s+", "", sample).lower() not in tight.lower():
                missing_terms.append(f"{idx}.{lv}")

    check(not missing_lv, f"all three levels on every article ({len(missing_lv)} missing)")
    check(not missing_terms,
          f"every passage printed ({len(missing_terms)} missing){'' if not missing_terms else ': ' + str(missing_terms[:5])}")
    check(not missing_vocab,
          f"vocabulary printed for every level ({len(missing_vocab)} missing){'' if not missing_vocab else ': ' + str(missing_vocab[:5])}")
    check(not missing_tr, f"Uzbek translation on every article ({len(missing_tr)} missing)")

    # --- nothing crosses the column gutter -----------------------------------
    strays = []
    for p0, p1 in ranges:
        for i in range(p0, p1):
            for b in doc[i - 1].get_text("blocks"):
                if b[3] > 800:
                    continue
                if not ((b[0] >= 31.0 and b[2] <= 289.5) or (b[0] >= 307.0 and b[2] <= 565.5)):
                    # the opener blocks legitimately span both columns
                    if b[1] > 420:
                        strays.append((i, round(b[0], 1), round(b[2], 1)))
    check(not strays, f"body text stays inside its column ({len(strays)} blocks)")

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
