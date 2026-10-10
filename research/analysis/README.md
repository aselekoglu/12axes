# Research analysis — locked-split baseline

**NO empirical findings have been produced. This is an offline analysis scaffold.**
Do not treat any results as evidence that 12Axes has been validated before
genuine recruitment, preregistration, expert assessment and independent review.

Input is a *restricted pseudonymized* export produced by `python -m research.export`:
`participants.csv`, `assignments.csv`, `answers.csv`, `archetypes.csv`.
Files should never be committed, uploaded to CI, or added to public reports.
The `participants.csv` EFA/CFA allocation is keyed and fixed during export.

## Run (approved research environment only)

```sh
Rscript research/analysis/run.R /secure/private/export-directory /secure/private/output-directory
```

Requires R and the `psych` / `lavaan` packages, installed under a research-maintained
`renv` lockfile prior to empirical analysis. This is **not** a preregistered statistical
model or reproducible package lock yet; versions must be frozen before fielding.

The script validates complete 72-item anchor data, checks planned-missing coverage,
computes an exploratory polychoric EFA and holds back the CFA set for an ordinal
12-factor CFA. It fails closed on inadequate sample sizes or unknown response keys.
Report model fit, loadings, correlated factors, missingness, alternative constructs
and uncertainty rather than presenting a single score as 'scientifically validated'.

**Pre-registration required:** independent power simulation, factor-number decision rule,
handling of local dependence, model-selection multiplicity, DIF, retest reliability,
sample exclusions, and publication plan. Consider higher-order/fewer-factor models.

## Fictional pipeline fixture

```bash
python3 -m research.analysis.synthetic /tmp/12axes-fake-data --participants 800
# This writes a SYNTHETIC_TEST_DATA_ONLY marker and FAKE_SYNTHETIC_ participant IDs.
# Do not publish factors or results from simulated respondents as empirical evidence.
```

R package versions are **not yet locked** by renv, so the R pipeline is a
development scaffold rather than fully reproducible research. Before empirical
analysis, generate and review a project-specific renv.lock in a pinned R
environment, and test EFA/CFA under documented package versions.
