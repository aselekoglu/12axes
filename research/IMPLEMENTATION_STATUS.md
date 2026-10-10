# 12Axes research implementation / status

This branch implements a **versioned research-only draft instrument** and a
separate, opt-in study stack. The legacy product scoring and user quiz are unchanged.

| Component | State |
|---|---|
| 240 bilingual questions and 5 archetypes, versioned / hash-locked | Implemented |
| 72 common + 48 rotating, axis/polarity balanced form assignments | Implemented |
| Read-only research preview with React UI at /research | Implemented (requires research API) |
| PostgreSQL table definition and separate FastAPI enrollment / submit / withdraw endpoints | Implemented but gated; no production deployment |
| Strict consent / 18+ / invite / version+SHA study release gates | Implemented, DISABLED |
| Unit tests and research CI job | Implemented, CI results require verification |
| Restricted pseudonymized CSV export | Implemented; run only in approved isolated environment |
| Ordinal EFA/CFA baseline R pipeline | Implemented scaffold, no participant data |
| Independent expert review and cognitive interviews | Expert evidence schema/checks implemented; humans have not performed reviews |
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
