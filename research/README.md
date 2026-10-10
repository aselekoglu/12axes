# 12Axes Research — implementation guide

**This is an experimental measurement research platform, not a validated scale or an
authorized political-opinion survey. The public quiz's scoring remains unchanged.**

## Architecture and progress

- Immutable PT/EN 240-question bank in `instruments/draft-0.1/`; core/rotating
  72+48 question allocation in `assignment.py`.
- An independent FastAPI `service.py` plus PostgreSQL schema, disabled by default,
  with a React `/research` development preview.
- Docker Compose and PostgreSQL synthetic lifecycle test (see `PHASE1.md`),
  restricted local export, retention and aggregate monitoring (see `OPS.md`).
- Ordinal psychometric exploratory scaffolding and **explicitly synthetic**
  datasets (see `analysis/README.md`). No empirical validity metrics exist.
- Phase 2 item-bank/translation diagnostics, review/interview instruments,
  private observation and editorial-decision tools; **no expert scores or human
  interview data have been collected**.

## Run the offline Phase 2 tooling (no personal information)

```sh
python3 -m research.item_audit
python3 -m research.item_dashboard --output /tmp/12axes-review.html
python3 -m research.phase2_workflow
python3 -m research.cognitive_packets --audit
python3 -m unittest discover -s research/phase2_tests -v
python3 -m unittest discover -s research/phase2_workflow_tests -v
python3 -m unittest discover -s research/phase2_artifact_tests -v
```

Open the generated HTML locally to browse English/Portuguese questions by axis,
keywords, core membership and **mechanical** wording flags. This is not a content
validity evaluation. GitHub Actions publishes this *public-question-only* HTML and
JSON as a short-lived CI artifact. It never contains expert ratings.

The 480-row decision ledger and private human observation schemas are specified
under `protocol/phase2-technical-gates.md`. All incomplete forms are treated as
pending evidence, never an implicit pass.

## Restrictions

Do not silently harvest answers from the normal `/api/results`.
Do not recruit people on this draft instrument. Never mark `pilot-1.0` approved
merely because CI passes. Real expert ratings, cognitive interviews, independent
privacy/ethics review, signed research protocol and independent pilot release
decisions are intentionally deferred and external to software automation.

A `candidate-0.1` compiler exists as a **future** technical tool, but requires
the complete private expert/interview evidence and editorial decision ledger.
Even then it writes `NOT_APPROVED_FOR_FIELDING`; the live research API does not
load that format. More details: `protocol/phase2-dashboard-and-candidate.md`.

## Reference

`protocol/study-protocol.md`, `protocol/analysis-plan.md`,
`protocol/phase2-content-review.md`, `protocol/phase2-cognitive-interviews.md`,
`SERVICE.md`, `FRONTEND.md`, `OPS.md`.
