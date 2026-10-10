-- Research schema only. Run as a dedicated least-privileged PostgreSQL role.
-- Never run against the production quiz without a reviewed, isolated deployment.
CREATE SEQUENCE IF NOT EXISTS research_form_index_seq START WITH 1 INCREMENT BY 1;

CREATE TABLE IF NOT EXISTS research_sessions (
  token_hash CHAR(64) PRIMARY KEY,
  instrument_version TEXT NOT NULL,
  consent_version TEXT NOT NULL,
  ethics_reference TEXT NOT NULL,
  form_index BIGINT NOT NULL UNIQUE,
  language TEXT NOT NULL CHECK (language IN ('pt','en')),
  assigned_ids TEXT[] NOT NULL CHECK (cardinality(assigned_ids) = 120),
  consented_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '30 days'),
  answers JSONB,
  archetype_answers JSONB,
  completed_at TIMESTAMPTZ,
  CONSTRAINT research_completed_consistency CHECK
    ((completed_at IS NULL AND answers IS NULL AND archetype_answers IS NULL)
     OR (completed_at IS NOT NULL AND answers IS NOT NULL AND archetype_answers IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS research_sessions_expiry
  ON research_sessions (expires_at);
-- Administrators must schedule: DELETE FROM research_sessions WHERE expires_at < now();
-- Backups, logs, exports and replicas need a corresponding retention/deletion policy.
