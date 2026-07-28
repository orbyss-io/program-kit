# Program Kit consumer CLI journey completeness design

Artifact identity:
`pkid:design:program-kit:consumer-cli-journey-completeness@0.1.0-alpha.1`.

State: `ready-for-human-decision`.

## Intent

Make one exact installation of the `program-kit` .NET tool sufficient for a
clean consumer agent to initialize Program Kit, retrieve the complete canonical
capability and every referenced resource, discover and retrieve registered
schemas, understand every finite command, materialize a canonical C# gate
definition, and invoke the existing backed operations without a Program Kit
checkout or assembly reverse engineering.

This is an atomic consumer-unblocker outside the approved `PKAV-W010` through
`PKAV-W070` work-unit boundaries. It incorporates the consumer-delivery and
capability-refresh outcomes that overlap `PKAV-W050`; that overlap is explicit
and must not be implemented a second time or silently reported as two completed
work units.

## Current source truth and observed failures

- `Orbyss.ProgramKit.CommandLine` is already a self-contained `program-kit`
  .NET tool package, but it does not own the capability payload.
- Capability initialization requires `--program-kit-root`, reads canonical
  definitions from that source tree, and generated wrappers point back to it.
- The ownership lock retains only the most recently initialized provider even
  though wrappers for an earlier provider remain discoverable.
- There is no `capabilities read`, supporting-resource retrieval, or schema
  retrieval command.
- The CLI parser rejects no arguments and `--help`; missing options and
  positional arguments are learned one failure at a time. Successful
  initialization and bundle verification are silent.
- Registered schema modules are already loaded in the tool process for
  validation, but their exact bytes and finite catalog are not exposed.
- `csharp-gate validate-definition` requires semantic ordering and
  artifact-kind/null combinations that are not fully represented in its JSON
  Schema. Valid Program Kit analyzer package identities are not discoverable.
- User-authored UTF-8 JSON with a byte-order mark fails before semantic
  diagnostics, and there is no gate-definition materialization boundary that
  emits canonical BOM-free bytes.
- The reported JTest agent therefore searched DLL strings, guessed package
  identities and collection order, and iterated one opaque validation failure
  at a time.
- The already implemented Console generation CLI binding is present at source
  commit `00ab82b`, but the final package-only proof must demonstrate that the
  installed tool bytes, not source project references, reach it.

## Product boundary

The installed CLI owns consumer capability delivery. Program Kit contributor
authoring does not use CLI-returned product capabilities as governing guidance.

```text
consumer provider trigger wrapper
  -> program-kit capabilities read <capability-id> --workspace-root .
  -> exact CLI payload and workspace-lock verification
  -> complete canonical capability bytes
  -> exact CLI resource/schema/operation commands named by that capability
```

The provider wrapper owns discovery metadata only. Installation alone does not
initialize wrappers, start a capability, grant authority, approve a design, or
select a gate. The Program Kit source authoring marker makes consumer
initialize/read operations fail closed.

## Installed payload and one-source rule

The CLI tool package carries an exact, allow-listed payload built from the one
canonical repository source tree:

1. the capability-bundle manifest;
2. five distributable canonical capability definitions;
3. reviewed Codex and Claude adapter templates;
4. all capability supporting resources;
5. the finite registered schema resources already owned by Program Kit modules;
6. a machine-readable C# gate authoring catalog containing the current public
   analyzer selections and exact resource identities.

The existing CapabilityBundle project may remain an internal exact-byte pack
and verification artifact, but a consumer does not install it separately.
Packing must consume the canonical files directly and prove exact source,
bundle, and CLI-payload byte equality. Authoring markers, contributor
baselines, repository-only capabilities, history, indexes, private gate
implementation, and unlisted files are excluded.

## Public command contract

The finite command descriptors remain the single help/parse source. They gain
descriptions, usage names, allowed-value projections, and examples sufficient
to generate deterministic help.

| Invocation | Required behavior |
| --- | --- |
| `program-kit` | Concise first-use install/initialize guidance and the help exit contract. |
| `program-kit --help` | Complete finite top-level command catalog. |
| `program-kit <command-path> --help` | Exact positional arguments, required/optional options, allowed values, exit classes, and an example. |
| `program-kit capabilities initialize --provider <codex|claude> --workspace-root <dir>` | Transactional initialize/refresh from the installed payload; no `--program-kit-root`. |
| `program-kit capabilities read <capability-id> --workspace-root <dir>` | Emit only the complete canonical capability bytes on standard output after exact lock/payload/wrapper verification. |
| `program-kit capabilities read-resource <resource-id> --workspace-root <dir>` | Emit only one allow-listed supporting resource on standard output under the same verification boundary. |
| `program-kit schemas list --format <text|json>` | Emit the finite registered schema catalog, including identity, version, canonical URI, digest, and dependency identities. |
| `program-kit schemas read <schema-id>@<version> --output <file|->` | Emit one exact registered schema resource; never resolve a path, URI, assembly, or network resource supplied by the caller. |
| `program-kit csharp-gate describe-definition --format <text|json>` | Emit the gate-definition schema identities, finite enum values, semantic conditions, canonical collection keys, and exact supported Program Kit analyzer selections. |
| `program-kit csharp-gate materialize-definition <draft> --output <file>` | Accept one explicit human/agent-authored draft, diagnose the complete contract, and emit canonical BOM-free, stable-ordered definition bytes without inventing authority or semantic selections. |

Invalid finite values enumerate the allowed values. Positional-count errors show
the exact synopsis. Success messages for mutating/setup operations are short,
deterministic, and name the affected provider, wrapper counts, and lock path.
Commands whose primary result is file content keep result bytes on standard
output and diagnostics on standard error.

## Capability initialization, refresh, and retrieval

Initialization preflights the complete transaction before mutation. The lock
format records:

- lock format and exact Program Kit CLI/package version;
- bundle/content and manifest-format versions;
- payload-manifest digest;
- an ordinal provider map, not one last-provider field;
- for each capability and provider, canonical, adapter-template, generated
  wrapper, and output-path digests;
- supporting-resource digests and owned output paths.

Repeated initialization is byte-idempotent. Adding or refreshing one provider
preserves the other provider's owned wrappers. Human-modified or unowned paths
are refused without partial writes. Legacy single-provider locks migrate only
during explicit initialization and only after exact old ownership verifies.

Capability and resource reads verify the exact installed CLI version, payload
manifest, requested item, active provider lock entry, and owned wrapper bytes.
A global/tool-path version different from the workspace lock, a modified
wrapper, stale digest, unsupported ID, missing provider, authoring marker, or
unowned collision is a setup blocker. A read never repairs state.

Canonical capabilities are updated to name only CLI-addressable resource and
schema identities. Provider wrappers become thin installed-CLI retrieval
instructions and contain no source-tree pointer or copied procedure. The
design capability references the alpha design-flow contracts selected by the
approved version transition rather than the legacy high-major instances.

## Schema and resource discovery

Schema cataloging is projected from the same explicit schema-module
registrations used by validation. Each entry binds the exact package-owned
bytes and any registered `$ref` dependencies. Duplicate identities, versions,
URIs, or bytes fail tool composition. `schemas read` is offline and allow-list
only; a schema URI is metadata, never a network location.

Capabilities may retrieve non-schema supporting resources only through
`capabilities read-resource` and exact resource IDs in the capability payload
manifest. Supporting resources are inert and cannot be triggered as
capabilities.

## C# gate-definition authoring

The gate-definition contract advances from
`pkid:schema:program-kit:csharp-build-gate-definition@0.1.0-alpha.1` to
`@0.1.0-alpha.2`. The alpha.1 bytes remain immutable and an explicit,
deterministic migration sorts finite collections and preserves every semantic
value.

The alpha.2 schema and model agree on artifact selection:

- `local-non-packable-project` requires an exact non-null repository-relative
  project path, a null package, and `isPackable: false`;
- `analyzer-package` requires a null project path, one exact package reference,
  and `isPackable: true`.

Semantic collection ordering is no longer a hidden validity precondition for a
draft. The materializer rejects duplicates, sorts every finite collection by
its documented canonical key, performs schema and complete semantic validation,
and writes canonical UTF-8 without a BOM. It may ignore exactly one UTF-8 BOM
at the draft ingestion boundary; invalid encodings still fail.

The draft supplies all identities, versions, digests, ownership, rules,
profiles, activation choices, exceptions, suppressions, assurance, and human
authority values. The materializer cannot infer or approve them. The
description catalog publishes exact allowed enum values and canonical sort
keys plus the currently packaged Program Kit public-analyzer package identity,
NuGet ID/version, assembly name/digest, rule ownership, and compatibility
references. Schema, parse, and semantic diagnostics are aggregated where safe
and always include a stable ID, JSON path, violated rule, and expected shape or
allowed values.

## Compatibility and migration

- The coordinated product/package version remains the not-yet-published
  `0.1.0-alpha.2`; this work unit changes those candidate bytes before the
  first alpha.2 handoff and must not create two different delivered alpha.2
  archives.
- Existing alpha.1 package artifacts already handed out remain historical and
  are never overwritten in a cache or release location.
- Legacy capability locks remain readable only for explicit verified
  initialization migration. New reads require the new lock format.
- The legacy `--program-kit-root` consumer contract is removed. Source-run
  authoring/test invocations, if retained internally, are not consumer help.
- Existing backed operational commands retain their names and semantics.
- Gate-definition alpha.1 remains readable/migratable; canonical new output is
  alpha.2.
- The exact design capability and wrappers change digest, so the capability
  bundle/payload manifest and refresh tests must change together.

## Authority and failure behavior

- No command starts work, approves a design/gate, invents a human decision, or
  grants authority.
- No retrieval command scans the current directory, source checkout,
  assemblies, package feeds, user profile, or network.
- No setup command overwrites modified or unowned files or leaves lock/wrapper
  state partially updated.
- No schema command accepts an arbitrary filesystem path or URI as a resource
  identity.
- No gate materializer fabricates package selections, repository facts,
  identities, digests, exceptions, or approval evidence.
- Tool version, payload, lock, wrapper, schema, and resource drift fail closed
  with actionable setup diagnostics.

## Static conformance disposition

Disposition: `reuse-existing`.

This design references the repository-scoped Program Kit gate:
`pkid:policy:program-kit:csharp-source-quality-gate@1.10.0` with digest
`sha256:e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1`,
activated by
`pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`
with digest
`sha256:bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b`.

The gate is established once for the Program Kit repository. This review set
does not recreate a gate requirement per design; it records the existing
repository binding because the changed Program Kit C# source is inside its
scope.

## Acceptance

1. Pack and inspect the CLI: exact allow-listed capability payload and schema
   resources are present; authoring/private/unlisted bytes are absent.
2. Install the CLI from only a bounded local alpha.2 package feed into an
   isolated tool path and NuGet cache with no Program Kit checkout, submodule,
   CapabilityBundle installation, project reference, or source capability
   path.
3. Prove no-argument, top-level help, command help, allowed-value diagnostics,
   deterministic success output, standard-output result bytes, standard-error
   diagnostics, and stable exit classes.
4. Initialize Codex, Claude, both providers, and repeated refresh; prove exact
   thin wrappers, multi-provider ownership, idempotence, legacy migration,
   modified/unowned refusal, and transactional interruption.
5. Read all five capabilities and every supporting resource at exact packaged
   bytes; prove stale CLI/lock/payload/wrapper and unsupported IDs fail closed.
6. List/read every registered schema, resolve all registered dependency
   identities, and prove exact package-owned bytes without network access.
7. Reproduce the JTest gate-authoring scenario without DLL/string/source-tree
   inspection: discover the exact schema and analyzer identity, ingest a BOM
   and unordered draft, report all invalid fields together, materialize
   canonical bytes, and validate them successfully.
8. Prove the alpha.1 gate schema remains byte-immutable and the alpha.1-to-
   alpha.2 migration is deterministic, idempotent, and value preserving.
9. Run a real package-installed Console `generate-host` operation and verify
   the integrity-sealed generated host, proving the Console binding is in the
   delivered CLI bytes.
10. Pass the mandatory solution build, all unit tests, routine conformance,
    exhaustive repository gate, capability payload checks, and cold-consumer
    proof.
11. Build one final flat-feed ZIP containing the exact alpha.2 first-party
    package closure, checksum/manifest evidence, and a JTest retry prompt.

## Deliberately outside this amendment

- Actual GitHub Release creation or the queued GitHub Actions release pipeline.
- NuGet.org, GitHub Packages, Azure Artifacts, or other feed publication.
- Remaining routing, approval-materialization, contributor-bootstrap, nested
  gate handback, release-cycle, and general health-patch findings.
- JTest repository mutation by this session.
- Automatic CLI update, version selection, signing, promotion, deployment,
  hooks, watchers, MCP bindings, or autonomous execution.
