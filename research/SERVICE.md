# Research API — independent, gated human-subjects study service

**Research fielding remains DISABLED. No participant collection is approved or enabled by this commit.**

This is an isolated FastAPI service rather than a modification of the existing Spring Boot
quiz endpoints, deliberately preventing anonymous quiz answers from being silently stored.
Study collection is enabled *only* for a separately expert-reviewed, explicitly
approved and SHA-256-pinned non-draft instrument. `draft-0.1` can only be previewed.
The research API is not hosted or deployed automatically by this repo.

## Developer preview (no DB, no responses)

```sh
python -m pip install -r research/requirements.txt
uvicorn research.service:app --host 127.0.0.1 --port 8090
curl http://127.0.0.1:8090/research-api/preview?form_index=0
python -m unittest discover -s research/tests -v
```

## Database and collection: release gates, not a ready production deployment

1. Obtain independent political science/psychometrics content review, documented cognitive interviews,
   privacy/legal review, and any ethics authorization required for the research.
2. Freeze and validate a new approved instrument JSON **with `research_status=APPROVED_FOR_FIELDING`**
   and a different version than draft; obtain a SHA-256 digest, independently verify provenance.
   The assignment engine accepts a versioned `pilot-*` schema, but **no approved pilot snapshot is shipped**. The current draft is intentionally ineligible for collection; freezing a real pilot requires expert and ethics review.
3. Provision a separate, private PostgreSQL with TLS, backups under retention control, restricted DB
   permissions, and run `research/sql/001_sessions.sql`. Never reuse public quiz DB or URLs.
4. Separate domain/API ingress; HTTPS only, invite-rate-limits, abuse controls and
   log redaction. Access bearer token must not appear in query strings, logs, cookies or web storage.
5. Configure these **server-only** env vars:
   `RESEARCH_COLLECTION_ENABLED`, `RESEARCH_DATABASE_URL`, `RESEARCH_STUDY_SEED`,
   `RESEARCH_TOKEN_PEPPER`, `RESEARCH_INVITE_CODE`, `RESEARCH_APPROVED_VERSION`,
   `RESEARCH_INSTRUMENT_SHA256`, `RESEARCH_INSTRUMENT_PATH`,
   `RESEARCH_ETHICS_REFERENCE`, `RESEARCH_CONSENT_VERSION`.
   Do not expose server secrets through Vite/Vercel `VITE_*` vars.
6. Independent reviewer verifies consent text, retention and withdrawal processes,
   **including backups and completed-session withdrawal**, before changing the fielding flag.

## API

- `GET /research-api/health`: safe operational health; collection status is not authorization.
- `GET /research-api/preview?form_index=0&lang=en`: public, read-only 120-question draft view.
- `POST /research-api/sessions?lang=en`: 201 for consented adult invitee only after fielding gate; issues one secret bearer and assigned form.
- `GET /research-api/session`: resumes with Authorization Bearer token.
- `POST /research-api/responses`: all 120 assigned answers + 5 archetypes atomically.
- `POST /research-api/withdraw`: deletes session and answers, including completed sessions.
- No public per-participant export endpoint; no integration with `POST /api/results`.
- Researcher-controlled offline export and R/Quarto analysis come next.

**Threat model caveats:** invite code is not strong participant identity or bot protection.
Provide reverse-proxy rate limits, controlled recruitment, explicit expiry and backup deletion;
the provided service is a development reference implementation, not a certified secure clinical
research platform. Raw political response exports are sensitive and should not be made public.
