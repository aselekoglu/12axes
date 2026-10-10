# Phase 1 operations and safeguards

The research API is **NOT approved for live political-opinion collection**.

## Application controls
- Every `/research-api/*` response gets `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex` and `nosniff`.
- The independent FastAPI service has a bounded, in-memory per-peer sliding-window limiter: 12 enrollments/minute, 60 participant requests/minute, and 120 preview or health requests/minute. `Content-Length > 64 KiB` is rejected. Limits apply to each process, so multiple workers, reverse proxies, and chunked requests **must** also be protected at ingress; these measures do NOT make an internet deployment secure by themselves.
- Do not trust `X-Forwarded-For` from clients. Reverse proxy IP privacy, bot controls and TLS require a separate security review.
- Sessions use hashed, randomly generated bearer tokens and expire after 30 days by default. Tokens must be kept safe and are not included in URLs or client storage.

## Private aggregate operational report

In a study-authorized private environment only:
```bash
python3 -m research.monitoring --json
```
This reports only counts of assigned forms, completed forms, language groups and question coverage. No demographic inference, no individual responses, no public API.

## Retention cleanup

```bash
python3 -m research.retention
# Only with an approved deletion policy:
RESEARCH_RETENTION_DELETE_ACKNOWLEDGE=DELETE_EXPIRED_LOCAL_RECORDS \
  python3 -m research.retention --execute
```

The script deletes records from the active database only. **It cannot remove backups or earlier exports**. Verify backups, log redaction, retention intervals, restore procedures, reviewer access and audit trails before pilot launch.

## Real DB synthetic integration tests

See `PHASE1.md`. GitHub Actions provisions a disposable PostgreSQL database and verifies:
- rejected non-consent;
- valid synthetic enrollment and balanced assignment;
- malformed answers rejected without partial writes;
- complete answers stored, duplicate completion rejected;
- participant session recovery and withdrawal even after enrollment is disabled;
- aggregate counts and assigned-vs-answered coverage.
