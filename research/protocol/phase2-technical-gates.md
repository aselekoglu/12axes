# Phase 2: technical implementation with expert assessment DEFERRED

**There are no real expert ratings, interviews, approved pilot items, or study participants in this branch.** Do not infer content validity from lexical diagnostics or automatically generated records.

## What is operational now

1. Version-locked 240-item bilingual instrument; 72 common items, 12 axis and polarity groups.
2. Read-only **mechanical** inventory audit with 480 language-item rows and lexical anomaly flags. It cannot tell whether a political proposition is true, fair, leading or psychometrically valid.
3. Independent expert review packets, ingestion and conservative coverage summaries (implemented earlier).
4. 20-packet cognitive-interview allocation and new **private observation** schema. Blank moderator packets are explicitly not evidence.
5. Item-level **editorial decision ledger** (480 item-language rows), immutable item identities, provenance requirement for nonblank decisions, and no direct writeback to live quiz.
6. A fail-closed Phase 2 readiness dashboard that reports missing evidence and **always forbids enabling collection**. Human signoff is never simulated.

## Commands (run from repository root)

```sh
# No human data; safe automatic diagnostics
python3 -m research.item_audit
python3 -m research.item_audit --output /tmp/12axes-item-audit.json
python3 -m research.phase2_workflow

# Private reviewer packet, completed only by genuine experts later:
python3 -m research.content_review packet --reviewer expert_01 --lang en \
  --output /secure/review-materials/expert_01_en.csv

# Private cognitive interview templates, filled only after appropriate consent:
python3 -m research.cognitive_review template --interview COG_001 \
  --index 0 --lang en --output /secure/review-materials/cog_001.csv

# Template only: no editorial decisions are generated automatically
python3 -m research.phase2_workflow \
  --template /secure/review-materials/editorial-decisions.csv

# Later, after actual expert and cognitive data have been collected:
python3 -m research.phase2_workflow \
  --review /secure/review-materials/expert_A_en.csv /secure/review-materials/expert_B_en.csv \
  --interview /secure/review-materials/cog_001.csv \
  --decisions /secure/review-materials/editorial-decisions.csv \
  --output /secure/review-materials/phase2-readiness.json
```

Review and interview files stay private: code names must not be mapped to individuals in GitHub. All scores, interview observations and editorial decisions need actual human authorship. A fabricated rating in a synthetic **test case** is not research evidence.

## Release boundary

This tooling does **not** mutate `draft-0.1`, set `APPROVED_FOR_FIELDING`, create participant records, or emit an executable `pilot-1.0`. Actual expert review, cognitive interviews, translation adaptation, formal editorial decisions, research ethics and privacy/security approval are **blocked external gates**.

The next engineering step after those external gates is to create and review a separate versioned pilot snapshot with formally justified revisions, per-item provenance, frozen hash, and explicit expert/ethics signatures. Its item balance and questionnaire assignments must be recalculated before enabling any fielding service.

This phase is about building a reproducible process, **not certifying validity**.
