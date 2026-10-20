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
| `materials/CEFR_Article_Book.pdf` | 63 | magazine-style reader: 20 B2 articles with glossary, speaking and essay questions |

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
pip install pymupdf segno          # segno draws the article book's Telegram QR code
```

Run from `materials/`:

```bash
python build_cefr_book.py              # Listening book + 57 per-test PDFs
python build_cefr_reading_book.py      # Reading book + 71 per-test PDFs
python build_covers.py                 # both A3 covers
python attach_covers.py                # wrap each book in its covers
python build_article_book.py           # B2 article reader (default 20)
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
python verify_article_book.py
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

## The article reader

`build_article_book.py` builds a magazine-style reader from the B2 version of
the first N articles (default 20; `python build_article_book.py 30` for thirty). Each
article takes three pages:

- **Opener** — the article's photograph in high-contrast black and white, set in
  one of five layouts that rotate through the book: a colour band across the
  photo, a giant serif initial behind it, a rotated title on a vertical strip, a
  circle split between photo and colour, and a photo grid with a title block.
- **Reading page** — the text opened by a giant initial, a solid pull-quote
  block, its key terms underlined, and a numbered glossary (term and definition,
  in the order the terms appear) on the right, in a panel tinted with that
  article's accent colour.
- **Questions page** — three speaking questions to discuss with a partner, five
  of the article's key words to try using, and an essay task with ruled lines to
  write on. The questions live in `materials/article_questions.json`, keyed by
  article number and checked against the article's title; edit and rebuild.

The cover and a dodgerblue back cover carry a QR code for the Telegram channel
[@cefr_impulse](https://t.me/cefr_impulse), drawn as vector so it prints sharp.
`verify_article_book.py` decodes it when `zxing-cpp` is installed.

Dodgerblue leads on every page; each article also carries one secondary accent
(coral, saffron or mint, cycled) for its outline number, pull quote and small
shapes. Apart from the photographs, every shape is drawn by the builder, so it
needs no external image service. Type is Bahnschrift for display and Georgia
for text, both standard on Windows.

`gen_article_images.py` optionally generates a replacement photograph per
article through the OpenAI images API; the book converts it to black and white
like the others. It needs `OPENAI_API_KEY` in the environment and does nothing
(and costs nothing) without it:

```bash
python gen_article_images.py --dry-run   # print the prompts, call nothing
python gen_article_images.py             # generate, skipping any already done
```

Images land in `media/article-illustrations/` (not committed, like the rest of
`media/`) and `build_article_book.py` places them automatically on the next run.

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

## Videos

`cefr_video_generation/` is a Remotion project that produces the video material: an
Uzbek explainer of the Multilevel exam, and a timed Speaking mock-exam simulation in
YouTube (16:9) and Instagram Reels (9:16) formats, with ElevenLabs narration. See its
[README](cefr_video_generation/README.md). Like `materials/media/`, the Mock Stream
question media is not committed; the project's build script re-downloads it.
