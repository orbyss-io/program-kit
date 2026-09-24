# Bounded PostgreSQL compatibility

The renderer reads the selected owner and existing managed EF/Npgsql props, then
binds `persistence-runtimes.json` to a disposable loopback-only database. Shared sync
performs renew and locked restore; the recipe only builds with `--no-restore`.

Cases prove real write/read, expected-revision conflict rejection, transaction
rollback and retained state after database restart. Two separately loaded DbContexts
attempt the same revision; the stale context must raise DbUpdateConcurrencyException
and preserve the winner. This follows [EF concurrency](https://learn.microsoft.com/en-us/ef/core/saving/concurrency)
and [Npgsql's provider contract](https://www.npgsql.org/efcore/modeling/concurrency.html).
The application-managed token is synthetic; it selects no consumer token policy.

EnsureCreated is confined to this newly created synthetic database. Consumer migration,
retry/idempotency, authorization, schema and production admission remain their existing
feature/delivery obligations. No consumer application files or database are changed.
