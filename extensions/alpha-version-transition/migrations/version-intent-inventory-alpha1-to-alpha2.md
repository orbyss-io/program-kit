# Version-intent inventory alpha.1 to alpha.2 migration

The migration is deterministic source guidance. For every alpha.1 inventory
entry, the maintainer supplies the exact JSON Pointer that identifies the
classified value within the already digest-bound source file. The migration
copies every existing field unchanged and inserts that pointer as
`sourceLocator`.

An already-alpha owned revision may then use `retain-owned-revision` only when
its value is exactly `0.1.0-alpha.N` and `N` equals its recorded
`ownedRevisionOrdinal`. Stable-looking owned values continue to use
`migrate-owned-revision`. No product, external, historical-evidence, or fixture
classification changes during migration.

The migration rejects a missing or invalid JSON Pointer, duplicate
source-path-plus-locator key, changed source digest, or an owned disposition
that does not match the exact current version.
