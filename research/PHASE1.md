# Phase 1: isolated PostgreSQL integration

## Local research preview

```sh
docker compose -f research/docker-compose.yml up --build -d
curl http://127.0.0.1:8090/research-api/health
curl http://127.0.0.1:8090/research-api/preview?lang=en
cd frontend && npm ci && npm run dev
# http://localhost:5173/research
```

The development database binds only to loopback on 5433. The API binds only to
loopback on 8090. All human-response collection routes remain **disabled**.
`docker compose down` preserves the local DB volume; `docker compose down -v`
removes the local dev volume and its contents. Never enable fielding with sample
development credentials or put sensitive data in the Compose database.

## Actual PostgreSQL lifecycle tests

The CI research job starts a **fresh ephemeral PostgreSQL service** and runs
`research/integration_tests` with `RESEARCH_TEST_DATABASE_URL` pointing to a
loopback database named exactly `research_test` and with
`RESEARCH_INTEGRATION_TEST_ACKNOWLEDGE=ephemeral_only`. Test rows contain
synthetic answers and live in a uniquely named schema which is deleted after tests.

The mocked `pilot-1.0` instrument exists **only inside the test runner**; it is
never saved as an approved study instrument or deployed for fielding.
Runtime study authorization and SHA checks are not bypassed in production.

Before any real study: external ethics and instrument review, security testing,
operational rate limits, backup/retention review, audited production infrastructure
and human-subjects consent documentation remain mandatory.
