-- Independent fixture deployment authority. Runtime never creates/updates product schema.
CREATE SCHEMA evidence;
CREATE TABLE evidence.entries (
  identity text PRIMARY KEY,
  owner text NOT NULL,
  packet jsonb NOT NULL,
  accepted boolean NOT NULL,
  revision integer NOT NULL
);
-- Runtime is deliberately a different, non-administrator identity.
CREATE ROLE evidence_runtime LOGIN PASSWORD 'fictional-fixture-only';
GRANT CONNECT ON DATABASE lending TO evidence_runtime;
GRANT USAGE ON SCHEMA evidence TO evidence_runtime;
GRANT SELECT, INSERT, UPDATE ON evidence.entries TO evidence_runtime;
