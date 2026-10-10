# Independent expert evidence coding (design)

This stream complements human questionnaire validation. It does NOT fabricate
historic politicians' answers or re-label LLM outputs as expert truth.

## Evidence record
Store one JSON document per time-specific historic/ideology/country profile.
Each independent expert must work blind to the other raters' assessments and
to the existing simulated profile scores. Each rated question carries:

- `rater_id`: pseudonymous independent expert identifier (not name/email).
- `question_id` and `axis_id`: frozen instrument identifiers.
- `evidence_state`: `OBSERVED`, `INFERRED`, `UNKNOWN`, `NOT_APPLICABLE`.
- `answer`: `DT|D|N|C|CT` for OBSERVED/INFERRED; **null** when UNKNOWN / NOT_APPLICABLE.
- `sources`: HTTPS URLs, dates and notes, required for OBSERVED.
- At profile level: `profile_id`, `reference_period`, `instrument_version`, `ratings`.

Use `python3 -m research.expert_audit path/to/private/audit.json` to
validate and flag contested answers without resolving them automatically.

A real codebook must define what qualifies as a directly observed political
statement or a justified inference, treatment of disputed source authenticity,
translations, historical anachronism and period selection. Candidate targets:
30–60 selected profiles with 2–3 experts per profile, but actual sampling and
inter-rater reliability analysis require preregistration. Do not treat the script's
descriptive exact-agreement count as Krippendorff alpha or a validity estimate.
Do not add expert identifiers, unpublished evidence or personal data to the public repo.
