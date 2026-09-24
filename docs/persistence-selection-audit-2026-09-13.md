# Persistence selection and application audit

Reviewed candidate: `cfb60cc3974c4f5458a9814fda0abf6ed39c04fe`, 2026-09-13.
Investigation only: no production implementation, consumer intake edits, or live agent runs.

Decision update: the user accepted all persistence recommendations on 2026-09-13.
Implementation remains pending; the shared engineering integration plan is in
`dotnet-engineering-integration-plan.md`.

## Findings

1. **The existing default is none, not PostgreSQL.**
   `extensions/program-kit-dotnet/references/persistence-profiles.md` explicitly defaults to
   `none`; `dotnet_sync.py` does too. The reference at historical commit `fd8cae6` has the same
   rule. PostgreSQL appearing in `default-adoption.md` is an example of explicit intake, not a
   database default. This does not establish what was agreed in every historical conversation.

2. **The latest intake did not surface the installed EF profile.**
   In the retained `program-kit-intake-wcr5qhp_` workspace, project-intent.md records the user's
   PostgreSQL choice but leaves a SQL-first versus ORM-backed adapter as a founding candidate.
   It does not name `ef-postgresql`. This is an early discovery gap. No bootstrap has run yet,
   so it is not evidence that the later architecture stage actually rejected EF.
   Choosing PostgreSQL alone does not logically choose an ORM; the kit needs an explicit
   default policy connecting those choices if that is the desired behavior.

3. **The coordinator cannot resolve the desired persistence profile from design authority.**
   `extensions/program-kit-governance/scripts/repository_sync.py:128` reads only
   `managed.get("persistenceProfile", "none")`. It does not use the loaded decision-register
   selections or feature ownership profiles for this value.
   A disposable, agent-free reproduction declaring `ef-postgresql` in both locations returned
   `none` for bootstrap, planning and setup. With existing managed state set to `ef-sqlite`,
   upgrade returned `ef-sqlite` even though those declarations still named PostgreSQL.
   These minimal documents probe the resolver; they are not approved consumer artifacts.
   Preserving installed state during upgrade is appropriate until a change is approved, but
   the missing desired-state comparison prevents an explicit discrepancy from being surfaced.

4. **Selection metadata is weaker than actual adoption.**
   The .NET adapter installs all three managed persistence props files. Its persistence argument
   is used for state/reporting; activation still requires the consumer-owned central import and
   references on the owning provider/test projects. The root template imports no persistence
   profile. `docs/profile-transition-audit-0.8.11.md` already identified that profile/import
   coherence was not validated. The current source retains that gap.
   `tests/validate_lifecycle_profiles.py::validate_sync_preservation` passes the profile directly
   and verifies preservation and recorded state. That does not test intake-to-adoption behavior.

5. **There is strong guidance, but incomplete phase enforcement.**
   The existing persistence reference already covers ownership, transactions, retry/ambiguous
   commit, concurrency, private provider types, migrations and real-provider tests.
   knowledge-inventory.json lists it for architecture, planning and delivery, but the current
   phase-obligations.json has no persistence-specific obligation or direct reference to it.
   General domain and .NET obligations supply partial coverage. An inventory entry does not
   prove that persistence requirements were presented or their runtime behavior tested.

6. **The live fixture has a separate service integration gap.**
   `tests/live/v2/lending_host.py::PublishedLendingHost` provisions a Foundation container,
   data directory and settings/package mounts. It does not establish a PostgreSQL service,
   isolated connection handoff or database lifecycle. A filesystem persistence contract does
   not adequately describe externally stored durable state. This is not evidence PostgreSQL
   is incompatible with Foundation. Review the service boundary before calling this a small fix.

## Research and resulting recommendations

- EF Core already makes a supported relational `SaveChanges` atomic. Keep that default;
  require explicit transactions only when the operation spans additional database work.
  It does not automatically protect a preceding business read/check from competing requests.
  [EF transactions](https://learn.microsoft.com/en-us/ef/core/saving/transactions).
- Adopt Npgsql's provider execution strategy for transient failures, with bounded policy and
  cancellation. Avoid inventing a broad catch-and-retry loop. Explicit transactions must be
  replayed as a complete unit through the execution strategy; ambiguous commits need stable
  identity or success verification. Do not repeat external effects inside a replayable unit.
  [Npgsql strategy](https://www.npgsql.org/efcore/misc/other.html),
  [EF connection resiliency](https://learn.microsoft.com/en-us/ef/core/miscellaneous/connection-resiliency).
- Require a feature-specific concurrency design and real contention test. PostgreSQL's default
  Read Committed does not establish every multi-step business invariant. Select constraints,
  conditional writes, concurrency tokens, locking or stronger isolation according to the
  invariant. Serializable failures require whole-transaction retry; do not make Serializable
  universal without evidence.
  [PostgreSQL isolation](https://www.postgresql.org/docs/18/transaction-iso.html),
  [EF concurrency](https://learn.microsoft.com/en-us/ef/core/saving/concurrency).
- Database retry and request idempotency solve different problems. For replayable commands,
  bind stable operation identity to the accepted input and durable outcome, and enforce
  uniqueness transactionally. Product semantics determine whether changed input conflicts,
  what a replay returns and how long identity must remain valid.
- Where state changes require asynchronous effects, adopt a transactional outbox with
  idempotent delivery/consumption. An outbox can publish duplicates; it is not a general
  exactly-once guarantee. For this fixture's same-database sink, a deduplicated durable work
  record and receipt can satisfy the contract without introducing a broker or universal bus.
  [AWS transactional outbox guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html).
- Retain controlled migration artifacts and explicit application ownership; do not infer
  production migration permission from startup. Keep real PostgreSQL testing for SQL,
  isolation, constraints, migrations and recovery. SQLite/InMemory cannot establish those.
  [EF migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying),
  [EF testing strategy](https://learn.microsoft.com/en-us/ef/core/testing/choosing-a-testing-strategy).

These sources support the mechanisms and their limits. They do not establish PostgreSQL as
the universally best database. PostgreSQL plus EF/Npgsql as the preferred server-relational
.NET stack is a proposed Program Kit product default. Exact installed package pins were
inspected, not independently restored or revalidated for release availability in this audit.

## Proposed integrated correction

Extend existing default-adoption, persistence reference, stage projection and sync authority:

1. No durable-store requirement means no provider. For a .NET capability needing server-based
   relational persistence without an explicit alternative, propose EF Core/Npgsql/PostgreSQL
   as the inherited default. Explicit PostgreSQL should surface `ef-postgresql` immediately.
   Existing stores, embedded requirements and reviewed alternative adapters remain supported.
2. Separate proposed selection, accepted design, materialized imports/references and verified
   behavior. Intake selection must not install packages or claim runtime compatibility.
   Before admission is complete, retain the proposed profile with explicit outstanding work;
   do not lose it by resolving to none.
3. Bind profiles per data-owning capability/provider. The current single repository scalar
   cannot adequately represent different legitimate providers owned by different capabilities.
   Reconcile shared EF package versions where multiple provider imports would duplicate pins.
4. Use the existing coordinator for first setup and upgrade. Compare accepted selection with
   imports, package assignments and installed state; surface drift, preserve consumer changes
   and require explicit migration authority for provider changes. An upgrade never migrates
   data merely because a selection string changes.
5. Project only the applicable persistence knowledge into intake/architecture/planning stages.
   Supply existing defaults and tested framework mechanisms; ask the user about business
   invariants, replay meaning and operational requirements that actually remain undecided.
6. Add conditional persistence obligations with proof for adoption, real shell resolution,
   transaction/concurrency/replay behavior, migrations and recovery. Preserve proportional
   nonapplicability for features without those concerns. Reusable examples must exercise
   framework mechanisms and fit domain-owned ports, not create a second generic ORM layer.
7. Add a reviewed service integration contract for fixture provisioning, connection delivery,
   isolation, app/database restart distinctions and cleanup. Preserve fixed business oracles.

Deterministic acceptance must cover: no persistence; default and explicit PostgreSQL; explicit
alternative; pending admission; existing consumer provider; conflicting pins/imports; different
capability owners; fresh setup; repeated sync; upgrade preservation; rejected unapproved provider
switch; real provider activation; contention; rollback; replay/conflicting identity; ambiguous
commit; notification recovery and controlled migration. The paid trial remains separately
authorized after the corrected path is ready.
