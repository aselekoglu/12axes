# Preregisterable statistical analysis plan — DRAFT

This is a structured **pre-registration candidate**, not preregistration or evidence of validity. Finalize hypotheses, estimators, thresholds and exclusion rules before accessing empirical outcomes.

## Confirmatory separation

Randomize completed eligible records into discovery (EFA) and locked confirmation (CFA) groups with a saved allocation seed. Avoid tuning EFA model choices on the confirmatory sample. For the 72 complete common questions, consider ordered-categorical polychoric EFA with parallel analysis and oblique factor rotation; compare theoretically defensible alternatives to 12 factors. Confirmatory ordinal CFA, item residuals, cross-loadings and fit diagnostics on the held-out group.

## Planned-missing rotation

The other 168 rotating questions have by-design missingness. Do **not** substitute neutral answers for unassigned questions or naïvely run a 240-variable complete-case factor analysis. Use appropriate planned-missing IRT / ordinal modeling and inspect co-administration, coverage per item and dropout-related missingness. Estimate per-axis score precision.

## Other validation streams

- Reliability: omega with uncertainty, test-retest ICC from separately consented follow-up, and response-style / reverse-keying diagnostics.
- Sensitivity: short-form subsampling, alternative form designs, language adaptation, DIF and measurement invariance if subgroup sizes allow.
- External criteria: independent political/self-report instruments, policy preferences and preregistered construct hypotheses; do not validate matches against 12Axes' own simulated catalog.
- Historical profiles: dated sourced evidence, unknown/not-applicable distinct from neutral, multiple independent expert raters, disagreement and uncertainty estimates.
- Report failures and competing models; **do not** relabel inferred dimensions to force the predetermined 12-axis result.

## Planned tooling

R (`psych`, `lavaan`, `mirt`, possibly `semTools`), `renv` lockfile and Quarto reproducible report. Versions, seeds, cleaning rules and instrument version belong with each analysis artifact. No scientific thresholds or validation metrics are claimed at this stage.

References: https://lavaan.ugent.be/tutorial/cat.html ; https://philchalmers.github.io/mirt/docs/reference/mirt.html ; https://www.pewresearch.org/politics/2026/06/10/appendix-b-typology-group-creation-and-analysis/
