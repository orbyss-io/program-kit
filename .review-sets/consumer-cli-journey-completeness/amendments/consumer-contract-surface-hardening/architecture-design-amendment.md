# Program Kit consumer contract-surface hardening architecture amendment

Artifact identity:
`pkid:design-amendment:program-kit:consumer-contract-surface-hardening@0.1.0-alpha.1`.

This amendment preserves and extends the exact completed consumer-journey
design
`pkid:design:program-kit:consumer-cli-journey-completeness@0.1.0-alpha.1`
with SHA-256
`9d336e3015daa8a8ec771d8e8aacc29020175a10174df7964d23088656468648`
and the exact completed Console-input materialization amendment
`pkid:design-amendment:program-kit:consumer-cli-console-input-materialization@0.1.0-alpha.1`
with SHA-256
`9fb6d810dd89232135d048dd54ebfba8d67ac45a46704d7855ef466c0ebb787f`.

State: `ready-for-human-decision`.

## Reason for the amendment

A package-only JTest 2.0 run proved that the alpha.2 CLI can install, retrieve
capability knowledge, materialize Console inputs, and generate a Console host.
It also exposed several places where Program Kit accepts or requires an exact
contract without making that contract sufficiently locatable or
materializable. The consumer had to bisect a 57 KB request, inspect Program Kit
source, reconstruct ordinal sort keys, copy a test-only fixture, and discover
that a generated-project verification target did not exist.

Those are product contract-surface defects. They are not reasons to weaken
strict JSON, identifier, Console projection, selection-lock, schema, gate, or
package verification.

The source basis is Program Kit commit
`e206f8cbfc2e61e909b18d7a3b91cc04a8d51a35`. The observed source truth is:

| Concern | Current source truth |
| --- | --- |
| Strict JSON diagnostics | `ProgramKitJsonSerializer` discards `JsonException.Path` and reports only the root CLR type; `ConsoleInputMaterializer` then replaces the path with `/request`. |
| PKID grammar | `ProgramKitIdentifier` accepts exactly four lowercase kebab-only segments, while registered schemas use several different patterns and some accept dotted names. |
| Console semantics | The relevant invariants live in `OpenConsoleDocumentValidator`, `DotNetConsoleBindingValidator`, and `DotNetConsoleProjectionValidator`; the packaged guide does not state the complete rules. |
| Console request examples | The only complete executable example is `tests/Fixtures/ConsumerCliConsole/console-input-request.json`, outside the installed knowledge closure. |
| Gate selection locks | `csharp-gate bind` consumes a fully hand-authored candidate. `inputDigest`, `outputDigest`, expected-receipt derivation, and composite ordinal keys have no public authoring contract. |
| Generated-project verification | Both host renderers emit an empty `Directory.Build.targets`; the C# gate harness invokes `/t:ProgramKitVerifyGeneratedProject`. |
| Local feed packing | The cold proof assumes exactly 29 prebuilt packages. `ProgramKit.Pack.proj` accepts one project and disables parallelism, so a local coordinated feed is normally packed through repeated restores/invocations. |
| Design-flow validation | `CommandSchemaSelector` supplies a cross-module closure only for C# gates. Architecture and planning schemas reference artifact schemas outside their selected module. Current design-flow schemas also cannot consistently carry the `$schema` member required for implicit CLI selection. |

## Required outcome

An AI agent using only an exact installed Program Kit CLI and its retrieved
capability/resource closure can:

1. locate the exact failed member and CLR expectation for every strict typed
   JSON read failure;
2. discover and use one canonical PKID grammar without source inspection;
3. discover the complete supported Open Console authoring style and obtain a
   complete request example;
4. produce a complete Console materialization request from one explicit
   consumer project and one small consumer-owned command sketch;
5. materialize a candidate C# gate bind request without deriving lock digests,
   receipt rows, or sort keys by hand;
6. invoke the generated-project verification target emitted with a generated
   host;
7. build the coordinated local package feed from source through one documented
   restore/build/pack journey; and
8. validate architecture, planning, and static-conformance documents through
   one offline transitive schema closure.

All commands remain finite, fail closed, deterministic, workspace-contained,
and non-authoritative. Program Kit does not edit consumer source or governing
documents. Scaffolding writes only a new explicitly selected output and refuses
an existing path.

## Version and immutability decision

The already handed-off `0.1.0-alpha.2` package bytes and every existing
versioned schema byte remain immutable.

If implementation is approved, the coordinated product candidate is
`0.1.0-alpha.3`. The repository's canonical product-version source remains the
only selector; no command, script, build, or workflow chooses or increments
the alpha ordinal.

Contract identities progress independently:

| Contract | Proposed current writer revision | Reason |
| --- | --- | --- |
| Artifact definitions / PKID grammar | `0.1.0-alpha.2` | Canonical dotted-name grammar replaces divergent inline patterns. |
| Static conformance disposition | `0.1.0-alpha.2` | Adds a selectable `$schema` member and canonical PKID references. |
| Architecture Design | `0.1.0-alpha.3` | Uses the new artifact definitions and disposition revision and permits exact implicit schema selection. |
| Implementation Plan | `0.1.0-alpha.4` | Uses the new artifact definitions/design reference and permits exact implicit schema selection. |
| Open Console | `0.1.0-alpha.2` | Makes operation request/result/diagnostic schema sets explicit and closes exit-role ambiguity. |
| Console materialization request | `0.1.0-alpha.2` | Selects Open Console alpha.2 and the canonical PKID grammar. |
| Console command sketch | `0.1.0-alpha.1` | New smaller consumer-authored input. |
| C# gate lock scaffold request | `0.1.0-alpha.1` | New explicit input for mechanical lock derivation. |
| C# gate selection lock | `0.1.0-alpha.1` | Defines previously unspecified input/output digest semantics. |

Existing readers remain available at their exact old revisions. New writers
emit only the proposed alpha revisions. Migrations are deterministic,
loss-rejecting, and preserve the source when a new exact requirement cannot be
derived.

## Strict typed JSON diagnostic contract

`ProgramKitJsonSerializer.Read<T>` remains the single strict typed read
boundary. It gains one internal, source-generated-metadata-backed failure
locator. For every failure it must retain:

- the exact JSON path of the failing value;
- the JSON member name, or `<root>` when the root token itself is invalid;
- the exact expected CLR type from the selected `JsonTypeInfo`; and
- the existing stable diagnostic identifier and culture-invariant message.

The public `ProgramKitDiagnostic.Path` and `CommandDiagnostic.Path` fields
remain the machine-readable path transport. Strict-reader messages use one
stable form:

```text
Member '<member>' at '<path>' expected CLR type '<full-type-name>': <reason>.
```

The path is an RFC 6901 JSON Pointer. Array indexes are numeric pointer
segments. A command adapter composes an operation prefix such as `/request`
with the serializer pointer; it must never replace a more specific path.

Missing required members, nullability failures, wrong token kinds, enum and
primitive converter failures, nested model failures, unknown members, and
root failures all use this contract. An unknown member names the containing
CLR type and states that the member is undeclared. No diagnostic includes the
entire input document, secrets, absolute consumer paths, or source text.

This is an additive diagnostic-quality correction. The four-field command
diagnostic JSON shape does not change, avoiding a second diagnostic-envelope
contract solely for these fields.

## Canonical Program Kit identifier grammar

Program Kit identifiers have exactly four colon-delimited segments:

```text
pkid:<kind>:<scope>:<name>
```

`kind` and `scope` are non-empty lowercase ASCII kebab tokens. `name` is one
or more lowercase ASCII kebab tokens separated by a single dot. The exact
regular expression is:

```regex
^pkid:[a-z0-9]+(?:-[a-z0-9]+)*:[a-z0-9]+(?:-[a-z0-9]+)*:[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*$
```

Consequently `pkid:approval-record:jtest:jtest-2.0` is valid. Uppercase,
underscores, empty atoms, repeated/trailing punctuation, and extra colon
segments remain invalid.

`ProgramKitIdentifier`, its JSON converter, artifact definitions alpha.2, and
every new schema revision use that exact grammar. Kind-specific schemas compose
the canonical definition with a kind prefix instead of copying another full
PKID pattern.

The grammar is discoverable through both:

```text
program-kit schemas read pkid:schema:program-kit:artifact-definitions@0.1.0-alpha.2
program-kit diagnostics explain PKART001
```

Schema conformance scans all registered current-writer schemas and rejects a
divergent full PKID grammar. Immutable older schemas retain their exact
historical reader semantics and are labelled as such by `schemas list`.

## Offline schema dependency closure

The CLI replaces the C#-gate-specific `CompositeSchemaModule` decision with a
generic finite dependency-closure provider over the already registered
`SchemaCatalog`.

For one selected schema it:

1. resolves the exact selected schema once;
2. walks only registered `$ref` URIs from the catalog;
3. rejects missing, duplicate, cyclicly malformed, or digest-mismatched
   registrations;
4. constructs the stable transitive closure in ordinal canonical-URI order;
5. registers that closure with the schema engine; and
6. performs no filesystem, assembly, network, or ambient URI discovery.

`validate`, `artifacts inspect`, gate validation, and future schema-backed
commands use the same closure provider. `validate` gains an optional exact
`--schema <schema-id@version>` selector for immutable legacy documents that do
not contain `$schema`; implicit selection still requires `$schema`.

The current-writer Static Conformance Disposition, Architecture Design, and
Implementation Plan schemas require a `$schema` property whose value is the
exact canonical URI for that revision. Their typed models carry the same
member. This resolves the present contradiction where implicit selection
requires a property that the selected closed schema rejects.

## Open Console contract style

The installed CLI gains a read-only finite command:

```text
program-kit dotnet describe-console-contract --format text|json
```

The output is projected from one versioned product-owned catalog, not
hand-maintained help prose. The command, Console materialization guide, schema
descriptions, and tests share this catalog.

For Open Console alpha.2 the catalog states and validators enforce:

1. Every command exit map is non-empty, contains code `0`, contains every
   host-owned role code, and contains each numeric code exactly once.
2. `invalidInvocation`, `cancellation`, and `internalFailure` are distinct
   positive host-owned reservations. They do not share code `0` or the help
   success code. Semantically similar failures still receive distinct codes so
   automation can distinguish the host lifecycle owner. Program Kit does not
   silently merge roles.
3. Every present stdin/stdout/stderr contract has a non-null exact
   `schemaRevision`.
4. A source with maximum occurrence greater than one binds only to
   ``System.Collections.Immutable.ImmutableArray`1<TScalar>`` with exactly one
   scalar generic argument matching the finite logical type catalog.
5. The selected shell host's `operationBindings` are authoritative. Each
   Open Console command carries explicit ordinal-unique
   `requestSchemaRevisions`, `resultSchemaRevisions`, and
   `diagnosticSchemaRevisions`. These sets must exactly equal the corresponding
   operation-binding sets. Arguments/options/stdin, stdout/result projection,
   exit diagnostics, and stderr must also reconcile with the explicit sets.
   Supersets, subsets, duplicate revisions, and merely contained result schemas
   fail.

The explicit schema-set fields correct the current
`ContainsOrAbsent` result check without pretending that the old 1.0.0
semantics changed in place.

## Complete Console request knowledge and scaffolding

The capability payload allow-lists:

- `dotnet-console-input-materialization-guide`;
- `dotnet-console-contract-style`;
- `dotnet-console-input-request-example`; and
- `dotnet-console-command-sketch-example`.

The complete request example is a schema-valid, semantically valid alpha.2
request derived from a compiling isolated consumer fixture. It is an example,
not a promise that its paths exist in another workspace.

The installed CLI also gains:

```text
program-kit dotnet scaffold-console-request <command-sketch> \
  --workspace-root <dir> \
  --consumer-project <relative-csproj> \
  --output <new-json-file>
```

The command sketch supplies every consumer-owned semantic selection:
identities, command paths and summaries, argument/option meanings, operation
and schema revisions, request/handler/optional-validator CLR metadata names,
authority references, streams, exit meanings, and explicitly selected
product-owned contract style. The consumer project supplies only the exact
project boundary.

The scaffolder may read the exact named project and exact named supplied
artifacts. It may derive project-file mechanics, mirrored operation schema
sets, default product contract structure, canonical ordering, and content
digests. It may not inspect source to invent operations or business meaning,
scan a solution/repository/feed/cache, restore, build, edit the project, choose
identities, or infer human authority.

The output is a complete strict materialization request, not a partially valid
document disguised as canonical output. A missing placeholder or semantic
selection produces a path-specific diagnostic and no file. The command
preflights the complete output, writes a BOM-less staging file, validates it
through the public strict reader and schema closure, then atomically promotes
it. Existing, escaping, or partially owned output is refused.

## C# gate selection-lock authoring

The installed CLI gains:

```text
program-kit csharp-gate scaffold-lock <definition> <lock-intent> \
  --repository-root <dir> \
  --output <new-bind-request>
```

The lock intent supplies values that cannot be derived mechanically: lock
identity, exact toolchain tuple, exact disposition and other external
references, receipt identity namespace, and any explicitly selected local
asset path not already named by the definition. The definition remains the
source of gate profiles, activations, selected analyzer components, rules,
recipes, and inventories.

The command reads only definition- or intent-named contained paths. It hashes
those paths, derives the complete candidate lock and `localAssets`, validates
the result, and writes one complete `CSharpGateBindRequest`. Existing
`csharp-gate bind` remains the final verifier/materializer.

The selection-lock alpha.1 digest contract is:

- `inputDigest` is SHA-256 over RFC 8785 canonical JSON for the versioned
  lock-input projection: exact definition reference, exact lock intent, exact
  toolchain tuple, and stable repository-relative local-asset path/digest
  rows. Absolute repository/output paths are excluded.
- `outputDigest` is SHA-256 over RFC 8785 canonical JSON for the complete
  selection lock with the `outputDigest` member omitted.

Both values are recomputed by scaffold, bind, and validation. A caller never
supplies either digest as an unchecked assertion.

Expected receipts are the distinct set produced from every activation row's
`projectProfileId`, every selected `analyzerComponentId`, and
`verificationProfile`, plus the exact mechanically formed receipt identity.
The stable receipt key is:

```text
projectProfileId|analyzerComponentId|verificationProfile|receiptIdentity
```

The stable activation key is:

```text
projectProfileId|sourceProfileId|command|boundary|verificationProfile|comma-joined-analyzerComponentIds
```

One shared canonical-ordering component owns these keys. Validators,
definition materialization, lock scaffolding, and `describe-definition` use
that component. Diagnostics print the relevant key and adjacent out-of-order
values. `describe-definition` states that ordering is .NET ordinal Unicode
code-unit order, not alphabetical or locale order; for the observed prefix
case `-` (`U+002D`) sorts before `|` (`U+007C`), so
`cli-tests|...` sorts before `cli|...`.

## Generated-project verification entry point

API/worker and Console host renderers use one shared exact
`Directory.Build.targets` projection. It defines:

```text
ProgramKitVerifyGeneratedProject
```

as the public generated-project verification entry point. A preceding
configuration target sets the generated-project binding property before the
normal `Build` dependency executes. The existing exact
`Orbyss.ProgramKit.GeneratedOutputIntegrity.Build` package remains the provider
of generated-output integrity mechanics, and an installed C# gate import can
therefore observe the `generated-project-verify` command/boundary.

The entry point runs no restore and is not an alias for the CLI-only
`dotnet verify-host` operation. The package-only acceptance fixture must prove
that:

```text
dotnet msbuild GeneratedHost.csproj \
  /t:ProgramKitVerifyGeneratedProject \
  /restore:false
```

executes the generated-output integrity target, builds the host, and executes
the configured generated-output gate activation when one is selected.

## Manifest-driven local consumer-feed packing

The repository gains a canonical release-package manifest containing the
current 29 first-party package IDs, project paths, roles, and dependency
closure. The count is evidence derived from the manifest, never a separate
hard-coded contract.

The contributor/source-checkout command is:

```text
build/Invoke-PackConsumerFeed.ps1 -OutputRoot <new-dir>
```

It:

1. reads the exact repository-selected product version;
2. restores the solution once using the repository NuGet configuration and
   lock/audit policy;
3. builds the selected solution/projects once;
4. invokes one aggregate no-restore/no-build pack over the manifest-selected
   projects, with bounded parallelism;
5. verifies exact package IDs, versions, filenames, first-party dependency
   closure, and allow-listed content; and
6. emits a flat feed, package manifest, and SHA-256 projection.

The script refuses an existing output, extra/missing packages, version drift,
packable projects absent from the manifest, and package bytes outside the
selection. It does not publish or alter a global NuGet configuration.

The README labels this as an optional source-contributor/local-testing journey.
Ordinary consumers continue to download a verified release feed and never need
Program Kit source to install the CLI.

## Knowledge-closure routing

Schemas alone are not sufficient consumer knowledge. The following capability
closures must retrieve the relevant guide/catalog/example by exact resource
identity:

| Capability | Required knowledge |
| --- | --- |
| `design-software` | Console integration-project seam, Open Console style, command-sketch example, schema and migration identities. |
| `design-csharp-build-gate` | Definition and selection-lock authoring catalogs, exact ordering/digest rules, generated-project target. |
| `implement-software-plan` | Scaffold/materialize/generate/verify command sequence and no-overwrite boundaries. |
| `maintain-software` | Strict diagnostic interpretation, safe refresh/scaffold behavior, compatible migration rules. |
| `publish-dotnet-application-locally` | Exact local feed/host verification prerequisites without source checkout assumptions. |

Provider wrappers remain thin. Capability retrieval stays read-only and
digest-bound to the installed CLI/workspace lock. A schema, guide, example, or
catalog cannot grant authority or authorize an edit.

## Compatibility assessment

| Surface | Classification | Treatment |
| --- | --- | --- |
| More specific strict-reader diagnostics | compatible additive | Existing IDs and command envelope remain; paths/messages gain exact information. |
| Runtime PKID dotted-name acceptance | compatible widening | Old valid values remain valid; new current-writer schemas share the widened grammar. |
| New schema revisions and `$schema` members | contract migration | Old bytes/readers remain; explicit lossless migrations create new revisions. |
| Exact Open Console result-schema sets and positive unique host roles | conditionally compatible | New alpha.2 contract; old documents remain old-reader inputs and migrate only when exact sets can be supplied. |
| New describe/scaffold commands and packaged resources | compatible additive | Finite descriptor/catalog additions; no implicit execution. |
| Selection-lock digest enforcement | contract migration | New alpha lock revision; old 1.0.0 lock remains readable but is not relabelled. |
| Generated `Directory.Build.targets` | generated-artifact change | Regeneration/refresh is required; existing sealed output is never edited in place. |
| Aggregate pack script/manifest | contributor tooling additive | Does not alter package consumers or publication authority. |
| Generic schema dependency closure | compatible bug fix | Previously unresolved registered references become resolvable; unregistered/network references still fail. |

## Static-conformance disposition

Disposition: `reuse-existing`.

The static gate is bound once at Program Kit repository scope, not once per
software design:

- gate:
  `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`,
  `sha256:e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1`;
- activation matrix:
  `pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`,
  `sha256:bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b`.

This amendment reuses that compatible repository policy for changed C# and
adds contract-, CLI-, schema-, package-, and cold-consumer tests for behavior
outside static analysis.

## Required acceptance scenarios

Implementation acceptance must include at least:

1. Deep nested wrong-type, missing-member, nullability, unknown-member,
   converter, array, and root strict-read failures with exact pointer, member,
   and CLR type, including preservation through PKCIM001.
2. PKID positive `pkid:approval-record:jtest:jtest-2.0` plus punctuation,
   underscore, uppercase, segment-count, and parser/schema parity negatives.
3. `describe-console-contract` text/JSON equality to its versioned catalog and
   guide.
4. Exhaustive/unique exit maps; distinct positive host roles; non-null stream
   schemas; exact repeated `ImmutableArray` binding; exact request/result/
   diagnostic sets, including superset and subset negatives.
5. Retrieval of the complete Console request and sketch examples from an
   installed package-only CLI at exact source bytes.
6. Sketch-to-request-to-materialize-to-generate-to-verify from one empty
   isolated consumer with no Program Kit checkout and no hand-authored 57 KB
   request.
7. Scaffold refusal for missing placeholders, semantic inference attempts,
   escaping paths, existing outputs, BOM input, stale project/artifact digests,
   and interrupted writes.
8. Gate lock scaffold derivation of local assets, exact input/output digests,
   expected receipts, and canonical ordering; bind recomputation and tamper
   negatives.
9. `describe-definition` output naming both composite keys and ordinal code
   points, including the `cli-tests` versus `cli` regression.
10. Generated API/worker and Console hosts containing the exact target and
    successfully executing `/t:ProgramKitVerifyGeneratedProject` with no
    restore.
11. One restore, one build, and one aggregate manifest-selected pack producing
    the complete exact local feed; no per-project restore loop.
12. `validate` and `artifacts inspect` agreement for Architecture Design,
    Implementation Plan, and Static Conformance Disposition current writers,
    with offline cross-module `$ref` success and unregistered-reference
    failure.
13. Full unit, conformance, private C# gate, package inspection, isolated tool
    install, capability/resource digest, and package-only cold-consumer proofs
    against coordinated `0.1.0-alpha.3` candidate bytes.

## Non-goals

This amendment does not authorize:

- implementation before exact design/plan digest approval;
- modification or republication of `0.1.0-alpha.2` package/schema bytes;
- automatic package-version selection or increment;
- GitHub Release creation, NuGet/feed publication, signing, or promotion;
- JTest repository mutation;
- repository, solution, package-cache, feed, or source scans used to infer
  consumer semantics;
- editing existing consumer source, requests, definitions, locks, or generated
  output in place;
- shared host exit-code roles or relaxed exact projection;
- network schema resolution; or
- a new static gate per design.

## Residual risks and stop conditions

- If source-generated JSON metadata cannot deterministically locate the
  expected member type for every strict failure category, implementation stops
  rather than parsing runtime exception prose heuristically.
- If the smaller Console sketch cannot express every consumer-owned semantic
  choice without inference, its contract must be amended and re-approved.
- If a selection-lock digest projection is ambiguous or self-referential,
  implementation stops rather than choosing an undocumented convention.
- If the generated-project target cannot execute the configured gate activation
  without adding a new host/gate binding contract, that is a material
  deviation requiring a design amendment.
- If one restore/build plus aggregate no-build pack cannot produce byte-valid
  packages, implementation may optimize the repository build graph but may not
  weaken lock, audit, package, or closure verification.
- Any need to mutate existing schema bytes, resolve schemas over the network,
  scan ambient consumer state, or publish packages is a material deviation.
