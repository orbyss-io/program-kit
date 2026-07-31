# Research: Status Component and API Vertical Slice

## Decision 1: Exact .NET baseline

**Decision**: Pin .NET SDK `10.0.302` in `global.json` with
`rollForward: "disable"` and `allowPrerelease: false`. Target `net10.0` and pin
`LangVersion` to `14.0`; never use `latest`. Shared build policy enables
nullable analysis, disables implicit usings, treats warnings as errors, enforces
code style, selects `AnalysisLevel` `10.0-recommended`, and enables deterministic
compilation.

**Rationale**: `10.0.302` is the latest stable .NET 10 SDK on the planning date
and is installed in the development environment. Exact SDK selection is part of
the construction identity and prevents ambient feature-band movement.

**Alternatives considered**:

- Roll forward to the newest patch/feature band: rejected because it changes
  compiler, pack, and restore behavior outside an accepted lock update.
- Pin the runtime separately: deferred because the CLI is not yet selecting a
  self-contained deployment profile.
- Use preview C#: prohibited by the constitution.

**Sources**: [.NET 10 downloads](https://dotnet.microsoft.com/en-us/download/dotnet/10.0),
[`global.json` policy](https://learn.microsoft.com/en-us/dotnet/core/tools/global-json),
[C# language version configuration](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/configure-language-version),
[analysis-level settings](https://learn.microsoft.com/en-us/dotnet/core/project-sdk/msbuild-props).

## Decision 2: Four production projects and three test projects

**Decision**: Create:

- `ProgramKit.Contracts`: versioned public records, schema resources, provider
  service-provider interfaces, and no filesystem/process implementation.
- `ProgramKit.Kernel`: trusted canonicalization, validation, resolution,
  authority, candidate sealing, ownership, publication, admission, evaluation,
  evidence, and diagnostics.
- `ProgramKit.Providers.DotNet`: one first-party distribution containing
  separately identified .NET/CShells component and ASP.NET endpoint/host
  providers.
- `ProgramKit.Cli`: thin composition root, owned argument parser, exact provider
  registration, and human/JSON rendering.

Tests are split into `ProgramKit.UnitTests`, `ProgramKit.ContractTests`, and
`ProgramKit.AcceptanceTests`, with reference semantics only under
`tests/Fixtures/Reference.Status`.

**Rationale**: These are real trust, public-contract, distribution, and
application boundaries. Keeping the two logical providers in one distribution
avoids a project per identity while their manifests remain distinct. Generated
consumer projects reference CShells and ordinary platform packages only; no
Program Kit assembly enters their runtime graph.

**Alternatives considered**:

- One monolithic CLI project: rejected because kernel trust and provider/public
  contracts would be inseparable and forbidden dependencies hard to prove.
- One assembly per provider identity: rejected until independent distribution
  requires it.
- A production `Reference.Status` project: rejected because Status meaning is a
  consumer fixture, not Program Kit domain meaning.

## Decision 3: Owned finite CLI parser

**Decision**: Do not add `System.CommandLine`. Implement a small invariant parser
for exact commands `explain`, `construct`, `evaluate`, `help`, and `version`
with only `--workspace`, `--request`, `--format`, and `--`. All recoverable parse
and usage failures enter the Program Kit result/diagnostic pipeline.

**Rationale**: The grammar is finite, while Program Kit must own help, version,
parse, exit-code, stdout, and diagnostic behavior. Framework-generated prose or
exceptions could bypass the one-envelope public contract.

**Alternatives considered**:

- `System.CommandLine [2.0.10]`: a stable fallback if later command breadth
  justifies the dependency and contract interception is proven.
- Ad-hoc parsing in `Program.cs`: rejected; parsing remains a typed, tested CLI
  boundary despite having no external dependency.

**Sources**: [System.CommandLine package](https://www.nuget.org/packages/System.CommandLine/),
[Microsoft command-line guidance](https://learn.microsoft.com/en-us/dotnet/standard/commandline/).

## Decision 4: Program Kit canonical JSON profile

**Decision**: Define `program-kit.canonical-json/v1` as a Program Kit-owned,
RFC 8785-compatible strict subset:

- UTF-8, no BOM, no insignificant whitespace, no trailing newline;
- recursively sort object members by unsigned UTF-16 code-unit order;
- preserve array order; contracts sort set-like collections before encoding;
- use RFC 8785 string escaping, reject lone surrogates, and perform no blanket
  Unicode normalization;
- reject duplicate object names;
- allow null, Boolean, string, array, object, and base-10 integers only in
  `[-9007199254740991, 9007199254740991]`;
- reject floats and exponent notation; model exact decimal/time/version values
  as contract-validated strings; and
- preserve the distinction between absent and explicit null.

Use `System.Text.Json` for strict UTF-8 parsing and transport, including duplicate
property rejection, with a small Program Kit-owned canonical writer. Never use
serializer declaration order, dictionary insertion order, or the framework's
default encoder as the canonical contract.

**Rationale**: This preserves interoperable deterministic bytes without importing
ECMAScript floating-point formatting or allowing framework implementation drift
to define Program Kit identity.

**Alternatives considered**:

- Unrestricted RFC 8785/JCS: rejected because the first slice needs no floating
  point and should not inherit its rounding complexity.
- Default `JsonSerializer` bytes: rejected because property ordering and encoder
  block lists are not a stable canonical contract.
- Blanket NFC normalization: rejected because canonicalization must not silently
  rewrite consumer strings; field-owning contracts may validate normalization.

**Sources**: [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html),
[`JsonPropertyOrder`](https://learn.microsoft.com/en-us/dotnet/api/system.text.json.serialization.jsonpropertyorderattribute?view=net-10.0),
[`System.Text.Json` encoding behavior](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/character-encoding),
[duplicate property rejection](https://learn.microsoft.com/en-us/dotnet/api/system.text.json.jsondocumentoptions.allowduplicateproperties?view=net-10.0).

## Decision 5: JSON Schema is structural, offline, and bounded

**Decision**: Publish JSON Schema Draft 2020-12 contracts. Pin
`JsonSchema.Net [9.4.0]` behind an internal structural-validation adapter and
lock its full transitive closure. Schemas use exact `$id` values, local static
`$ref`/`$defs`, closed objects, and an allowlisted keyword subset. Program Kit
resolves schemas only from a local exact identity/digest registry; schema IDs
never cause a network fetch.

Validation order is:

1. resource-bounded JSON/restricted-YAML parsing with duplicate-key rejection;
2. projection to a neutral JSON value tree;
3. structural schema validation;
4. binding to the API-neutral typed model;
5. kernel semantic validation;
6. canonical encoding only after acceptance.

Validator-native messages and enumeration order never become public
diagnostics. Contract tests cover every keyword/profile actually used rather
than importing a broader executable schema engine or the entire upstream test
suite.

**Rationale**: JSON Schema documents the public structural boundary, while typed
kernel invariants retain identity, authority, resolution, ownership, and
admission meaning.

**Alternatives considered**:

- Draft 7: rejected for a new contract family with no legacy constraint.
- Schema-only semantics: rejected because JSON Schema cannot own Program Kit
  authority or admission.
- Custom schema engine: rejected as unjustified scope.

**Sources**: [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12),
[validation specification](https://json-schema.org/draft/2020-12/json-schema-validation),
[core specification](https://json-schema.org/draft/2020-12/json-schema-core),
[`JsonSchema.Net 9.4.0`](https://www.nuget.org/packages/JsonSchema.Net/9.4.0).

## Decision 6: Restricted YAML is authoring syntax only

**Decision**: Pin `YamlDotNet [18.1.0]` behind a low-level parser/event adapter
for `program-kit.restricted-yaml/v1`. Permit one YAML 1.2 document containing
string-key mappings, sequences, quoted strings, exact plain `null`/`true`/`false`,
safe-range base-10 integers, and comments. Treat all other accepted plain
scalars as strings.

Reject duplicate keys after decoding, complex/non-string keys, explicit tags,
anchors, aliases, merge keys, directives, multiple documents, floats,
infinities, NaN, octal/hex coercion, implicit empty/`~` nulls, includes,
environment expansion, templates, network resolution, and inputs above exact
byte/depth/node/scalar limits. Preserve source spans only for safe diagnostics.
Semantic identity always comes from the accepted canonical JSON projection, not
the original YAML bytes or mapping order.

**Rationale**: YAML is humane authoring input but has too many ambient/coercive
features to become canonical truth. A low-level adapter makes the supported
subset visible and testable.

**Alternatives considered**:

- Direct POCO deserialization: rejected because implicit typing, aliases, and
  parser-native errors could escape the boundary.
- JSON-only v1: rejected because the constitution explicitly selects restricted
  YAML authoring.
- A custom YAML parser: rejected as unnecessary and unsafe.

**Sources**: [YAML 1.2.2](https://yaml.org/spec/1.2.2/),
[`YamlDotNet 18.1.0`](https://www.nuget.org/packages/YamlDotNet/18.1.0).

## Decision 7: SHA-256 identity profile

**Decision**: Hash exact canonical bytes with SHA-256 and render
`sha256:<64 lowercase hex characters>`. A collection or construction identity
hashes a canonical manifest of sorted typed entries
`(role, identity, revision, digest)`; it never concatenates bare hashes.

Artifact digests, collection identities, source-authoring evidence, authority,
freshness, availability, and future authenticity/signature claims remain
distinct.

**Rationale**: SHA-256 is in the BCL, standardized, transparent in diagnostics
and filenames, and requires no dependency. Algorithm qualification preserves
future agility.

**Alternatives considered**:

- BLAKE3: rejected due to new dependency/interoperability cost.
- SHA-512: no v1 benefit.
- Base64 display: shorter but less transparent for humans and file tooling.

**Sources**: [`SHA256.HashData`](https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.sha256.hashdata?view=net-10.0),
[FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final).

## Decision 8: Exact dependency and test baseline

**Decision**: Use central package management, exact direct versions, no central
version override, and committed `packages.lock.json` files for every
executable/test root. Normal validation is locked restore followed by
`--no-restore` build/test/pack.

Initial direct package set:

| Purpose | Exact package |
|---|---|
| JSON Schema adapter | `JsonSchema.Net [9.4.0]` |
| Restricted YAML adapter | `YamlDotNet [18.1.0]` |
| Generated component | `CShells.AspNetCore.Abstractions [0.0.28]` |
| Generated API host | `CShells.AspNetCore [0.0.28]` |
| Tests | `MSTest.TestFramework [4.3.3]` |
| Tests | `MSTest.TestAdapter [4.3.3]` |
| Test host | `Microsoft.NET.Test.Sdk [18.8.1]` |

`System.Text.Json`, cryptography, filesystem, PE metadata, and ASP.NET Core come
from the pinned .NET 10 shared framework/SDK. No coverage, mocking, command-line,
logging, dependency-injection, or filesystem-abstraction package is admitted
without a demonstrated need.

The repository `NuGet.Config` clears inherited sources and names approved
sources. Direct and transitive resolution is frozen by lock files; transitive
pinning is not enabled because it can change packed library dependencies.

**Rationale**: This is the smallest known dependency set that satisfies the
constitutional YAML, schema, CShells, and test obligations while keeping the
full closure visible and reproducible.

**Alternatives considered**:

- `MSTest.Sdk` MSBuild-SDK reference: rejected for this slice because ordinary
  exact package references make the test closure more directly visible in lock
  files.
- xUnit/NUnit: capable, but no user value justifies a non-Microsoft test stack.
- Loose or minimum versions: prohibited.

**Sources**: [NuGet version ranges](https://learn.microsoft.com/en-us/nuget/concepts/package-versioning),
[lock files](https://learn.microsoft.com/en-us/nuget/consume-packages/package-references-in-project-files),
[central package management](https://learn.microsoft.com/en-us/nuget/consume-packages/central-package-management),
[NuGet configuration](https://learn.microsoft.com/en-us/nuget/reference/nuget-config-file).

## Decision 9: Version-specific CShells provider

**Decision**: Treat CShells `0.0.28` as an exact version-specific .NET provider
profile:

- component package: `CShells.AspNetCore.Abstractions [0.0.28]`;
- host package: `CShells.AspNetCore [0.0.28]`;
- component feature implements the pinned
  `CShells.AspNetCore.Features.IWebShellFeature` surface;
- host activation uses exact 0.0.28 `AddShells`, `FromAssemblies`, and
  `MapShells` APIs with an explicitly selected feature assembly.

Compile provider conformance fixtures against exact package bytes and source
commit `29fe542835696131278fcacc6cdb9a6186fc0447`. Isolate all CShells syntax in
the .NET provider. Never use default/host assembly discovery, dynamic
management, migration, or multitenancy behavior.

**Rationale**: The current CShells repository has already renamed some APIs
(`FromAssemblies` became `WithAssemblies`), proving that package-version syntax
must be an adapter concern rather than kernel meaning. CShells supplies selected
.NET host mechanics; Program Kit still owns deterministic contribution input
and exact activation.

**Alternatives considered**:

- Generate against current repository docs: rejected because they do not match
  the accepted package.
- Put CShells types in the kernel: rejected because target mechanics must remain
  provider-scoped.
- Ambient assembly discovery: prohibited.

**Sources**: [`CShells 0.0.28`](https://www.nuget.org/packages/CShells/0.0.28),
[`CShells.AspNetCore 0.0.28`](https://www.nuget.org/packages/CShells.AspNetCore/0.0.28),
[CShells repository](https://github.com/valence-works/cshells).

## Decision 10: Sealed candidate and atomic trust

**Decision**: Providers write only into an isolated draft. The kernel normalizes
logical paths, rejects traversal/symlink/case-fold/reserved-name collisions,
hashes every file, sorts the manifest, records whole-file ownership and source
authority, then seals the complete set. State proceeds:

```text
Draft -> Sealed -> Evaluated -> PublicationPrepared -> Publishing
      -> PublishedUnadmitted -> Admitted
```

Terminal/recovery states are `Rejected`, `Interrupted`, and
`RecoveryRequired`. After sealing, mutation is forbidden and bytes are rehashed
before evaluation and publication.

Publish same-volume groups under a Program Kit cooperative workspace lock:

1. revalidate live ownership and digest preconditions;
2. durably write the complete journal before effects;
3. apply canonically ordered directory moves or sibling temporary
   create/replace operations with backups where supported;
4. durably record each physical transition;
5. verify every live byte;
6. write publication evidence and the admission receipt last.

No valid admission receipt means the set is untrusted. Evaluation never
recovers or mutates; complete/rollback repair is a separate authorized request.
After an uncertain effect, no blind retry occurs.

**Rationale**: Windows and Linux provide useful same-volume file operations but
no general atomic multi-file transaction. Program Kit can honestly guarantee
atomic trust, recoverable publication, and explicit interruption—not power-loss
proof or invisible partial bytes.

**Alternatives considered**:

- Claim atomic multi-file writes: false and rejected.
- Automatic evaluation rollback: violates read-only evaluation and authority.
- A filesystem abstraction or database transaction: unnecessary for the first
  ordinary-workspace slice.

**Sources**: [`File.Move`](https://learn.microsoft.com/en-us/dotnet/api/system.io.file.move?view=net-10.0),
[`Directory.Move`](https://learn.microsoft.com/en-us/dotnet/api/system.io.directory.move?view=net-10.0),
[`File.Replace`](https://learn.microsoft.com/en-us/dotnet/api/system.io.file.replace?view=net-10.0),
[`FileStream.Flush`](https://learn.microsoft.com/en-us/dotnet/api/system.io.filestream.flush?view=net-10.0).

## Decision 11: Two-stage exact local package integration

**Decision**: The pre-construction explanation names the exact component package
ID/version, producing construction identity, selected contract, and intended
direct relationship. The candidate flow then:

1. constructs, builds, and packs the component inside isolation;
2. records the package SHA-256 and NuGet content hash;
3. finalizes the API sub-lock with that exact package evidence;
4. generates the API with `PackageReference Version="[x.y.z]"`;
5. restores from an explicit two-source local `NuGet.Config`;
6. seals/evaluates the whole component/API/feed candidate before publication.

One local source contains exactly the constructed component package. A separate
local mirror contains the exact approved dependency/test closure. Package Source
Mapping maps the component ID only to its feed and every other allowed ID to the
mirror. Restore uses the generated config explicitly, a clean relative packages
folder, no cache, and locked mode.

The package digest is post-pack evidence, not a guessed pre-construction fact.
Within each operation it must agree across the feed, lock, assets, artifact
manifest, and API binding.

Classify `.nupkg` initially as `verified-equivalent` under an exact named
verifier because it is external-tool output. A pinned `10.0.302` path/culture
fixture may upgrade the claim to `canonical-byte`; failure to prove byte
identity must not be hidden or allowed to weaken Program Kit-owned canonical
artifact claims.

**Rationale**: This proves integration between packaged products without a
project reference, ambient global cache, source-order choice, or false
pre-knowledge of package bytes.

**Alternatives considered**:

- Project reference: fails the product integration promise.
- Plain `Version="1.0.0"`: NuGet treats it as a minimum, not exact-only.
- One mixed source/global cache: source-confusion and reproducibility risk.
- Require `.nupkg` byte identity before evidence exists: an overclaim; the
  external-tool verifier class is the honest initial boundary.

**Sources**: [NuGet package versioning](https://learn.microsoft.com/en-us/nuget/concepts/package-versioning),
[PackageReference lock files](https://learn.microsoft.com/en-us/nuget/consume-packages/package-references-in-project-files),
[configuration precedence](https://learn.microsoft.com/en-us/nuget/consume-packages/configuring-nuget-behavior),
[Package Source Mapping](https://learn.microsoft.com/en-us/nuget/consume-packages/package-source-mapping),
[NuGet pack targets](https://learn.microsoft.com/en-us/nuget/reference/msbuild-targets).

## Decision 12: Contract and acceptance evidence

**Decision**: Tests are divided by proof:

- unit: canonicalization, paths/collisions, identity, ownership transitions,
  candidate sealing, diagnostics, parser, and endpoint seam rules;
- contract: Draft 2020-12 schema/profile fixtures, canonical bytes, public CLI
  results, diagnostic catalog, exact CShells ABI/generated shape, provider
  manifests, and absence of Status semantics from production assemblies;
- acceptance: real filesystem fault injection, two-stage package consumption,
  path/culture/order repeatability, invalid/no-write behavior, drift/evaluate/
  repair, runtime dependency allowlisting, relocated consumer execution, and
  black-box status operation.

Run filesystem/publication tests on Windows and Linux. The required
reproducibility fixtures vary short/deep Unicode paths, `en-US`, `tr-TR`, and
`nl-NL`, enumeration/contribution/provider order, scheduling, and clean package
caches. Compare logical manifests and every claimed canonical byte.

Runtime isolation copies only generated consumer outputs and declared local
feeds into a clean location, restores locked, builds/tests/publishes, inspects
assets/deps/PE references against an allowlist, starts the ordinary API, and
observes its declared status endpoint. No Program Kit checkout or assembly may
be required there.

**Rationale**: Green unit tests cannot prove product integration, real
filesystem recovery, runtime independence, or contributor comprehension.

**Alternatives considered**:

- In-memory filesystem only: rejected because rename, sharing, case, and handle
  behavior are platform-specific.
- Prohibited-name search only: rejected; exact dependency allowlisting is
  stronger.
- Container-only quickstart: too heavy for the required one-hour local path,
  though it may become additional CI evidence.

## Resolved clarification summary

All planning unknowns are resolved:

- exact SDK/language and dependency versions are pinned;
- command grammar and result boundary are fixed;
- canonical JSON, YAML, schema, and digest profiles are fixed;
- project/package/provider boundaries are fixed;
- CShells 0.0.28 syntax is isolated and verified;
- publication promises atomic trust and recovery without overstating
  filesystem guarantees; and
- package and generated-artifact reproducibility claims remain separately
  classified and evidence-backed.
