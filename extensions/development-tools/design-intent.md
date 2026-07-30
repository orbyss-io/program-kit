# Program Kit operation exposure and application capabilities design intent

## Human-started outcome

Design reusable Program Kit infrastructure through which an application owner
can publish exact application operations and optional outcome guidance for AI
consumers.

The application owns one host-neutral operation catalog. Generated Console and
API hosts bind their own syntax to those operations. A provider-neutral MCP
bridge projects the same selected operations as executable tools. Optional
application-authored capabilities describe meaningful outcomes that use those
operations without depending on Console syntax, HTTP routes, or MCP tool names.

A fresh Codex or Claude Code session must be able to:

- invoke one registered operation directly without an outcome capability;
- select and follow an installed outcome capability from semantic intent;
- discover the complete flat workspace capability catalog on demand;
- refuse incomplete knowledge closure or changed bytes;
- distinguish registration, capability initialization, provider trust and
  permission, and invocation as separate authority transitions; and
- consume Program Kit's own supported consumer journeys from packages without
  a Program Kit source checkout.

This review set defines design and implementation planning only. It creates no
runtime, schema, package, MCP bridge, provider registration, provider mutation,
capability payload, permission, or autonomous behavior.

## Product and semantic ownership

An application product is customer-owned application/domain logic exposed
through one or more generated hosts. Program Kit may generate Console, API, or
other reviewed hosts, but the generated host does not become the semantic owner
of the application operation.

The application owner owns:

- operation identity and revision;
- request, result, diagnostic, authority, effect, timeout, cancellation,
  concurrency, and idempotency meaning;
- capability trigger, outcome, intake, procedure, stop conditions, completion,
  interpretation, remediation, and handoff meaning;
- the assertion that published application content is official.

Program Kit owns:

- contract schemas and deterministic validation;
- mechanical host and MCP projection;
- package and digest binding;
- proposal, ownership-lock, status, refresh, update, and removal mechanics;
- provider adapter rendering;
- knowledge-closure completeness checks; and
- conformance evidence.

Program Kit does not approve application semantics merely because bytes conform.

## Host-neutral operation catalog

`OperationContractCatalog` is the provider- and host-neutral source of exact
operation identity and contracts. Open Console owns Console paths, aliases,
arguments, options, completion, help, streams, and exit meanings. OpenAPI owns
HTTP paths, verbs, parameters, status codes, and transport schemas. Both exposure
documents bind exact operation identities and revisions from the same catalog.

Two exposures may bind the same operation only when the application owner
asserts exact semantic equivalence. Sharing a handler is not sufficient.

The catalog may include exact:

- identity, revision, summary, description, and examples;
- request, result, diagnostic, progress, and transitive schema references;
- authority, effect, resource, timeout, cancellation, concurrency, expected
  revision, and idempotency facts;
- compatibility, migration, deprecation, and related-operation references.

Application-owned outputs remain application-owned. Program Kit introduces no
universal application result, `availableActions`, next-action envelope, or
workflow state machine.

## Generated Console structured introspection

Every generated Console host reserves one host-owned structured introspection
surface:

```text
<application> --program-kit-introspect
<application> --program-kit-introspect=<exact-operation-revision>
```

The option has no short alias. It accepts only those exact argument shapes.
Introspection takes precedence over completion, help, and application-command
dispatch. Mixing it with other arguments returns a structured invalid-invocation
diagnostic without composing application services.

The full and selected forms use one versioned Program Kit JSON shape. The full
form contains the complete operation array; the selected form contains the same
shape restricted to one operation. Both include a deduplicated transitive
schema closure.

The introspection document is generated and embedded in the host assembly. It
uses exact catalog and Open Console facts only, exposes no secrets, performs no
network or configuration lookup, and composes no application services.
Application commands cannot claim the reserved option or aliases.

Human `--help` and completion remain independent. MCP `tools/list` remains the
primary registered-agent surface; Console introspection provides direct-CLI,
offline, and diagnostic parity. No API introspection endpoint is inferred.

## MCP projection and execution

One provider-neutral stdio bridge supports both:

- modern MCP `2026-07-28`, selected through per-request metadata and
  `server/discover`; and
- legacy MCP `2025-11-25`, selected through the `initialize` handshake.

Protocol selection is negotiated on the wire. The bridge has no startup
`--protocol` option.

The first adapter invokes an exact generated Console executable. A future HTTP
adapter may bind the same operation identities through OpenAPI, but requires a
separate reviewed adapter design. One registration selects exactly one
invocation binding per operation revision; ambiguity blocks until the human
selects one.

MCP tool names are:

```text
<operation-scope>__<operation-name>
```

Operation revision is omitted from the name and remains in metadata. When the
name exceeds 128 characters, use the first 95 characters followed by
`__sha256_` and the first 24 lowercase hexadecimal SHA-256 characters of the
base operation PKID. Any resulting duplicate is a hard conformance failure.

The initial portable schema profile requires object-root inputs with offline
closure and object-root structured results. It supports both protocol eras.
Modern-only arbitrary JSON results and optional MCP extensions are deferred.

The bridge returns exact application structured results and diagnostics. It
does not wrap them in a Program Kit application-result envelope, retry calls,
compose application services, call an AI provider, or form an autonomous loop.

Application-owned MCP server instructions may provide a bounded cross-tool
description. Program Kit appends the authority boundary. Outcome procedures
belong in capabilities, not server instructions.

## Registration authority

Registration is never automatic. Program Kit may build a deterministic
registration proposal, but provider/workspace mutation requires explicit
acceptance of its exact proposal digest.

Registration, provider trust/permission, and invocation are separate
transitions. Registration starts no provider, bridge, consumer process, or tool
call. Program Kit never grants provider trust or permission.

Codex receives only one owned project `mcp_servers.<registration-id>` entry in
`.codex/config.toml`. Claude Code receives only one owned project
`mcpServers.<registration-id>` entry in `.mcp.json`. Unrelated bytes are
preserved. User/global provider configuration is outside scope.

## Optional application capability bundle

An application owner may publish an inert `consumer-outcome-capabilities`
bundle beside its runtime/tool package. A focused tool can remain tool-only;
absence of a capability bundle is not a conformance failure.

Each capability represents a meaningful outcome. It may use one or many
operations. A one-operation capability is valid when it adds meaningful intake,
interpretation, remediation, or a safety boundary. There is no one-capability-
per-command rule.

Each capability has:

- an exact machine descriptor;
- one canonical provider-neutral procedure;
- exact operation bindings by identity and revision;
- a finite, digest-bound consumer knowledge closure;
- compatibility, migration, and handoff declarations; and
- thin Program Kit-rendered provider adapters.

The procedure refers to stable local binding names that resolve to operation
identities. It never embeds an MCP tool name, Console path, or HTTP route.
Changing the selected invocation adapter therefore does not rewrite the
application capability.

Declared handoffs are exact and acyclic. A handoff does not automatically invoke
the target, transfer authority, or bypass target preflight. Required capability
dependencies block readiness when missing; optional handoffs do not.

## Capability knowledge closure

A procedure is insufficient without all consumer knowledge required to perform
the outcome. Closure may include:

- exact operation descriptions and transitive request/result/diagnostic schemas;
- examples, templates, fixtures, and artifact interpretation;
- diagnostics, remediation, compatibility, and migrations;
- publisher, application, package, tool, Open Console, OpenAPI, capability, and
  provider-adapter identities and digests; and
- materializer or scaffolder identities where hand authoring is impractical.

Every resource node is typed, identified, versioned, digested, and reachable
from a declared root. Shared bundle resources may be referenced without byte
duplication. Source-relative pointers, undeclared network retrieval, assembly
inspection, source grep, and knowledge outside the installed closure are
forbidden.

Program Kit verifies identities, digests, graph completeness, compatibility,
and contract completeness. It does not judge the domain truth of the content.

## Acquisition and lifecycle

Two CLI planes share one capability engine.

`program-kit capability-bundles` acquires and inspects inert bytes:

```text
capability-bundles acquire local
capability-bundles acquire nuget
capability-bundles acquire https
capability-bundles acquire github-release
capability-bundles verify
capability-bundles inspect
capability-bundles prune
```

Source kind, carrier format (`directory`, `zip`, or `nupkg`), bundle kind,
logical identity, and content identity remain separate. Sources are exact:
local path plus format; NuGet package/version/source; GitHub repository/tag/
asset; or HTTPS URL plus expected digest. V1 supports public/anonymous
acquisition only. Floating versions, `latest`, ranges, query-string secrets,
and credential design are excluded.

Acquired bytes are normalized into a content-addressed workspace store under
`.program-kit/capability-bundles`. Later verification, status, preflight,
initialization, and reads never resolve the original URL or package source.

`program-kit capabilities` owns provider/workspace projections:

```text
capabilities initialize
capabilities refresh
capabilities update
capabilities status
capabilities remove
capabilities preflight
capabilities read
capabilities read-resource
```

One mutating command addresses one exact bundle/provider and defaults to all
bundle capabilities; repeated exact capability selections may narrow it.
Every mutation previews by default and applies only with the exact
`--accept-proposal-digest`.

`refresh` reconstructs derived catalog/provider bytes from the same verified
bundle and valid ownership lock. `update` accepts a new bundle version or
content digest. Neither silently adopts manual edits. A tampered lock blocks
until ownership is re-established through an explicit verified transition.

Program Kit's embedded capabilities use the same engine and retain the current
no-bundle-reference initialization shorthand. Embedded delivery is the only
narrow bootstrap distinction.

## Flat workspace capability catalog

Program Kit deterministically derives one flat workspace catalog grouped by
publisher and application. It is generated only from accepted exact
per-bundle/provider locks. It is not an author-edited source file.

Program Kit replaces the catalog atomically and binds its bytes in ownership
evidence. Manual edits or deletion are detectable drift and unusable until an
explicit accepted refresh reconstructs the canonical projection. Operating-
system permissions may add defense in depth but are not the integrity model.

Provider-native capability/skill selection remains authoritative. Program Kit
implements no confidence score, router, nested index, or intent resolver.
One Program Kit-owned `discover-capabilities` outcome capability can read the
flat catalog on demand and explain available outcomes, direct registered
operations, and setup blockers.

## Authoring safeguard and readiness

A human-started application-capability design procedure asks first whether the
product should remain tool-only or become agent-guided. Tool-only is a valid
explicit outcome. When agent-guided is requested, the procedure elicits
application-owned triggers, outcomes, intake, authority, operation bindings,
diagnostics, completion, handoffs, and knowledge closure.

Deterministic scaffolding creates required structure and coverage reports but
never invents domain content or one capability per operation. Unreferenced
operations are visible information, not an error.

Working readiness labels are:

- `tool-ready`: an exact operation can be safely projected and registered;
- `agent-guided`: an exact outcome capability has valid closure, provider
  projection, and resolved required operation bindings.

Bundle conformance is an independent underlying fact. The labels remain
candidate contract terms until their implementation contract is reviewed.

## Program Kit dogfood and acceptance

Program Kit's built-in consumer capabilities become the reference
application-capability payload. They use the same descriptor, closure,
verification, proposal, lock, provider rendering, catalog, preflight, read,
refresh, update, and cold-session mechanics.

Contributor architecture and debugging capabilities remain source-attached and
separately initialized. They are not consumer payload.

Acceptance includes:

- cold JTest semantic intent activating an outcome capability without inherited
  syntax and using registered exact operations;
- direct single-operation MCP use without a capability;
- generated Console introspection parity;
- host-neutral identity across Console, API, and MCP exposure;
- incomplete closure refusal;
- explicit update after changed operation/tool/capability bytes;
- no self-registration, self-permission, or autonomous loop;
- deterministic flat-catalog drift detection and refresh repair; and
- Program Kit's package-only consumer journey as reference proof.

Genuine Codex and Claude Code proofs remain provider-labelled. Deterministic
contract equality does not imply equal prompts, reasoning, models, or general
provider behavior.

## Static conformance and exclusions

The human explicitly selected `reuse-existing` for the private Program Kit C#
source gate. It applies only to Program Kit-owned implementation source and is
never attached to generated or consumer application source. Protocol, byte,
provider, lifecycle, package-only, and cold-session behavior remains executable
conformance rather than a Roslyn claim.

V1 excludes remote MCP; MCP Apps and optional extensions; HTTP invocation
adapter implementation; private/authenticated acquisition; package-feed
publication; provider-native transport; plugins as the delivery mechanism;
release, deployment, infrastructure, production data, operational history,
secret values; application-semantic approval by Program Kit; and all
autonomous registration, permission, provider, capability, or tool loops.
