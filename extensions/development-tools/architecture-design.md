# Program Kit operation exposure and application capabilities

Status: candidate review projection. The canonical source is
`architecture-design.json`; this document grants no implementation authority.

## Outcome

Application owners publish one exact host-neutral operation catalog. Generated
Console and API hosts expose catalog operations through independent Open Console
and OpenAPI bindings. The MCP bridge projects the same selected operations into
provider-neutral executable tools. Optional application-authored capabilities
then provide outcome guidance over exact operation and schema identities without
becoming a transport or changing application semantics.

Program Kit owns conformance, deterministic projection, acquisition, explicit
workspace lifecycle, provider adapters, and evidence. The application publisher
owns operation meaning, capability triggers and intake, workflow interpretation,
authority boundaries, stop conditions, and completion meaning.

## Technical shape

```text
Application-authored source
  OperationContractCatalog
    ├─ Console exposure binding ──> generated Console + host introspection
    ├─ OpenAPI exposure binding ──> generated API host
    └─ Development Tool selection ──> neutral MCP tools/list + tools/call

  Optional outcome capability bundle
    ├─ descriptor + triggers + readiness
    ├─ procedure + authority/stop/completion guidance
    ├─ exact operation/schema bindings
    └─ finite transitive knowledge closure

Program Kit CLI
  acquire/verify/store
  propose/accept
  initialize/refresh/update/status/remove
  render provider wrappers + one derived flat workspace catalog
```

An operation identity and revision remain stable when the same application
operation is exposed through Console, HTTP, or MCP. Exposure bindings own only
host syntax and invocation adaptation. They cannot redefine request, result,
failure, authority, or side-effect meaning.

## Generated Console introspection

Every generated Console host reserves a host-owned metadata route for:

- one canonical document over the complete operation catalog; or
- the same projection restricted to one exact operation identity/revision.

It may include exact identities, paths and aliases, summaries, examples,
inputs, options, constraints, schemas, result and failure meanings, authority,
side effects, cancellation, timeout, and concurrency facts when the catalog
contains them. It never composes application services, exposes secrets, or
invents domain meaning.

The reserved syntax is checked before generation. Any collision with an
application command, alias, or path is a deterministic design error. Human
`--help` and completion remain separate. MCP `tools/list` remains the primary
registered-agent discovery surface; Console introspection provides direct CLI,
offline, and diagnostic parity.

## MCP and registration authority

One stdio bridge supports both the current modern MCP discovery contract and
the legacy initialization contract, then exposes exact `tools/list` and
`tools/call` behavior. Direct single-operation use never requires a capability.

Registration is never automatic:

1. Program Kit deterministically builds a provider/workspace proposal.
2. The human reviews and accepts its exact digest.
3. Program Kit writes only the accepted project-scoped provider entry and its
   ownership evidence.
4. Provider trust or permission remains provider-owned.
5. Invocation is a later provider/user transition.

Registration, trust/permission, and invocation are independently observable and
reversible. No registration command starts a provider, server, or application.

## Application capability bundle

The bundle is optional. Its deterministic outer structure contains:

- publisher, application, package, operation-catalog, adapter, capability, and
  knowledge-closure identities and digests;
- one descriptor per outcome capability, including provider-native trigger
  descriptions and exact readiness requirements;
- one canonical procedure per capability, including intake, referenced
  operations/schemas, interpretation, human-decision points, authority
  boundaries, stop conditions, completion meaning, and optional explicit
  handoffs;
- exact resources and their transitive dependencies: descriptions, schemas,
  examples/templates, diagnostics/remediation, artifact interpretation,
  migrations, materializers, and scaffolders.

Capabilities represent meaningful outcomes, not a generated one-per-command
layer. A one-operation capability is valid when it adds meaningful intake,
interpretation, remediation, or a safety boundary. A capability may explicitly
hand off to another capability, but Program Kit does not create a workflow
state machine or infer the composition.

Program Kit proves integrity, compatibility, closure completeness, and exact
binding. Publisher attestation remains the authority for domain semantics.

## Acquisition and workspace lifecycle

One acquisition engine accepts explicit source kinds for public local
directories, zip files, NuGet packages, HTTPS artifacts, and GitHub release
artifacts. Carrier bytes normalize into one verified bundle and immutable
content-addressed store. Installation or acquisition activates nothing.

The shared capability lifecycle owns deterministic initialization proposal,
acceptance, per-bundle/provider locks, provider projections, one flat derived
workspace catalog, preflight, canonical reads, refresh, update, status, removal,
and pruning.

`refresh` and `update` are intentionally different:

- `refresh` discards and reconstructs derived catalog/provider bytes from the
  same verified bundle and valid ownership lock;
- `update` presents and accepts a new authoritative bundle version or digest;
- lock edits are integrity failures and are never adopted by refresh.

A filesystem owner can edit local bytes, but such edits become detectable and
unusable. Refresh repairs only derived state; it cannot convert tampering or new
publisher bytes into authority.

## Discovery and readiness

Normal activation uses each provider's native tool and capability selection.
Program Kit does not implement a confidence scorer or intent router.

Program Kit additionally generates one on-demand `discover-capabilities`
capability over a single flat workspace catalog grouped by publisher and
application. It helps broad “what can I do?” requests without creating nested
indexes. Ambiguity remains a provider/user clarification problem.

Two independent readiness observations are retained:

- `tool-ready`: the exact operation projection can be safely proposed or is
  registered for MCP use;
- `agent-guided`: the application-owned outcome capability and its complete
  closure, provider projection, and required operation bindings preflight.

The labels remain candidate product vocabulary, not permission or execution
authority.

## Program Kit dogfood

Program Kit's built-in consumer capabilities become the reference application
bundle and pass through the same generic verifier, locks, provider projections,
catalog, refresh/update rules, and cold-session proofs. Only embedded delivery
may receive a narrowly documented bootstrap distinction.

The completed alpha-3 package-only consumer proof and feed handoff are existing
source truth to generalize, not parallel machinery to replace or duplicate.

Package-only consumers receive outcome parity for every supported consumer
operation without Program Kit source, assembly inspection, grep, unrelated test
fixtures, or remembered internal knowledge. Contributor architecture and
debugging remain source-attached and separately initialized.

## Static conformance

Disposition: `reuse-existing`.

The current Program Kit private C# gate remains selected for Program Kit-owned
implementation only. Static source and project/package invariants reuse it;
protocol, lifecycle, package-only, capability, authority, provider, and
cold-session behavior require executable tests and genuine provider-labelled
evidence. The completed Program Kit health-patching task is source truth and is
not changed or widened by this design.

## Deliberate exclusions

This design does not introduce one capability per command, a universal result
schema, `availableActions`, a next-action envelope, a workflow state machine,
Program Kit semantic approval, automatic registration or initialization,
self-permission, autonomous retry, nested indexes, or a model/tool loop.

No runtime, CLI, schemas, packages, providers, capabilities, catalogs, or locks
are implemented by this review set.
