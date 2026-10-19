# Multilevel Record — full material export

Everything the account at **multilevelrecord.com** (Mock Stream platform) holds,
pulled 2026-10-19 while signed in as `examonlineedumo@gmail.com`.

**2,276 items · 21,154 media files · 5.10 GB · 0 missing**

## Layout

```
materials/
  INDEX.md                   catalogue — every mock, by category, with its file path
  manifest.json              the same catalogue as machine-readable JSON
  raw/<type>.json            one file per category: the untouched API rows
  <type>/NNN-<title>-idN.json   one file per item (the readable, per-test copy)
  media/                     audio + images, mirroring the site's own URL paths
  media_urls.txt             every asset URL referenced (21,154)
  _scripts/                  the scripts used, so this can be re-run or refreshed
```

## What's in an item file

Each per-item JSON holds the complete test under `mock_data`:

- **Reading** — `passages` (IELTS) or `parts` (Multilevel/Cambridge): full passage
  text, every question, options and the answer key.
- **Listening** — `parts` with every question and answer, plus audio references.
- **Writing** — `tasks` / `part1`, prompts, chart images, band labels, vocabulary
  and model answers.
- **Speaking** — `questions` with per-question prompt audio, cue images, and A1–C2
  sample answers (English + Uzbek).
- **Learn** — grammar/vocabulary question banks, flashcard decks with per-card
  audio, and articles at B1/B2/C1 with narration and word-level timings.

Media paths in the JSON point at `audio.mock-stream.com`. The same path under
`media/` is the local copy, e.g.
`https://audio.mock-stream.com/test52/PART 1.m4a` → `media/test52/PART 1.m4a`.

## Counts

| Category | Items | Assets |
|---|---:|---:|
| IELTS Reading | 114 | 2 |
| IELTS Listening | 113 | 487 |
| IELTS Writing | 96 | 163 |
| IELTS Speaking | 99 | 1,975 |
| Multilevel (CEFR) Reading | 71 | 0 |
| Multilevel (CEFR) Listening | 57 | 394 |
| Multilevel (CEFR) Writing | 104 | 100 |
| Multilevel (CEFR) Speaking | 65 | 780 |
| Cambridge KET — Reading & Writing | 28 | 0 |
| Cambridge KET — Listening | 28 | 563 |
| Cambridge PET — Reading | 8 | 96 |
| Cambridge PET — Listening | 8 | 212 |
| Cambridge PET — Writing | 8 | 9 |
| Cambridge FCE — Reading, UoE & Writing | 1 | 0 |
| Cambridge FCE — Listening | 1 | 4 |
| Cambridge CAE — Reading, UoE & Writing | 2 | 0 |
| Cambridge CPE — Reading, UoE & Writing | 2 | 0 |
| Learn — Grammar | 402 | 402 |
| Learn — Vocabulary | 342 | 342 |
| Learn — Flashcards | 507 | 16,138 |
| Learn — Articles | 220 | 1,480 |
| **Total** | **2,276** | **23,147**¹ |

¹ References, counted per item; 21,154 unique files (shared covers, logos and
shared Cambridge audio are referenced by more than one item).

Reading categories show few or no assets because reading passages are text held
in the JSON itself.

## Re-running

```bash
python -I _scripts/collect_media.py   # rebuild media_urls.txt from raw/
python -I _scripts/extract.py         # re-split raw/ into per-item files + manifest
python -I _scripts/fetch_media.py     # download media (skips files already present)
python -I _scripts/build_index.py     # rebuild INDEX.md
python -I _scripts/coverage.py        # per-category check that nothing is missing
```

`raw/` is refreshed by querying the platform's Supabase REST API for `mock_tests`
rows filtered by `mock_type`.

## Notes and known gaps

- **Asset collection walks the data tree, not the JSON text.** An earlier
  regex-based pass missed every URL containing a literal space — e.g.
  `.../test52/PART 1.m4a` — and so skipped 108 listening files without any
  download error. `collect_media.py` resolves assets structurally and also joins
  relative values to their declaring base (`audio.base`, `imageBase`), which the
  regex could not see at all.
- **Article dictation audio is unavailable.** Every article declares
  `audio.<level>.dictationBase` pointing at a `dictation-b1/` style folder, but
  those folders return 404 on the server across every article probed — the
  assets were never published. Nothing was downloadable there.
- Word-level narration timings (`audio.<level>.timings`, 630 `.json` sidecars)
  *are* included; they drive the article reader's text highlighting.
