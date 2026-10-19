"""Write materials/INDEX.md — a readable catalogue of everything downloaded."""
import json, os, collections

ROOT = r"C:/temporary/multilevel_reels/materials"
man = json.load(open(os.path.join(ROOT, "manifest.json"), encoding="utf-8"))

LABEL = {
    "cefr-reading": "Multilevel (CEFR) Reading",
    "cefr-listening": "Multilevel (CEFR) Listening",
    "ielts-reading": "IELTS Reading",
    "ielts-listening": "IELTS Listening",
    "ket-reading-writing": "Cambridge KET — Reading & Writing",
    "ket-listening": "Cambridge KET — Listening",
    "pet-reading": "Cambridge PET — Reading",
    "pet-listening": "Cambridge PET — Listening",
    "fce-reading-writing": "Cambridge FCE — Reading, UoE & Writing",
    "fce-listening": "Cambridge FCE — Listening",
    "cae-reading-writing": "Cambridge CAE — Reading, UoE & Writing",
    "cpe-reading-writing": "Cambridge CPE — Reading, UoE & Writing",
    "cefr-writing": "Multilevel (CEFR) Writing",
    "cefr-speaking": "Multilevel (CEFR) Speaking",
    "ielts-writing": "IELTS Writing",
    "ielts-speaking": "IELTS Speaking",
    "pet-writing": "Cambridge PET — Writing",
    "grammar": "Learn — Grammar",
    "vocabulary": "Learn — Vocabulary",
    "flashcard": "Learn — Flashcards",
    "article": "Learn — Articles",
}
ORDER = list(LABEL.keys())
# The Learn types run to hundreds of rows each — listing every one would
# bury the mock tables, so the index gives them a count line instead.
SUMMARY_ONLY = {"grammar", "vocabulary", "flashcard", "article"}

by = collections.defaultdict(list)
for m in man:
    by[m["mock_type"]].append(m)

lines = ["# Multilevel Record — reading & listening materials", ""]
lines.append("Source: multilevelrecord.com (Mock Stream platform), signed in as the account owner.")
lines.append("")
lines.append("Each mock is one JSON file holding the full test: passages/transcript structure,")
lines.append("every question, the answer key and any media references. Audio and images are")
lines.append("mirrored under `media/` with the same paths the site uses.")
lines.append("")
lines.append("| Category | Mocks | Folder |")
lines.append("|---|---:|---|")
total = 0
for t in ORDER:
    if t not in by:
        continue
    total += len(by[t])
    lines.append("| %s | %d | `%s/` |" % (LABEL[t], len(by[t]), t))
lines.append("| **Total** | **%d** | |" % total)
lines.append("")

for t in ORDER:
    if t not in by:
        continue
    rows = sorted(by[t], key=lambda r: (r["mock_number"] is None, r["mock_number"] or 0))
    lines.append("## %s (%d)" % (LABEL[t], len(rows)))
    lines.append("")
    if t in SUMMARY_ONLY:
        lines.append("%d items in `%s/`, one JSON file each. See `manifest.json` "
                     "for the full list." % (len(rows), t))
        lines.append("")
        continue
    lines.append("| # | Title | File | Media refs |")
    lines.append("|---:|---|---|---:|")
    for r in rows:
        lines.append("| %s | %s | `%s` | %d |" % (
            r["mock_number"], (r["title"] or "").replace("|", "/"), r["file"], r["media_count"]))
    lines.append("")

with open(os.path.join(ROOT, "INDEX.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("INDEX.md written -", total, "mocks across", len([t for t in ORDER if t in by]), "categories")
