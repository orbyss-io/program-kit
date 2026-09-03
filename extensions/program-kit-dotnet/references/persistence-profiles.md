# Governed .NET persistence profiles

Persistence is admitted per domain capability and data owner; it is not inferred from a PostgreSQL
readiness probe or from the presence of a provider props file. The consuming repository selects
exactly one profile for an owning provider package by importing the matching managed props
file from consumer-owned `Directory.Packages.props` and adding package references only to that
provider and its real-provider test project. `none` is the default.

| Profile | Stable pins reviewed 2026-09-02 | Selection rule |
| --- | --- | --- |
| `ef-postgresql` | EF Core/Design 10.0.11; Npgsql EF 10.0.3; Testcontainers.PostgreSql 4.14.0 | PostgreSQL behavior, deployment, extensions, isolation, or operations are requirements. |
| `ef-sqlserver` | EF Core/Design/SqlServer 10.0.11; Testcontainers.MsSql 4.14.0 | SQL Server/Azure SQL behavior and operations are requirements. |
| `ef-sqlite` | EF Core/Design/Sqlite 10.0.11 | An embedded single-file relational store satisfies concurrency, durability, scale, and deployment constraints. It is never evidence for PostgreSQL or SQL Server. |

All profiles inherit the common managed `Microsoft.Extensions.DependencyInjection.Abstractions` and
`Microsoft.Extensions.Logging.Abstractions` 10.0.11 central pins. These pins converge older compatible
transitive requests from Testcontainers with net10 platform and observability projects; they do not
create new project dependency edges.

Dapper is not a built-in profile in this release. Program Kit does not yet provide a sufficiently
complete governed mapping, migrations, transaction, authorization-query, and real-provider test
contract for it; selecting it requires an Accepted ADR and an explicit profile extension.

## Admission record

Before plan completion, record all of the following in the feature plan and artifact-ownership
manifest. Unresolved answers block tasks and architecture-check:

1. The domain capability that owns the data and why persistence is required.
2. Aggregate, invariant, semantic atomic-operation, and transaction boundaries.
3. Consistency, concurrency-token, idempotency, retry, commit-ambiguity, and isolation semantics.
4. Provider-specific types, collation, case sensitivity, locking, indexing, generated-key, and failure behavior.
5. Schema/table/migration owner and the production deployment/rollback/forward policy.
6. Whether each read is domain behavior, an owned query, or a projection.
7. The authorization and tenant predicate enforced in the query, not only after materialization.
8. Data classification, secrets, retention/deletion, backup/recovery, and audit constraints.
9. Production topology, availability, connection limits, latency, and managed-service constraints.
10. Required real-provider Testcontainers evidence and explicitly non-substitutable behavior.

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
  Direct mapping of a persistence-ignorant Core POCO is permitted when provider concerns do not shape
  or escape through it.
- Put every EF mapping in `IEntityTypeConfiguration<T>` in the provider package. Map aggregate
  roots and owned/value objects deliberately: explicit stable keys, value converters/comparers,
  concurrency tokens, constraints, indexes, column types/lengths, and provider behavior.
- Register `DbContext` as scoped for a request/unit of work. It is not thread-safe. Pool only after
  verifying that no request/tenant state leaks through pooled instances and measuring benefit.
- Disable lazy-loading packages/proxies by default. Select only required columns, use projections
  for reads, default read-only queries to no tracking, pass cancellation tokens, and test query count
  or SQL shape where N+1/cartesian behavior is a risk.
- `SaveChanges` is normally one transaction. An explicit multi-operation transaction combined with
  retry execution strategies must execute the complete unit through that strategy and address
  ambiguous commit/idempotency. Do not hide transaction semantics inside a generic repository.
- Connection strings and secrets come from environment/secret providers. `shells.json` may contain
  feature activation and validated configuration names only, never credentials.
- Never run destructive or uncontrolled migrations at application startup. CI checks pending model
  changes. Deployment produces a reviewed migration bundle or provider-supported idempotent artifact,
  records its digest, applies it once under deployment control, and retains forward-fix/restore policy.
  SQLite does not claim idempotent-script support. Startup performs a read-only compatibility check.
- PostgreSQL and SQL Server tests use their exact Testcontainers module and pinned real server image.
  SQLite/InMemory cannot substitute for their SQL, transactions, constraints, concurrency, or types.

Microsoft's `DbContext` guidance defines it as a short-lived, non-thread-safe unit of work; EF Core's
query guidance warns that lazy loading readily creates N+1 round trips; and Microsoft's migrations
guidance recommends reviewed SQL/bundles and documents provider-specific idempotent limitations.
