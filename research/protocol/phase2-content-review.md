# Phase 2 — Scientific item content validation

**Design and tooling only. No completed expert reviews, interviews, or human research results exist here.**

## Research rationale

Evaluate each draft question for:
1. relevance to its claimed political construct and context;
2. clarity/comprehensibility in EN and PT separately;
3. construct fit (does a question meant to measure one axis introduce another?);
4. leading wording, double-barreled propositions, cultural/temporal ambiguity;
5. balance and comprehensiveness of the 12 proposed axes;
6. whether the response choices really represent the available opinions.

Methodological inspirations (adapted, **not** a COSMIN certification of a political survey):
- COSMIN content-validity Delphi: https://pmc.ncbi.nlm.nih.gov/articles/PMC5891557/
- Pew questionnaire wording and acquiescence: https://www.pewresearch.org/writing-survey-questions/
- CDC cognitive interviewing: https://www.cdc.gov/nchs/ccqder/question-evaluation/cognitive-interviewing.html

## Offline expert review workflow

Recruit independent subject-matter reviewers by appropriate qualifications and diversity
of expertise (political science, survey methods, psychometrics, and local/cultural context).
Ask them to review without seeing others' scores. Use pseudonymous reviewer IDs.

Generate separate blank **locked-text** CSVs in a secure private directory:

```bash
mkdir -p /secure/review-materials
python3 -m research.content_review packet --reviewer expert_01 --lang en \
  --output /secure/review-materials/expert_01_en.csv
python3 -m research.content_review packet --reviewer expert_02 --lang en \
  --output /secure/review-materials/expert_02_en.csv
# After independent reviewers actually complete their files:
python3 -m research.content_review report --min-raters 5 \
  --output /secure/review-materials/content_report_en.json \
  /secure/review-materials/expert_01_en.csv /secure/review-materials/expert_02_en.csv
```

Each question is rated 1–4 for **relevance**, **clarity**, and **construct fit**.
Scores 3–4 count as rated relevant for a descriptive item-level content validity
index (I-CVI). The `.78` discussion flag is an exploratory prompt, not an
automatic scientific acceptance threshold. If an item has insufficient expert
coverage, it **cannot** be treated as passed. An overall S-CVI/Ave is withheld
unless *all 240 items* have the requested review coverage in a single language.
Independent qualitative feedback and construct-map holes matter more than a
mechanically calculated average. Review summaries never rewrite live questions.

## Cognitive interviews

Use qualitative think-aloud and interviewer probes. For each source-language
cohort, the proposed 20-packet allocation shows 24 distinct questions per
interview, one LEFT + one RIGHT for each of 12 axes. Over 20 packets, all 240
questions are assigned *twice*. This is **coverage bookkeeping**, not a guarantee
of comprehension or suitable interview length; a researcher must pilot duration
and may split long interviews into smaller sections.

```bash
python3 -m research.cognitive_packets --audit
python3 -m research.cognitive_packets --index 0 --lang en --round draft-round-1 \
  --output /secure/review-materials/interview_00_en.csv
```

Record moderator observations in private, access-controlled storage only.
Avoid interview recordings, political self-disclosures, names, quotations or
contact details in the GitHub repository. Participant consent and any relevant
review requirements precede real interviewing.

## Research gates

Do not publish a `pilot-1.0` survey snapshot until the review board has
documented how every item was retained/revised/reassigned/retired, translations
have been independently adapted, coverage of each construct has been reassessed,
the form assignment has been recalibrated, and study/ethics/security signoffs
have been recorded outside the repo. Content review does not establish factor
structure or instrument validity.
