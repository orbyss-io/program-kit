# Governed .NET persistence profiles

Persistence is admitted per domain capability and data owner; it is not inferred from a PostgreSQL
readiness probe or from the presence of a provider props file. The consuming repository selects
exactly one profile for an owning provider package by importing the matching managed props
file from consumer-owned `Directory.Packages.props` and adding package references only to that
provider and its real-provider test project. No durable-store requirement selects `none`. For a .NET
data owner requiring server-relational persistence without an explicit alternative, inherit
`ef-postgresql` (EF Core/Npgsql/PostgreSQL). This is Program Kit product policy, not a claim that one
database suits every workload. Explicit embedded, existing-store and custom choices take precedence.

| Profile | Stable pins reviewed 2026-09-02 | Selection rule |
| --- | --- | --- |
| `ef-postgresql` | EF Core/Design 10.0.11; Npgsql EF 10.0.3; Testcontainers.PostgreSql 4.14.0 | PostgreSQL behavior, deployment, extensions, isolation, or operations are requirements. |
| `ef-sqlserver` | EF Core/Design/SqlServer 10.0.11; Testcontainers.MsSql 4.14.0 | SQL Server/Azure SQL behavior and operations are requirements. |
| `ef-sqlite` | EF Core/Design/Sqlite 10.0.11 | An embedded single-file relational store satisfies concurrency, durability, scale, and deployment constraints. It is never evidence for PostgreSQL or SQL Server. |

The installed `persistence-runtimes.json` supplies the managed `ef-postgresql` local
server version/digest and primary source evidence. Bootstrap projects it together with
the package pins from the existing props into `provider_inputs.persistence_runtimes`.
Use maintained `ef-postgresql` compatibility for a retained external provider risk;
do not ask the consumer to select missing kit metadata or reconstruct a test service.
This disposable server is a test default, not a production deployment commitment.
An explicit alternative profile does not inherit PostgreSQL. SQL Server requires a
reviewed exact server image for its chosen edition/platform; SQLite has no server image.

All profiles inherit the common managed `Microsoft.Extensions.DependencyInjection.Abstractions` and
`Microsoft.Extensions.Logging.Abstractions` 10.0.11 central pins. These pins converge older compatible
transitive requests from Testcontainers with net10 platform and observability projects; they do not
create new project dependency edges.

Dapper is not a built-in profile in this release. Program Kit does not yet provide a sufficiently
complete governed mapping, migrations, transaction, authorization-query, and real-provider test
contract for it; selecting it requires an Accepted ADR and an explicit profile extension.

## Ordinary development decisions

For the supported Foundation BFF/Keycloak plus EF/PostgreSQL composition, reuse the
maintained provider setup/runner adapters and feature-owned lifecycle scaffolds. Before
application schema exists, readiness proves connectivity and selected generic behavior;
it establishes no application migration, transaction, ownership, conflict or replay outcome.
Synthetic provider probes are test-only and never a production feature selection. A change
to deployment/provider settings renews affected setup checks; application semantic changes
renew their owned real-provider checks. Preserve all ten application admission topics below.
There is no requirement to author generic provisioning/reporting infrastructure again or
to finish unrelated future storage work before an independent product operation.

For ordinary feature planning and task generation, record affected data owners, the retained
exact provider/profile, capability and project ownership, and the ten topics below in plan.md
or an existing ADR. Map the required behavior to concrete test and implementation tasks.
No new artifact-ownership, persistence admission, verification-plan or attributed review dossier
is required for tasks, architecture-check or ordinary implementation guidance. Preserve accepted
bootstrap decisions and installed pins; do not rewrite hash-approved intent to add feature detail.

Generate and save tasks before executing compatibility/admission prerequisites. If an input or
decision is unresolved, schedule its resolution with an owner and explicit dependency before
the affected implementation/proof task. Report material design conflicts through normal review;
do not fabricate approvals or evidence. Actual provider compatibility, authorization, data
protection and real-provider verification remain required before dependent work or completion.

Address all of the following in the feature plan and tasks. Unresolved answers become explicit
prerequisite tasks; they do not block saving tasks or reporting architecture-check findings:

1. The domain capability that owns the data and why persistence is required.
2. Aggregate, invariant, semantic atomic-operation, and transaction boundaries.
3. Consistency, concurrency-token, idempotency, retry, commit-ambiguity, and isolation semantics.
4. Provider-specific types, collation, case sensitivity, locking, indexing, generated-key, and failure behavior.
5. Schema/table/migration owner and the production deployment/rollback/forward policy.
6. Whether each read is domain behavior, an owned query, or a projection.
7. The authorization and tenant predicate enforced in the query, not only after materialization.
8. Data classification, secrets, retention/deletion, backup/recovery, and audit constraints.
9. Production topology, availability, connection limits, latency, and managed-service constraints.
10. Required real-provider evidence, its test provisioning owner and explicitly non-substitutable behavior.

## Architecture and implementation contract

- Core projects are POCO-only: no EF Core, provider, `DbContext`, migrations, DI, or vendor references.
- Core-owned interfaces state cohesive semantic capabilities. One interface may contain multiple
  naturally related operations, but split it when consumers, consistency, security, optionality,
  availability, lifecycle, or replacement differs. Do not introduce repositories, stores, units of
  work, generic CRUD, one-interface-per-method proliferation, or a solution-wide shared `DbContext`.
- One data owner declares its schema/table and migrations. Cross-owner writes require an Accepted
  transaction/integration decision rather than a shared context.
- Provider-specific persistence records never appear in Core, peer projects, transport contracts,
  or integration contracts. Map them to business-semantic domain/boundary models inside the provider.
  EF entities are separate provider-owned types. Direct mapping of Core POCOs is not permitted;
  storage representation and tracking/equality never shape the public domain model.
- Put every EF mapping in `IEntityTypeConfiguration<T>` in the provider package. Map aggregate
  roots and owned/value objects deliberately: explicit stable keys, value converters/comparers,
  concurrency tokens, constraints, indexes, column types/lengths, and provider behavior.
- Register `DbContext` as scoped for a request/unit of work. It is not thread-safe. Pool only after
  verifying that no request/tenant state leaks through pooled instances and measuring benefit.
- Independent units, parallel operations and long-lived callers use a nonpooled
  `IDbContextFactory<TContext>` with cancellation and caller-owned `await using` disposal. A mutation
  and receipt reconciliation own separate contexts; clearing tracking does not create a fresh unit.
  Keep one atomic transaction on one context. A single sequential request unit may use its scoped
  context unless the application chooses the stricter factory convention.
- Factories and provider configuration follow actual shell lifetimes. Own every factory-created unit
  inside a tracked `IShell.BeginScope` or equivalent shell lease, including initialization, background
  work and cleanup. Context disposal alone does not track the datasource. Test rejection outside a
  lease, cancellation/creation failure, active-unit drain and datasource disposal after units finish.
  A stable datasource owns connection pooling per shell/provider generation; context pooling is a
  separate decision. Do not rewrite connection strings per operation to select time budgets.
<!-- program-kit:decision-rule persistence-admission -->
- Native connection/command/lock/deadline options remain provider-owned typed validated configuration.
  Consumers own operation policy and map safe SQLSTATE plus named constraints to outcomes. Preserve
  commit uncertainty: cancellation cannot prove rollback. Verify independent contexts, replay races,
  actual provider state reset and redacted application diagnostics with real PostgreSQL.
- Disable lazy-loading packages/proxies by default. Select only required columns, use projections
  for reads, default read-only queries to no tracking, pass cancellation tokens, and test query count
  or SQL shape where N+1/cartesian behavior is a risk.
- `SaveChanges` is normally one transaction. An explicit multi-operation transaction combined with
  retry execution strategies must execute the complete unit through that strategy and address
  ambiguous commit/idempotency. Do not hide transaction semantics inside a generic repository.
- Keep external effects outside a retried database unit. Persist stable operation identity and its
  result atomically; conflicting reuse is a defined denial, not a new execution. For durable external
  delivery, use an admitted outbox and idempotent receiver. Retry the complete unit only when its
  replay/commit verification contract is safe; never promise exactly-once network delivery.
<!-- /program-kit:decision-rule -->
- Connection strings and secrets come from environment/secret providers. `shells.json` may contain
  feature activation and validated configuration names only, never credentials.
- Never run destructive or uncontrolled migrations at application startup. CI checks pending model
  changes. Deployment produces a reviewed migration bundle or provider-supported idempotent artifact,
  records its digest, applies it once under deployment control, and retains forward-fix/restore policy.
  SQLite does not claim idempotent-script support. Startup performs a read-only compatibility check.
- PostgreSQL and SQL Server tests use the pinned real server image. When tests own provisioning,
  use the exact Testcontainers module. A supervisor-owned service records `testProvisioning: supervisor`
  and supplies an isolated connection with the same real-provider contract; do not install an unused
  container client into a worker that cannot access Docker.
  SQLite/InMemory cannot substitute for their SQL, transactions, constraints, concurrency, or types.

Microsoft's `DbContext` guidance defines it as a short-lived, non-thread-safe unit of work; EF Core's
query guidance warns that lazy loading readily creates N+1 round trips; and Microsoft's migrations
guidance recommends reviewed SQL/bundles and documents provider-specific idempotent limitations.

## Existing structured setup and upgrade records

Keep the canonical data-owner records in `bootstrap-decisions.json.persistence`, validated by
`persistence.schema.json`. Each record names `owner`, `storage`, `profile` and `status`.
`storage: server-relational` plus `profile: auto` resolves to `ef-postgresql`; explicit PostgreSQL
must record that profile immediately. Never reinterpret an unresolved compatibility probe as `none`.
Use `proposed` until the assessment/architecture authority admits the design; `admitted` also needs
`capability`, `providerProject`, `testProjects`, `checkIds` and the evidence references below.
For consumers already using structured setup/upgrade records,
`artifact-ownership.json.persistenceOwners` names the owners affected by the feature; it does not
repeat their provider decisions. Different owners may select different providers. Existing
`artifact-ownership.json.persistenceAdmissions[<owner>]` records use the shared admission schema. That
record supplies status/capability/project/test/evidence details and cannot override owner, storage or
profile. Do not rewrite hash-approved bootstrap intent to add later implementation details. The
structured setup/upgrade adapter consumes those records when that workflow is explicitly selected;
ordinary task generation does not require or manufacture them. Upgrade preserves installed owners.

A later provider change uses `providerOverride: {"profile": "ef-sqlite", "authority": "<accepted ADR path>"}`
inside the feature admission. It preserves initial bootstrap intent and requires an Accepted transition
decision plus renewed migration/compatibility evidence. The installed effective choice remains visible
to subsequent sync and upgrade. Pending overrides preserve installed pins and tooling. Directly changing
`profile` in a feature admission is invalid; sync still never migrates data.

The `admission` object maps `ownership`, `atomicity`, `concurrency`, `providerSemantics`, `migrations`,
`queries`, `authorization`, `dataProtection`, `operations` and `realProviderTests` to nonempty lists of
repository-relative evidence files addressing the corresponding ten topics below. Existing plan/ADR
sections may share a file. Normal design/code review checks their substance. Existing `checkIds`
identify actual behavior cases; they do not require a new verification-plan dossier for ordinary
work. A schema-valid declaration is not runtime proof.

## Shared setup and upgrade

The repository coordinator resolves these records in bootstrap and planning before projects exist.
Incomplete structured admission is visible as proposed work and blocks that setup/upgrade
readiness claim, not ordinary task drafting. Engineering sync merges
admitted central pins into managed `eng/ProgramKit.Persistence.props`, deduplicating shared
EF versions and rejecting conflicts. The root consumer-owned `Directory.Packages.props` imports this
file. Existing custom files and direct provider imports are preserved; review the reported import or
duplicate-pin correction instead of overwriting consumer configuration. Provider and test project
package references remain owned implementation work and are checked against the selection. Restore
and compiled/real-provider evidence must still prove the evaluated dependency graph.

Upgrade uses the same resolver and coherence checks. Preserve existing profiles when no new choice
exists. Changing or removing an admitted provider needs an accepted `transitionAuthority` file;
sync never executes migrations, provisions production infrastructure or changes stored data. Custom
profiles supply approved exact `packages` and the same admission/evidence contract. Their package
sources and transitive compatibility remain governed by ordinary dependency admission.
Custom `packageAssignments` explicitly separates `provider` and `tests` package IDs from those pins.

For EF, sync also pins `dotnet-ef` to the selected Design version in the existing managed tool manifest.
Keep EF Design private to the provider. Make design-time context creation explicit, normally with
`IDesignTimeDbContextFactory<TContext>` in the provider, reading admitted configuration without starting
the published host. Record `dbContext` when tooling must disambiguate contexts. A factory is not a
second consumer host. Test fixture deployment may generate and apply a reviewed idempotent script
against its isolated service before host activation; normal deployment retains its own approval.

Primary evidence checked 2026-09-13: [EF transactions](https://learn.microsoft.com/ef/core/saving/transactions),
[execution strategies and commit ambiguity](https://learn.microsoft.com/ef/core/miscellaneous/connection-resiliency),
[optimistic concurrency](https://learn.microsoft.com/ef/core/saving/concurrency),
[migration deployment](https://learn.microsoft.com/ef/core/managing-schemas/migrations/applying),
[design-time context creation](https://learn.microsoft.com/ef/core/cli/dbcontext-creation),
[real-provider testing](https://learn.microsoft.com/ef/core/testing/choosing-a-testing-strategy),
[PostgreSQL isolation](https://www.postgresql.org/docs/18/transaction-iso.html), and
[transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html).
