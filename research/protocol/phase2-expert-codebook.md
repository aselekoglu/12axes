# Expert item review codebook — draft 0.1

The 12 dimensions are **hypotheses to interrogate**. Do not assume that a
question belongs to its source axis because the JSON says so.

## Evaluation per question

Rate each 1–4 independently (avoid using the same score for all by default):
- **Relevance:** 1 not related; 2 only tangentially related; 3 materially relevant;
  4 central to the proposed construct.
- **Clarity:** 1 uninterpretable; 2 ambiguous; 3 generally clear;
  4 clear and specific for the intended population.
- **Construct fit:** 1 predominantly measures another construct; 2 strongly
  confounded with another; 3 mainly measures the intended axis; 4 focused,
  discriminating representation of this axis.

Check yes/no/blank (blank means **not assessed**, not no):
- `leading_yes_no`: implicit normative push, emotive labels, or presuppositions.
- `double_barrel_yes_no`: combines independently disputable claims.
- `cross_cultural_risk_yes_no`: terms or presuppositions likely vary across
  countries/languages or historical contexts.

`proposed_axis_id` may be used when a different dimension better captures
the proposition. `proposed_action`: retain / revise / reassign / retire /
discuss. `evidence_note`: concise rationale, example ambiguous phrasing,
possible alternative wording, and sources when relevant.

**Reviews must be independent.** Do not create ratings with language models
and present them as human expert scores. No domain threshold in this codebook
is a professional certification. Missing evaluations are not zeros and may
not be imputed as agreement.

## Suggested expert panel

A provisional 5–7 reviewers per language/discipline mix can be budgeted for
initial content validation; their independence and relevant expertise matter.
Decide the actual panel/translation plan before recruitment. Consider
separate domain maps for countries and languages; recognize that the
concepts *federalism* / *centralism*, *multiculturalism*, and *religion* may
have materially different social meanings in distinct contexts.

## Documentation for each revision

Maintain a private decision log recording instrument version, old/new item,
reviewer concerns, disagreement rationale, final editorial rationale,
decision-maker, date, test implications and version bump. No silent changes to
the frozen `draft-0.1` question snapshot.
