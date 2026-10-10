# Phase 2 review interface and safe future candidate bundle

New **static offline review dashboard** (no database, external dependencies or participant data):

```sh
python3 -m research.item_dashboard --output /tmp/12axes-review.html
# Open /tmp/12axes-review.html in a browser
```

The dashboard filters the 240 questions by language, axis, 72-common subset,
search text and non-scientific wording flags. It does not display fictitious
expert ratings or register decisions. The same HTML and machine-readable JSON
are uploaded to GitHub Actions as **phase2-public-question-audit** for 14 days.
These contain only already-public item text and mechanical diagnostics.

A real editorial decision ledger may eventually be compiled into an **unapproved**
candidate after all 480 item-language decisions, expert ratings and cognitive
observations are complete:

```sh
python3 -m research.phase2_candidate \
  --decisions /secure/review-materials/decisions.csv \
  --experts /secure/review-materials/expert-en.csv /secure/review-materials/expert-pt.csv \
  --interviews /secure/review-materials/cognitive-en.csv /secure/review-materials/cognitive-pt.csv \
  --output /secure/review-materials/candidate-0.1.json
```

This must fail with missing human evidence right now, **by design**.
Even after real evidence is present, the output is always
`candidate-0.1` with `research_status=NOT_APPROVED_FOR_FIELDING`,
which the live assignment engine rejects. Real-world external review,
privacy/ethics authorization and independently documented release criteria
remain mandatory.

**Do not commit completed private review data or cognitive transcripts.**
