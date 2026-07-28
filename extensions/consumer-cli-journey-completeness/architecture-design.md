# Program Kit consumer CLI journey completeness design

Artifact identity:
`pkid:design:program-kit:consumer-cli-journey-completeness@0.1.0-alpha.1`.

State: `ready-for-human-decision`.

## Intent

Make one exact installation of the `program-kit` .NET tool sufficient for a
clean supported consumer agent to initialize Program Kit, determine exact
capability readiness, retrieve the complete canonical capability and its
complete product-owned knowledge closure, discover and retrieve registered
schemas, understand every finite command, materialize a canonical C# gate
definition, and invoke the existing backed operations without a Program Kit
checkout or assembly reverse engineering.

The Program Kit knowledge plane is read-only. Canonical capability, resource,
schema, catalog, migration, template, and diagnostic bytes are never copied
into the consumer workspace as editable source and no CLI operation edits
them. Consumer-owned inputs and generated application outputs remain writable
under their existing explicit operation contracts.

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
- The repository index mixes consumer, contributor-only, and unavailable
  capability identities. Five definitions are distributed, while the
  consumer-facing local-publish capability is marked available but excluded
  without a machine-readable role/readiness model.
- The CLI parser rejects no arguments and `--help`; missing options and
  positional arguments are learned one failure at a time. Successful
  initialization and bundle verification are silent.
- Stable Program Kit diagnostic catalogs exist in product code, but the CLI
  cannot explain a diagnostic's ownership, expected evidence, likely causes,
  remediation, or stop condition. Artifact validation likewise does not expose
  one read-only interpretation report that binds schema and operation owners.
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
- Provider wrapper descriptions do not form one tested precedence table, so an
  arbitrary provider may trigger the generic router for work already owned by
  a direct leaf capability.

## Product boundary

The installed CLI owns consumer capability delivery. Program Kit contributor
authoring does not use CLI-returned product capabilities as governing guidance.

```text
consumer provider trigger wrapper
  -> program-kit capabilities preflight <capability-id> --workspace-root .
  -> ready only after catalog + registration + closure freshness verification
  -> program-kit capabilities read <capability-id> --workspace-root .
  -> complete canonical capability bytes
  -> exact CLI resource/schema/operation commands named by that capability
```

The provider wrapper owns discovery metadata only. Installation alone does not
initialize wrappers, start a capability, grant authority, approve a design, or
select a gate. The Program Kit source authoring marker makes consumer
initialize/preflight/read operations fail closed.

Program Kit guarantees its product-owned instructions and resources. It does
not and cannot package facts owned by the selected consumer repository,
human-supplied authority/decisions, or external state. A capability must name
those as explicit inputs or missing evidence and fail closed; it must not rely
on an agent's remembered Program Kit behavior.

## Installed payload and one-source rule

The CLI tool package carries an exact, allow-listed, embedded payload built
from the one canonical repository source tree:

1. the capability-bundle manifest;
2. every `available` consumer-role canonical capability definition;
3. reviewed Codex and Claude adapter templates;
4. all capability supporting resources;
5. the finite registered schema resources already owned by Program Kit modules;
6. a machine-readable C# gate authoring catalog containing the current public
   analyzer selections and exact resource identities;
7. one versioned knowledge-closure manifest per consumer capability;
8. shared Program Kit troubleshooting guidance and exact diagnostic/
   remediation catalogs.

The current consumer set is exactly:

- `develop-software`;
- `design-software`;
- `design-csharp-build-gate`;
- `implement-software-plan`;
- `maintain-software`;
- `publish-dotnet-application-locally`.

`author-and-maintain-skills` is explicitly
`program-kit-contributor-only` and is unavailable from the consumer CLI
payload. Reserved release, qualification, and promotion flows remain
explicitly unavailable with a reason. A catalog entry cannot say `available`
for the consumer role unless its complete closure is packaged and retrievable.

The existing CapabilityBundle project may remain an internal exact-byte pack
and verification artifact, but a consumer does not install it separately.
Packing must consume the canonical files directly and prove exact source,
bundle, and CLI-payload byte equality. Authoring markers, contributor
baselines, history, repository indexes, private gate implementation, and
unlisted files are excluded.

## Read-only knowledge plane and trust boundary

Canonical knowledge is embedded in the installed product payload and exposed
only through read/preflight/describe operations. It is not initialized into
`.agent-capabilities`, `.codex`, `.claude`, or another consumer directory.
Only thin provider trigger wrappers and their ownership lock are written to
the workspace.

The CLI offers no create, update, export, repair, or delete operation for
canonical knowledge. Validation always uses the embedded canonical schema and
catalog bytes, never a consumer copy. If a consumer redirects standard output
to a file, that file is a non-authoritative consumer-owned copy and cannot
replace the embedded source.

Thin wrappers are necessarily provider files. A same-user process can
physically change them, but any change invalidates the recorded output digest
and all capability preflight/read operations refuse the workspace. The
payload's manifest and every item digest are verified before use.

No application can truthfully guarantee immutability against a malicious
process that has write access to the installed executable itself: modified
verification code could bypass its own checks. Protection against that actor
requires a read-only/sandboxed installation or operating-system policy outside
Program Kit. Program Kit's guaranteed boundary is: no knowledge-editing API,
no canonical workspace files, exact embedded bytes, tamper detection before
use, and fail-closed behavior for supported unmodified CLI binaries.

## Complete capability knowledge closure

Each consumer capability owns a `CapabilityKnowledgeClosure` entry containing:

- canonical definition identity/version/digest;
- repository role and provider trigger metadata;
- every supporting resource and template identity/digest;
- every schema identity/version/digest plus transitive `$ref` dependencies;
- every required command descriptor key and help-contract digest;
- required catalogs, examples, migration guidance, diagnostic/remediation
  catalogs, package/artifact selections, and compatibility evidence;
- the shared failure-resolution protocol when the capability can invoke build,
  validation, generation, refresh, package, or publication operations;
- explicit human inputs, consumer-repository evidence, and unavailable
  external evidence that cannot be packaged;
- the supported provider registrations and exact wrapper digests.

Pack-time and startup validation reject a missing, duplicate, stale, circular,
unregistered, or unlisted closure entry. Conformance parses every canonical
capability for Program Kit command, resource, schema, template, migration, and
relative-path references and proves that each resolves exactly once through
the declared closure. Relative source-tree references are forbidden in a
consumer capability.

`capabilities preflight` verifies catalog availability, repository role,
provider registration, workspace ownership, exact CLI version, wrapper bytes,
payload manifest, and the complete transitive knowledge closure. Its result is
exactly `ready`, `setup-required`, or `unavailable`, with structured reasons.
`capabilities read` succeeds only for `ready`; it never serves a partial
definition while a dependency is stale or missing.

## Public command contract

The finite command descriptors remain the single help/parse source. They gain
descriptions, usage names, allowed-value projections, and examples sufficient
to generate deterministic help.

| Invocation | Required behavior |
| --- | --- |
| `program-kit` | Concise first-use install/initialize guidance and the help exit contract. |
| `program-kit --help` | Complete finite top-level command catalog. |
| `program-kit <command-path> --help` | Exact positional arguments, required/optional options, allowed values, exit classes, and an example. |
| `program-kit commands describe <command-key> --format <text|json>` | Emit the exact finite grammar, allowed values, purpose, authority, input/output, and diagnostic contract for one backed command. |
| `program-kit diagnostics explain <diagnostic-id> --format <text|json>` | Emit the exact owner, meaning, affected contract/path, expected evidence, likely Program Kit causes, bounded remediation, escalation/stop condition, and related command/schema identities. |
| `program-kit artifacts inspect <artifact> --format <text|json>` | Read one explicit artifact, identify its exact registered schema, validate it, and report its contract/command/capability owners without modifying or normalizing the file. |
| `program-kit capabilities initialize --provider <codex|claude> --workspace-root <dir>` | Transactional initialize/refresh from the installed payload; no `--program-kit-root`. |
| `program-kit capabilities catalog --workspace-root <dir> --format <text|json>` | Distinguish release availability, repository role, active-provider registration, complete-closure freshness, and setup blockers for every known capability ID. |
| `program-kit capabilities preflight <capability-id> --workspace-root <dir> --format <text|json>` | Return `ready`, `setup-required`, or `unavailable` only after the complete knowledge closure and active wrapper verify. |
| `program-kit capabilities read <capability-id> --workspace-root <dir>` | Emit only the complete canonical capability bytes on standard output after exact lock/payload/wrapper verification. |
| `program-kit capabilities read-resource <resource-id> --workspace-root <dir>` | Emit only one allow-listed supporting resource on standard output under the same verification boundary. |
| `program-kit schemas list --format <text|json>` | Emit the finite registered schema catalog, including identity, version, canonical URI, digest, and dependency identities. |
| `program-kit schemas read <schema-id>@<version>` | Emit one exact registered schema resource to standard output; never resolve a path, URI, assembly, or network resource supplied by the caller. |
| `program-kit csharp-gate describe-definition --format <text|json>` | Emit the gate-definition schema identities, finite enum values, semantic conditions, canonical collection keys, and exact supported Program Kit analyzer selections. |
| `program-kit csharp-gate materialize-definition <draft> --output <file>` | Accept one explicit human/agent-authored draft, diagnose the complete contract, and emit canonical BOM-free, stable-ordered definition bytes without inventing authority or semantic selections. |

Invalid finite values enumerate the allowed values. Positional-count errors show
the exact synopsis. Success messages for mutating/setup operations are short,
deterministic, and name the affected provider, wrapper counts, and lock path.
Commands whose primary result is file content keep result bytes on standard
output and diagnostics on standard error.

## Failure resolution and interpretation

Every capability that may encounter validation, build, generation, refresh,
package, or publication failures includes the same exact troubleshooting
resource in its knowledge closure. Its mandatory sequence is:

1. retain the failing command, exact arguments with secrets redacted, exit
   class, diagnostic IDs, and artifact identities;
2. run `commands describe` for the backed command;
3. run `diagnostics explain` for every Program Kit diagnostic;
4. run `artifacts inspect` and retrieve the exact schema/resources for affected
   Program Kit artifacts;
5. distinguish Program Kit ownership from consumer repository, C# compiler,
   .NET SDK, NuGet, operating-system, and external-provider ownership;
6. apply only remediation authorized by the active capability and human
   request; otherwise report the missing evidence or escalation.

Diagnostic explanation is a finite registered catalog, not generated prose.
For Program Kit-owned IDs it binds exact remediation and stop conditions. For
known external families such as compiler or NuGet errors it identifies the
external owner and required evidence without pretending Program Kit owns all
possible error meanings. Unknown IDs return `unregistered-external` and no
invented remediation.

Artifact inspection is read-only. It uses the embedded schema selected from the
artifact's declared identity, reports all safely discoverable schema and
semantic diagnostics, and names the relevant command/capability closure. It
does not edit, normalize, migrate, repair, or approve the artifact.

This closes Program Kit product knowledge, not arbitrary application knowledge.
Consumer source, selected dependencies, machine state, and human decisions
remain explicit inputs. A capability that cannot resolve a failure from its
packaged closure plus those supplied inputs must stop and report what is
missing.

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
manifest, requested item's complete closure, active provider lock entry, and
owned wrapper bytes.
A global/tool-path version different from the workspace lock, a modified
wrapper, stale digest, unsupported ID, missing provider, authoring marker, or
unowned collision is a setup blocker. A read never repairs state.

Canonical capabilities are updated to name only CLI-addressable resource and
schema identities. Provider wrappers become thin installed-CLI retrieval
instructions, preflight before read, and contain no source-tree pointer or
copied procedure. The
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

## Provider discovery and invocation timing

Program Kit can mechanically guarantee closure and readiness after a supported
wrapper is selected. It cannot force an arbitrary AI provider to honor
front-matter trigger metadata. The supported contract is therefore limited to
the reviewed Codex and Claude adapters and is backed by fresh-session scenario
tests.

The canonical precedence table is:

| Human intent | Entry |
| --- | --- |
| Read, explain, review, diagnose, report, or status only | Ordinary read-only work; no development capability. |
| Explicit bounded compatible product change | `maintain-software`. |
| Explicit design, plan, revision, or convergence | `design-software`. |
| Exact approved-plan implementation | `implement-software-plan`. |
| Explicit C# gate design after a human start | `design-csharp-build-gate`. |
| Explicit local publication of one generated .NET application | `publish-dotnet-application-locally`. |
| Vague development intent or an explicit routing question | `develop-software`. |
| Release, qualification, or promotion | Explicitly unavailable until their backed capabilities exist. |

Codex and Claude trigger descriptions are generated/validated against this
table. Cold-session conformance covers every row, overlapping wording,
post-completion new work, and next-day continuation. A provider mismatch cannot
make `preflight` ready because active registration is independently verified.

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
- The exact consumer capabilities and wrappers change digest, so the capability
  bundle/payload manifest and refresh tests must change together.
- The consumer bundle advances from five to six definitions because the
  already available consumer-facing local-publish capability becomes
  role-correct and retrievable. Contributor authoring remains excluded.

## Authority and failure behavior

- No command starts work, approves a design/gate, invents a human decision, or
  grants authority.
- No retrieval command scans the current directory, source checkout,
  assemblies, package feeds, user profile, or network.
- No CLI command mutates canonical knowledge or treats a redirected consumer
  copy as authoritative.
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

1. Pack and inspect the CLI: all six consumer-role capability definitions,
   their complete closure manifests, exact allow-listed resources, and schema
   resources are embedded; contributor/private/unlisted bytes are absent.
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
5. Catalog and preflight every known capability. Read all six consumer
   capabilities and every transitive closure item at exact packaged bytes;
   prove contributor-only/unavailable IDs, partial closure, stale
   CLI/lock/payload/wrapper, and unsupported IDs fail closed.
6. List/read every registered schema, resolve all registered dependency
   identities, and prove exact package-owned bytes without network access.
7. For every registered Program Kit diagnostic, explain exact ownership,
   evidence, bounded remediation, related command/schema, and stop condition.
   Prove external/unknown IDs never receive invented Program Kit remediation.
8. Inspect representative valid, invalid, migrated, generated, and tampered
   Program Kit artifacts without changing their bytes; bind each report to its
   exact schema, commands, and capability closure.
9. Reproduce the JTest gate-authoring scenario without DLL/string/source-tree
   inspection: discover the exact schema and analyzer identity, ingest a BOM
   and unordered draft, report all invalid fields together, materialize
   canonical bytes, and validate them successfully.
10. Prove the alpha.1 gate schema remains byte-immutable and the alpha.1-to-
   alpha.2 migration is deterministic, idempotent, and value preserving.
11. Run a real package-installed Console `generate-host` operation and verify
   the integrity-sealed generated host, proving the Console binding is in the
   delivered CLI bytes.
12. Pass the mandatory solution build, all unit tests, routine conformance,
    exhaustive repository gate, capability payload checks, and cold-consumer
    proof.
13. Build one final flat-feed ZIP containing the exact alpha.2 first-party
    package closure, checksum/manifest evidence, and a JTest retry prompt.
14. Prove knowledge-plane mutation attempts have no CLI surface, canonical
    bytes never appear in the consumer workspace, redirected copies cannot
    influence validation/read results, and wrapper modification makes every
    affected preflight/read fail.
15. Run fresh Codex and Claude trigger scenarios for every precedence-table
    row and prove direct leaf intents do not route through the generic router.

## Deliberately outside this amendment

- Actual GitHub Release creation or the queued GitHub Actions release pipeline.
- NuGet.org, GitHub Packages, Azure Artifacts, or other feed publication.
- Routing findings beyond the exact supported-provider precedence/readiness
  table, plus approval-materialization, contributor-bootstrap, nested gate
  handback, release-cycle, and general health-patch findings.
- JTest repository mutation by this session.
- Automatic CLI update, version selection, signing, promotion, deployment,
  hooks, watchers, MCP bindings, or autonomous execution.
