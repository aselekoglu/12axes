# 12Axes scientific validation — foundation (NOT a live study)

This directory is the **first implementation increment**, not a validated questionnaire or active study. It changes **no existing quiz behavior or scoring**, makes **no network calls**, does **not persist political answers**, and has **no consent or recruitment endpoint**.

## Implemented

- `instruments/draft-0.1/instrument.json` — versioned research-only snapshot of 240 PT/EN questions, polarity, weights, 12 axes, five archetype questions, source Git commit + original file blob SHAs. Its 72-item common core is **mechanically selected and not expert-approved**.
- `assignment.py` — deterministic offline, axis/polarity balanced form generation: 72 common (3 LEFT + 3 RIGHT per axis) plus 48 rotating (2 LEFT + 2 RIGHT per axis), 120 Likert items total.
- 7-form rotation: every non-core question occurs exactly twice per 7 issued form indices. Shuffling is reproducible via explicit `study_seed`; registration order must not be linked to answer-derived traits.
- Standard-library unit tests and coverage simulation.
- Draft protocol and stage gates in `protocol/`.

## Run

```bash
python3 -m unittest discover -s research/tests -v
python3 -m research.assignment --index 0
python3 -m research.assignment --coverage 2400
```

`--coverage` counts **assigned** questions, *not collected answers*. It is a design simulation only.

## Before recruiting anyone

1. Confirm target population, jurisdiction, responsible institution and research governance/ethics review.
2. Expert-review and cognitively test constructs, wording, translations and selected 72 common items.
3. Publish/preregister the analysis plan and sample-size simulations; freeze an approved `pilot-1.0` instrument with per-item hashes.
4. Build separate, opt-in consent, secure database-backed sessions, idempotent response API, withdrawal/deletion, researcher access control and export. Do not modify `POST /api/results` to harvest political answers.
5. Test data privacy, deployment configuration, and retention/backup deletion end to end. Keep collection **disabled by default** until external study authorization is complete.

## Next implementation increment

Create a Spring Boot `research` module and PostgreSQL/Flyway schema for consented sessions and version-pinned assignments, then a separate React research-only route. Keep current matching and share links unchanged. A `pilot-1.0` release must never silently use draft items, new scoring, or participant data without consent.

Reference: `protocol/study-protocol.md`, `protocol/analysis-plan.md`.
