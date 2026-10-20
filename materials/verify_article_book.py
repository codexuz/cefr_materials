"""Verify the B2 article book: structure, content, glossary and palette."""
import os
import re
import sys

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_article_book as A  # noqa: E402

BOOK = os.path.join(A.ROOT, "CEFR_Article_Book.pdf")

fails, notes = [], []


def check(ok, msg):
    (notes if ok else fails).append(("PASS" if ok else "FAIL") + "  " + msg)


def tight(s):
    return re.sub(r"\s+", "", s).lower()


def hexcol(rgb):
    return "#%02X%02X%02X" % tuple(round(c * 255) for c in rgb[:3])


def main():
    arts = A.load_articles(A.DEFAULT_COUNT)
    doc = pymupdf.open(BOOK)
    toc = doc.get_toc()
    n = len(arts)

    per = A.PAGES_PER_ARTICLE
    check(n == A.DEFAULT_COUNT, f"{n} articles loaded")
    check(doc.page_count == 2 + per * n + 1,
          f"{doc.page_count} pages = cover + contents + {n} x {per} + back cover")
    check(len(toc) == 2 + 2 * n + 1, f"bookmarks: {len(toc)}")
    check({(round(p.rect.width), round(p.rect.height)) for p in doc} == {(595, 842)}, "every page is A4")

    openers = [e[2] for e in toc if e[0] == 1 and re.match(r"\d\d ", e[1])]
    check(openers == [3 + per * i for i in range(n)], f"articles open every {per} pages from page 3")

    # --- speaking and essay questions after every article -------------------
    questions, _ = A.load_questions(arts)
    missing_q = []
    for i, p in enumerate(openers, 1):
        qtext = tight(doc[p + 1].get_text())
        for s in questions[i]["speaking"] + [questions[i]["essay"]]:
            if tight(s) not in qtext:
                missing_q.append(f"{i}:{s[:30]}")
        if "speaking" not in qtext or "essay" not in qtext:
            missing_q.append(f"{i}:labels")
    check(not missing_q, f"3 speaking questions + 1 essay after every article ({len(missing_q)} missing)"
          + ("" if not missing_q else f": {missing_q[:4]}"))
    over = []
    for i, p in enumerate(openers, 1):
        essay_top = A.WRITE_TOP - 128
        bottom = max((b[3] for b in doc[p + 1].get_text("blocks") if 80 < b[1] < essay_top), default=0)
        if bottom > essay_top - 4:
            over.append(i)
    check(not over, f"speaking questions clear the essay block ({len(over)} overlapping)")

    # --- Telegram QR on the cover and the back -------------------------------
    try:
        import zxingcpp
        from PIL import Image
        found = []
        for idx in (0, doc.page_count - 1):
            pix = doc[idx].get_pixmap(matrix=pymupdf.Matrix(3, 3))
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            found.append([r.text for r in zxingcpp.read_barcodes(img)])
        check(all(A.TELEGRAM_URL in f for f in found),
              f"Telegram QR decodes to {A.TELEGRAM_URL} on cover and back ({found})")
    except ImportError:
        notes.append("SKIP  QR decode (pip install zxing-cpp to check it)")
    handle = f"@{A.TELEGRAM}".lower()      # the cover sets it in capitals
    check(handle in doc[0].get_text().lower() and handle in doc[-1].get_text().lower(),
          f"@{A.TELEGRAM} printed on cover and back")

    bad_kick, no_photo, no_gloss, bad_terms, bad_text, other_level, strays = [], [], [], [], [], [], []
    for i, (art, p) in enumerate(zip(arts, openers), 1):
        op, rd = doc[p - 1], doc[p]
        if f"article{i:02d}" not in tight(op.get_text()):
            bad_kick.append(i)
        if not any(b["width"] > 300 and b["height"] > 200 for b in op.get_image_info()):
            no_photo.append(i)

        text = tight(rd.get_text())
        if "glossary" not in text:
            no_gloss.append(i)
        for term in A.vocab(art):
            if tight(term) not in text:
                bad_terms.append(f"{i}:{term}")
        body = A.plain(A.passage(art))
        for sample in (body[120:190], body[len(body) // 2: len(body) // 2 + 70], body[-80:-10]):
            if tight(re.sub(r"\s+([.,;:!?])", r"\1", sample)) not in text:
                bad_text.append(i)
                break
        # only the B2 version: an opening run of the B1 text must not appear
        b1 = A.plain(art["mock_data"].get("passageB1") or "")
        if b1 and tight(b1[20:90]) in text and b1[20:90] not in body:
            other_level.append(i)

        # text stays in its column: body 42..360, glossary panel 378..553
        for b in rd.get_text("blocks"):
            if b[1] < 70 or b[3] > 800:
                continue
            if not (b[2] <= 361.5 or b[0] >= 377.0):
                strays.append((i, round(b[0]), round(b[2])))

    check(not bad_kick, f"every opener carries its kicker ({len(bad_kick)} missing)")
    check(not no_photo, f"every opener carries its photograph ({len(no_photo)} missing)")
    check(not no_gloss, f"every reading page has its glossary ({len(no_gloss)} missing)")
    check(not bad_terms, f"every glossary term printed ({len(bad_terms)} missing)"
          + ("" if not bad_terms else f": {bad_terms[:5]}"))
    check(not bad_text, f"every B2 passage printed in full ({len(bad_text)} incomplete)")
    check(not other_level, f"only the B2 version is used ({len(other_level)} with B1 text)")
    check(not strays, f"body text and glossary keep to their columns ({len(strays)} strays)"
          + ("" if not strays else f": {strays[:4]}"))

    all_text = tight("".join(p.get_text() for p in doc))
    check("tarjima" not in all_text, "no Uzbek translation section")

    # palette: every vector fill is dodgerblue, an accent, ink/grey, paper or white
    allowed = {A.BLUE, A.INK, A.BODY, A.GREY, A.GREY_SOFT, A.HAIR, A.PAPER, A.HAIR_PAPER,
               "#FFFFFF", "#000000", "#111111"} | {a for a, _ in A.ACCENTS}
    # each glossary panel is a tint of its article's accent
    allowed |= {c for k in range(1, len(A.ACCENTS) + 1) for c in A.glossary_colours(k)}
    allowed = {c.upper() for c in allowed}
    seen = set()
    for p in doc:
        for g in p.get_drawings():
            for key in ("fill", "color"):
                c = g.get(key)
                if c:
                    seen.add(hexcol(c))
    off = sorted(c for c in seen if c not in allowed)
    check(not off, f"palette limited to dodgerblue + accents ({len(off)} other colours)"
          + ("" if not off else f": {off[:8]}"))

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
