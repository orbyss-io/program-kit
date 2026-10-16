# Physical effects of durable cross-resource work

An outbox records committed intent and delivery obligations. It does not create
an atomic transaction between a database row and an arbitrary file mutation.
Existing Program Kit guidance on operation identity, idempotency and uncertain
commit remains valid. No shipped implementation was attributed as the source of
the observed consumer race; this adds the missing physical-effect design detail.

At the design/task boundary, inventory the actual effects: publication, reads
whose observations authorize recovery, erase, replay, cleanup, staging, originals
and backups. Name their owners and the exact operation/resource identities.
Ordinary read-only inspection need not acquire a work lease. An observation used
to authorize a later effect does need an admitted current identity/fence and a
fresh conditional check when that effect occurs.

Require increasing fencing tokens at the physical resource. Checking a database
lease before a filesystem call leaves a pause between the check and effect.
Serialize admission of newer authority with the old actor's final identity,
fence, barrier, cancellation/deadline checks and mutation at that same resource
boundary. Stale erase is as important as stale publish. A higher counter issued
in a database is not yet resource-side revocation: physical admission is the
linearization boundary. Keep slow input/staging outside a short guard where the
storage contract permits it, then validate again after input and guard waits.

The [bounded synthetic reference](examples/local-fencing/local_fencing.py) uses
committed SQLite work envelopes and a permanent local OS file guard. It supplies
no domain SQL schema, broker, paid worker, generic storage framework or distributed
transaction. Its effect identity includes one opaque resource, work, operation,
action, payload hash, committed increasing fence and deadline. Issuance commits
before returning a token; resource admission binds the exact envelope. Counter
overflow, conflicting reuse, missing/corrupt authority and a different resource
identity fail. A different work identity cannot reset the high-water mark.

Publication writes only its verified owned staging file through atomic replacement
while holding the resource guard. Erase persists removal protection before unlink
under that same guard. All later publication for that logical resource is denied,
even with a higher issued fence. An older admitted-but-paused remover cannot erase
a newer admitted publication. A new logical resource needs a new root and identity;
the reference cannot reprovision a prior root or remove its authority files.

Effect intent is persisted before mutation; completion in the resource and work
store are separate facts. A process can crash between them. An unresolved intent
blocks a new mutation until an admitted recovery operation observes the actual
physical hash and retained intent. Recovery binds that observation to its current
fence, checks it again under the guard, and records observed completion or an
observed not-applied state. A conflict remains uncertain. It does not blindly
repeat publication/removal or claim that a lost response proves rollback.
Exact completed replay verifies actual state, performs no new file effect and
still requires unexpired current authority, including denial at deadline equality.

The reference never retires its high-water/barrier metadata. Its finite journal
refuses new admissions when full. A TTL, completed row or missing content cannot
prove all old workers, staging, originals, replay sources or backups are gone.
Erasing the published payload does not erase owned staging or historical metadata;
only the exact attempt may clean its own staging. A production retention/privacy
decision must cover those remaining inputs and justify any eventual retirement.

Run `python tests/validate_local_fencing.py` for the required named synthetic cases.
They use actual processes and observed guard contention, paused producer/remover
interleavings, exact-fence cancellation, expiry after waits, deadline equality,
replay, real process restart, corruption, overflow, retained barriers and deliberate
process exits after admission, intent, effect and resource completion. Work status
and physical state are inspected separately. Evidence records source hashes,
actual platform/storage, child exit results and both streams under unique
`artifacts/local-fencing` runs. Missing, substituted or skipped required cases fail.

The contract is for cooperating processes on the actual local storage tested.
Windows uses the permanent file's native byte lock; POSIX uses `flock`. Linux CI
must qualify its actual mount before a Linux result is claimed. This does not
qualify SMB/NFS, shared volumes, multi-host operation or an object store. All actors
must obey the protocol; local hostile writers/administrators are outside scope.
Wall-clock deadline checks assume a suitable local clock; they are cooperative
checks before/after waits and immediately before effects, not cancellation of an
in-flight OS mutation. Fences protect against newer admitted authority independently
of an older actor's clock. File flush/rename and the tested abrupt process exits
are process-crash evidence, not power-loss durability proof. An OS/storage failure
or unobserved effect remains unavailable/uncertain; no cleanup success, new paid
dispatch or consumer acceptance follows from it.
Restoring or rolling back authority/issuer files from backup is unsupported; safe
recovery would need independently retained trusted high-water evidence and the
complete original/staging/replay inventory before enabling effects again.

Background: [resource-side fencing](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html),
[transactional outbox boundary](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html).
