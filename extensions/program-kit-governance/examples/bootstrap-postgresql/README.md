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

The row-lock case uses independent transactions and `SELECT ... FOR UPDATE` under
ReadCommitted. It requires SQLSTATE 55P03 while another transaction holds the row,
then proves rollback releases the lock without retaining the uncommitted write.
EF's default Npgsql execution strategy may wrap that PostgresException in an
InvalidOperationException. Only the direct or directly wrapped 55P03 at the contended
query counts as expected rejection. Positive and negative classification cases reject
unrelated SQLSTATEs, bare InvalidOperationException and non-provider timeouts.
Failures retain inner exceptions in JUnit and bounded, password-redacted stderr.
These mechanism cases do not choose a consumer's locking policy or prove its business rules.

EnsureCreated is confined to this newly created synthetic database. Consumer migration,
retry/idempotency, authorization, schema and production admission remain their existing
feature/delivery obligations. No consumer application files or database are changed.
