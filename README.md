# CEFR Materials

Multilevel (CEFR) exam material exported from the Mock Stream platform, plus the
builders that turn the Listening and Reading test data into print-ready books.

## Books

| File | Pages | Contents |
|---|---:|---|
| `materials/CEFR_Listening_Mock_Test_Book.pdf` | 126 | covers, overview, contents, 57 tests × 2 pages, 8 answer-key pages |
| `materials/CEFR_Reading_Mock_Test_Book.pdf` | 315 | covers, overview, contents, 71 tests × 4–5 pages, answer-key pages |
| `materials/CEFR_Listening_Cover.pdf` | 2 | A3 front + back cover, for printing separately |
| `materials/CEFR_Reading_Cover.pdf` | 2 | A3 front + back cover, for printing separately |
| `materials/cefr-listening-pdfs/` | 57 × 3 | one PDF per listening test, with its answer key |
| `materials/cefr-reading-pdfs/` | 71 | one PDF per reading test, with its answer key |

Each book carries its own covers as the first and last page, scaled from A3 to
the book's A4 (same 1:√2 portrait shape, so nothing is distorted). The
standalone A3 cover PDFs are kept for printing the cover on its own.

Layout is matched to `materials/demo_book.pdf`, which is the reference for the
page chrome: the gradient stripe, the banner, the dashed column divider
(2.25 pt dash on a 3.758 pt period at x = 298.24), the footer rule and the page
pill. Covers follow `materials/Cover_front_back.pdf`.

## Building

Needs Python 3.13+ with `pymupdf`, and Microsoft Edge or Google Chrome (the
builders drive it headless to render HTML to PDF).

```bash
pip install pymupdf
```

Run from `materials/`:

```bash
python build_cefr_book.py              # Listening book + 57 per-test PDFs
python build_cefr_reading_book.py      # Reading book + 71 per-test PDFs
python build_covers.py                 # both A3 covers
python attach_covers.py                # wrap each book in its covers
```

`attach_covers.py` runs last and is safe to re-run — a book that already has
its covers is skipped. Rebuilding a book drops them, so run it again after.

Pass test numbers to build a subset, e.g. `python build_cefr_book.py 1 2 3`, or
`--no-single` to skip the per-test PDFs.

On Windows, run these from PowerShell rather than Git Bash — MSYS path
translation mangles the `file:///` URLs and `--print-to-pdf` arguments passed to
the browser.

### Verifying

Both books are checked against the demo's measured geometry:

```bash
python verify_cefr_book.py
python verify_cefr_reading_book.py
```

These assert page and bookmark counts, the divider rhythm on every test page,
footer and page-pill placement, that no text crosses the column gutter, that
every part is present, and that every answer is printed in full.

## How the two builders differ

`build_cefr_book.py` (Listening) pins each test to two fixed pages and shrinks a
page slightly if its content overflows, because a listening test's parts are
short and predictable.

`build_cefr_reading_book.py` (Reading) cannot do that — the demo flows a
reading test's five parts continuously across however many pages they need. So
it renders the content as one multi-column document that Chrome paginates
natively, then stamps a separately rendered chrome layer underneath each page.
It imports the Listening builder for the shared chrome CSS and Edge plumbing.

## Data

`materials/<type>/NNN-<title>-idN.json` holds one test each, with every
question, option and answer under `mock_data`. `materials/INDEX.md` and
`materials/manifest.json` catalogue all 2,276 items;
`materials/README.md` documents the export itself.

**Not in this repository:** `materials/raw/` (the untouched API rows) and
`materials/media/` (21,154 audio and image files, ~5 GB). Media paths in the
JSON point at `audio.mock-stream.com`; `materials/_scripts/fetch_media.py`
re-downloads them into `materials/media/`. The reading and listening books need
only the JSON, except for the listening map images, which come from `media/`.
