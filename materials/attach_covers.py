"""
Wrap the built books in their covers.

The covers are A3 (841.92 x 1191.12pt) and the books A4 (595.32 x 841.92pt) --
the same 1:sqrt(2) portrait shape, so each cover page is placed scaled into an
A4 page and the artwork is not distorted. The standalone A3 cover PDFs are left
alone for printing.

Run after build_cefr_book.py / build_cefr_reading_book.py and build_covers.py:

    python attach_covers.py

It is safe to re-run: a book that already carries its covers is skipped.
"""
import os
import sys

import pymupdf

import build_cefr_book as L

ROOT = L.ROOT_DIR

PAIRS = [
    ("CEFR_Listening_Mock_Test_Book.pdf", "CEFR_Listening_Cover.pdf"),
    ("CEFR_Reading_Mock_Test_Book.pdf", "CEFR_Reading_Cover.pdf"),
]

FRONT, BACK = "Front cover", "Back cover"


def already_wrapped(book):
    toc = book.get_toc()
    return bool(toc) and toc[0][1] == FRONT


def attach(book_path, cover_path):
    book = pymupdf.open(book_path)
    if already_wrapped(book):
        print(f"  {os.path.basename(book_path)}: already has covers, skipped")
        book.close()
        return
    cover = pymupdf.open(cover_path)
    if cover.page_count < 2:
        raise RuntimeError(f"{cover_path} has {cover.page_count} pages, expected 2")

    rect = book[0].rect
    w, h = rect.width, rect.height
    ar_book, ar_cover = w / h, cover[0].rect.width / cover[0].rect.height
    if abs(ar_book - ar_cover) > 0.01:
        raise RuntimeError(f"aspect mismatch: book {ar_book:.4f} vs cover {ar_cover:.4f}")

    n_before = book.page_count
    book.insert_page(0, width=w, height=h)
    book[0].show_pdf_page(book[0].rect, cover, 0)
    book.insert_page(book.page_count, width=w, height=h)
    book[-1].show_pdf_page(book[-1].rect, cover, 1)

    # insert_page already re-targets the existing outline, so the entries read
    # back here are correct -- shifting them again would double-count.
    toc = [[lvl, "Overview" if title == "Cover" else title, page]
           for lvl, title, page in book.get_toc()]
    toc.insert(0, [1, FRONT, 1])
    toc.append([1, BACK, book.page_count])
    book.set_toc(toc)

    # pymupdf cannot rewrite the file it has open, so save beside it and swap
    tmp = book_path + ".tmp"
    book.save(tmp, garbage=3, deflate=True)
    pages = book.page_count
    book.close()
    cover.close()
    os.replace(tmp, book_path)
    print(f"  {os.path.basename(book_path)}: {n_before} -> {pages} pages "
          f"(front + back cover added)")


def main():
    missing = [f for pair in PAIRS for f in pair
               if not os.path.exists(os.path.join(ROOT, f))]
    if missing:
        print("Missing, build them first:")
        for m in missing:
            print("  ", m)
        return 1
    print("Attaching covers...")
    for book, cover in PAIRS:
        attach(os.path.join(ROOT, book), os.path.join(ROOT, cover))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
