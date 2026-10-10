# 12Axes measurement validation: research protocol (DRAFT — NOT PREREGISTERED)

**Status:** design only; no institutional ethics clearance or active recruitment.
**Scientific claim:** Not yet a validated political attitude measure. The 12 preassigned axes are hypotheses, not proven latent factors.

## Research objectives

1. Investigate whether 12 hypothesized constructs are distinguishable in observed human responses.
2. Compare item wording, keying, reliability, local dependencies, and response-style effects.
3. Compare 36/60-item product variants with a calibrated long inventory, with uncertainty.
4. Separately test AI-generated profiles against dated documentary evidence and blinded human-expert codings. Never use generated catalog scores as their own ground truth.

## Population and consent

First select one language / jurisdiction / population (e.g., PT-BR speaking adults 18+ residing in Brazil); later cross-language use needs adaptation and invariance evidence. A voluntary website sample is not a population probability sample. Collect no political answers without affirmative, specific study consent. Use separate data minimization, deletion/withdrawal mechanism, retention plan, researcher roles, and review of applicable legal/ethics duties.

## Item bank and forms

Source inventory: 240 questions, 20 per axis, 10 LEFT and 10 RIGHT, five separate archetype questions. The `draft-0.1` snapshot is retained independent of mutable production JSON.

Provisional form design: 72 common items (three of each polarity per axis) + 48 rotating items (two of each polarity per axis): 120 per person; archetype responses evaluated separately from the primary latent model. The current 72 common items were selected **mechanically for infrastructure testing**, *not psychometrically selected*. Expert assessment and cognitive interviews can change items and form design before locking the real pilot instrument.

The rotation cycles through seven participants. Each of the 168 non-core items appears twice per seven assigned forms, conditional on issuance, not completion. Store assigned item IDs and displayed order; non-assignment must be distinguished from nonresponse. Track item-pair overlap and early dropout for sparse-data diagnostics.

## Planned research stages and decision gates

- **Content validity:** 5–7 independent subject-matter experts as planning target; item-level relevance, wording, bias, polarity, construct fit and localized meaning. Preserve disagreement rather than forcing a consensus.
- **Cognitive interviews:** 2–3 rounds, about 5–15 interviews per round as a starting plan; revise misunderstood or double-barreled items.
- **Feasibility:** roughly 100–150 consenting participants; evaluate median duration, attrition, missingness and mobile accessibility. Do not infer 12 factors from this small feasibility sample.
- **Main study:** initial budgeting target approximately 2,400 completed participants, split *before model fitting* into discovery and independent confirmation subsamples, approximately 1,200 each. This is not a generic statistical minimum. Reassess based on Monte Carlo simulations of communalities, factor count, missingness and item information.
- **Cross-cultural:** test PT/EN equivalence and other populations separately; no automatically universal generalization.

## Ethics and reporting

No recruiting, production DB schema, response capture, or publication of empirical findings exists yet. AERA/APA/NCME validity framework; Boateng et al. scale-development stages; MacCallum et al. sample-size factors; ITC language adaptation; AAPOR transparency/disposition requirements; and V-Dem/CHES expert disagreement principles inform the intended study design. Protocol choices in this file are project proposals rather than mandatory scientific constants.

References: https://www.testingstandards.net/open-access-files.html ; https://doi.org/10.3389/fpubh.2018.00149 ; https://doi.org/10.1093/poq/nfm006 ; https://aapor.org/standards-and-ethics/transparency-initiative/ ; https://www.v-dem.net/about/v-dem-project/methodology/
