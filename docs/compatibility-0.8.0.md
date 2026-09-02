# Program Kit 0.8.0 compatibility report

Program Kit 0.8.0 keeps the technology-neutral governance path and application-bundle schema version
1 compatible with existing consumers. The runtime package and host image version advances to
`0.8.0-preview.1` because host validation and readiness behavior changed.

## Automatic upgrade behavior

- Update `program-kit-bootstrap` before the `program-kit` bundle. The Spec Kit extension update owns
  only Program Kit hook entries; repeated installs preserve unrelated hooks and produce the same
  mandatory clarify/analyze ordering.
- Managed files update only when their recorded hash still matches. UTF-8 bootstrap installation is
  idempotent and patches installed Spec Kit Python entry points without changing their behavior.
- Existing schema-version-1 application manifests without `features` remain readable by the new host;
  newly produced bundles include the feature closure and are checked before activation.
- Technology-neutral repositories are not given .NET, web, database, Docker, or Node artifacts unless
  Accepted evidence selects those profiles and the sync command is explicitly run.

## Consumer review required

- `Directory.*`, `VERSION`, `shells.json`, and `hostsettings.json` are scaffold-once, consumer-owned
  files. Existing consumers must review any new root MSBuild import, feature activation, package
  identity, and route ownership instead of expecting synchronization to overwrite them.
- Existing SPA repositories must import the managed Vite adapter and translate its policy into the
  production static server or edge configuration. Exact identity/API origins and CSP exceptions are
  deployment decisions; HSTS belongs only at the production TLS terminator.
- OpenAPI enforcement needs an explicit first compatibility baseline. A stale generated document,
  missing/duplicate operation ID, unpinned `oasdiff`, or unbound breaking-change approval blocks the
  build rather than silently changing the contract.
- Persistence remains opt-in. Selecting SQL Server, PostgreSQL, or SQLite requires architecture
  evidence, feature-owned adapters, migration/rollback ownership, and provider-representative tests.
  No Dapper profile is advertised because this release does not ship an equally complete operational
  and testing contract for it.
- Enable PostgreSQL readiness only when the host owns that operational dependency and supply the
  connection through deployment configuration. Keep liveness independent of external services.
- Run the toolchain checker interactively before relying on its installation path. Declining approval,
  an unavailable version manager, or an offline installer fails with actionable evidence and makes no
  hidden system change.

## Conflicts and manual resolution

Synchronization stops when a consumer changed a Program Kit-managed path, when ownership evidence
assigns a managed path to feature work, or when a proposed structure delta lacks Accepted evidence.
Resolve the conflict deliberately and rerun `--check`; Program Kit does not overwrite either consumer
work or architecture/specification evidence.

The Program Kit maintenance repository is the only release target. Consumer repositories, including
PriceCalculator, are not modified or used as a source of truth for this release.
