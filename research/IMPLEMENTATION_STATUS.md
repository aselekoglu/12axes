# 12Axes research implementation / status

This branch implements a **versioned research-only draft instrument** and a
separate, opt-in study stack. The legacy product scoring and user quiz are unchanged.

| Component | State |
|---|---|
| 240 bilingual questions and 5 archetypes, versioned / hash-locked | Implemented |
| 72 common + 48 rotating, axis/polarity balanced form assignments | Implemented |
| Read-only research preview with React UI at /research | Implemented (requires research API) |
| PostgreSQL table definition and separate FastAPI enrollment / submit / withdraw endpoints | Implemented; real PostgreSQL synthetic lifecycle tested in CI; no production deployment |
| Strict consent / 18+ / invite / version+SHA study release gates | Implemented, DISABLED |
| Unit tests and research CI job | Implemented, CI results require verification |
| Restricted pseudonymized CSV export | Implemented; run only in approved isolated environment |
| Ordinal EFA/CFA baseline R pipeline | Implemented scaffold + synthetic CSV fixtures, no participant data; R dependencies not yet locked |
| Phase 2 automated question diagnostics, offline dashboard, and expert review templates | Implemented; lexical flags only, not scholarly judgments |
| Phase 2 cognitive observation and 480-row editorial decision ledger | Implemented; private input parser and mandatory evidence references; no human evaluation |
| Phase 2 readiness dashboard and future non-fieldable candidate | Implemented; hard-blocked pending expert and participant input |
| Independent expert review and cognitive interviews | **DEFERRED**; no actual external review or participant interviews performed |
| Approved pilot-1.0 instrument and ethics/privacy approval | Not performed |
| Recruiting human subjects, collecting data, validating 12 factors | Not performed |
| Production-ready operational security and backups withdrawal audit | Not verified |

This project must not claim an instrument has been scientifically validated.
Refer to `SERVICE.md`, `FRONTEND.md`, `protocol/expert-coding.md`, `analysis/README.md` and the proposed
`protocol/` for governance and implementation. Cross-language validity,
retest, graded-response IRT, expert coding reliability and external validation
are not implemented as completed analyses until their designs and real input data
are available.

**Safety requirements:** treat all individual political attitudes as sensitive,
never collect them through the existing anonymous product API, never ship
invitation credentials or server secrets in frontend artifacts, and never upload
research data to public GitHub or CI.

## Phase 1 verification
- Docker Compose local preview and isolated Postgres: `PHASE1.md`.
- Live PostgreSQL lifecycle CI: `research/integration_tests/`, using synthetic respondents only.
- API security and retention/monitoring: `OPS.md`.
- No real participant responses have been collected. Do not enable collection until governance and privacy gates pass.


## Phase 2 technical status

- `python3 -m research.item_audit`: reproducible 480 language-item mechanical diagnostics.
- `python3 -m research.item_dashboard --output /tmp/review.html`: offline audit browser.
- `python3 -m research.cognitive_review template ...`: private blank moderator forms.
- `python3 -m research.phase2_workflow --template /secure/reviews/decisions.csv`:
  480 unapproved item+language revision entries.
- `python3 -m research.phase2_workflow`: missing evidence dashboard; fielding ALWAYS false.
- `research.phase2_candidate`: future candidate-only compiler, not usable until
  human evidence and editorial decisions are complete; output never approved.
- All source versioning, common/rotating item assignments and normal quiz behavior
  remain unchanged. No researcher observations, political answers, or private
  participant data should be saved in this repository.
