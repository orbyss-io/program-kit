# Phase 0 Research: Program Kit Adapter for Spec Kit

**Feature**: `003-speckit-adapter`

**Status**: Complete — no unresolved technical clarification

**Authority**: Approved `spec.md`, `DEC-046`,
`DESIGN-SPECKIT-ADAPTER.md`, and Program Kit Constitution 1.2.0

## Research method

Decisions below use the checked-in Program Kit source and package proof as the
implementation baseline, the accepted adapter design as product authority, and
the exact Spec Kit 0.15.1 release/documentation as the external integration
baseline. A currently broken local `uv` trampoline was not used as behavioral
evidence. Spec Kit compatibility is proven later from a clean exact installation.

## R001 — Exact V1 release envelope

**Decision**: Build the feature against this exact initial envelope:

- Program Kit CLI package `Orbyss.ProgramKit.Cli` `1.0.0-alpha.2`;
- Spec Kit `0.15.1`;
- adapter extension `orbyss-program-kit-adapter` `0.1.0`;
- adapter and Program Kit target framework `net10.0`;
- .NET SDK `10.0.302` with roll-forward disabled;
- target profile `dotnet10-cshells-0.0.28` at revision `1.0.0`; and
- Windows and Linux as the supported consumer platforms.

`1.0.0-alpha.2` is a deliberate new Program Kit release identity because this
feature adds versioned public commands and contracts. Existing alpha.1 package
claims remain historical rather than being silently rebound to different public
surface bytes.

**Rationale**: The repository already pins SDK 10.0.302 and exposes package
`1.0.0-alpha.1`; a new public surface requires a distinct exact release. The
approved design and specification bind Spec Kit 0.15.1 and the .NET/CShells
profile. The adapter has its own lifecycle and therefore its own version.

**Alternatives considered**:

- Reuse `1.0.0-alpha.1`: rejected because it would make two materially different
  public distributions share one package version.
- Use a Spec Kit version range: rejected because V1 compatibility is fail-closed
  and proof exists for one exact line only.
- Version the adapter with the Program Kit CLI: rejected because the extension
  and factory distribution update independently.

## R002 — Workspace-local Program Kit acquisition

**Decision**: The primary consumer path is an exact .NET local tool manifest:

1. create `.config/dotnet-tools.json` with `dotnet new tool-manifest`;
2. install `Orbyss.ProgramKit.Cli` at exactly `1.0.0-alpha.2`;
3. invoke only through `dotnet tool run program-kit -- <arguments>`; and
4. verify `version --format json` before trusting the configured distribution.

The already-proven exact `--tool-path` path remains a package-only test harness
fallback, not an ambient consumer semantic fallback. The adapter never searches
`PATH` for `program-kit`.

**Rationale**: A tool manifest is repository-owned, cross-platform, reviewable,
and expresses an exact package choice. It also distinguishes installed bytes
from provider/profile selection and authority.

**Alternatives considered**:

- Global tool installation: rejected because ambient lookup can shadow the
  reviewed distribution.
- Bundle the Program Kit CLI inside the Spec Kit extension: rejected because it
  would merge two independently selected product lifecycles.
- Direct assembly loading by the adapter: rejected because the adapter may use
  only the public CLI boundary.

## R003 — Public contract versioning

**Decision**: Preserve the existing closed v1 factory-request contract and add
the new request schemas for initialization, catalog, restore, preparation, and
authority recording. Advance the single current operation-result contract to
`program-kit.operation-result/v2` for every public command. Evolve the existing
`OperationResult` model, factory, dispatcher, projector, and renderer directly;
do not introduce parallel legacy/current result types or execution paths.

**Rationale**: Adding commands, phases, and typed payloads changes the exact
closed result contract and therefore requires a new schema identity. Program
Kit has no supported external result consumers or approved migration system in
this development stage, so maintaining v1 beside v2 would create speculative
compatibility complexity. Historical Feature 001/002 evidence remains truthful,
but it does not make the historical schema a live runtime surface.

**Alternatives considered**:

- Widen the v1 enums under the v1 identity: rejected because the v1 schema
  identity is closed; the evolved contract must identify itself as v2.
- Create unrelated result envelopes per command: rejected because the
  constitution requires one consistent public operation-result model.
- Keep v1 and v2 live in parallel: rejected because no named current consumer,
  support duration, retirement plan, or approved migration capability justifies
  the extra types and branches. Until migration is explicitly designed,
  consumers adapt manually when adopting a newer Program Kit contract.

## R004 — Program Kit public command grammar

**Decision**: Add these exact commands using the existing explicit
`--workspace`, `--request`, and `--format text|json` grammar:

```text
program-kit init --workspace <path> --request <path> [--format text|json]
program-kit catalog list --workspace <path> --request <path> [--format text|json]
program-kit restore --workspace <path> --request <path> [--format text|json]
program-kit prepare --workspace <path> --request <path> [--format text|json]
program-kit authority record --workspace <path> --request <path> [--format text|json]
```

All request files are regular files inside the declared workspace. `init` is a
bounded bootstrap operation rather than a factory command. `catalog list` is
read-only/offline. `restore` may materialize only the generated lock/state it
declares. `prepare` is effect-free. `authority record` is explicit and separate
from the adapter.

**Rationale**: One explicit request-file grammar provides canonical input,
disclosure handling, provenance, and non-interactive human-or-agent invocation.
It also avoids adding semantic CLI defaults.

**Alternatives considered**:

- Interactive prompts: rejected because they are not canonical or
  orchestrator-neutral.
- Many semantic command-line options: rejected because quoting and platform
  differences would become contract inputs.
- Let the adapter call authority recording: rejected because it would collapse
  review and authority.

## R005 — Profile selection preserves consumer ownership

**Decision**: V1 does not add a `program-kit profile select` mutator. A human or
authorized agent chooses a catalog entry by editing the consumer-owned
`program-kit.yaml`; `program-kit restore` then validates and locks the exact
selection. Help/continuation data may provide a bounded manifest patch proposal,
but Program Kit never applies it to an existing consumer-owned manifest.

The optional workspace profile default exists only in `program-kit.yaml` and
its accepted lock. Adapter project configuration may name an exact
feature-specific selection override, but it does not define a second profile
default. This keeps Program Kit composition as the sole profile-selection
authority.

`init` creates `program-kit.yaml` only when absent as a seeded handoff with zero
selections. After creation it is consumer-owned.

**Rationale**: This preserves the constitutional rule that consumer-owned files
are not modified by Program Kit while retaining the intended package-manager-like
manifest/lock workflow.

**Alternatives considered**:

- Directly edit `program-kit.yaml` from `profile select`: rejected because it
  would let Program Kit modify a consumer-owned artifact.
- Infer the sole catalog entry: rejected because availability is not selection.
- Put the selection only in adapter config: rejected because Program Kit's
  manifest and lock are the authoritative composition boundary.

## R006 — Distribution catalog and restore source

**Decision**: The CLI composition root creates one immutable distribution
descriptor from the explicitly registered `DotNetProvider`, embedded public
schemas/catalogs, package release identity, and packaged conformance resources.
Catalog and restore consume that descriptor; neither scans assemblies,
directories, NuGet sources, or the network.

The V1 manifest collection permits zero or more named exact selections, but the
tested distribution exposes only the exact .NET profile. Restore rejects ranges,
duplicates, ambiguity, unavailable evidence, and dynamic provider packages.

**Rationale**: The composition root already explicitly constructs one
`DotNetProvider`. Extending that explicit registration into a distribution
descriptor is smaller and safer than adding a plugin loader or registry service.

**Alternatives considered**:

- Reflection or directory scanning: rejected as ambient discovery.
- Remote catalog/marketplace: explicitly deferred.
- A new general package graph: rejected because the one-distribution V1 journey
  does not require it.

## R007 — Preparation and authority closure

**Decision**: `prepare` consumes a new `PreparationRequest` and returns a
`PreparationProposal` containing:

- exact request binding;
- resolved closure and live-state digests;
- integration explanation and blockers;
- the proposed construction mode/effect/subjects;
- authority requirements; and
- an ungranted construct projection that is not itself a valid effect-bearing
  v1 `FactoryRequest`.

`authority record` consumes the exact proposal artifact plus a separate human
decision record. It creates an exact repository grant/revocation record only
when all bindings match. The adapter later combines the proposal with one
explicitly supplied grant reference to create the existing valid v1 construct
request.

**Rationale**: Current v1 factory requests require authority and expected state
for committed effects, so an ungranted proposal requires its own public type.
This fills the real public handoff gap without weakening current construction.

**Alternatives considered**:

- Treat `construct --effect none` as preparation: rejected because current
  semantics correctly refuse that mismatch.
- Put grant issuance in `prepare`: rejected because preparation is effect-free.
- Let the adapter manufacture a grant: constitutionally prohibited.

## R008 — Adapter executable and extension packaging

**Decision**: Add one `net10.0` framework-dependent executable project,
`ProgramKit.SpecKitAdapter`. It references only `ProgramKit.Contracts` from the
Program Kit product graph plus exact generic parsing/schema dependencies. It
must not reference Kernel, DotNet provider, SessionIntegration, tests, `eng/`,
or private Spec Kit modules.

The repository stores extension source under
`extensions/orbyss-program-kit-adapter/`. Packaging publishes the adapter once,
copies the closed runtime dependency set and schemas into a staging extension,
and produces one versioned archive. No generated binary is checked into source.
Tests install the staged package through `specify extension add ... --dev`;
published proof installs the archive/catalog release without `--dev`.

**Rationale**: This realizes the accepted replaceable consumer-only boundary
and uses the same binary on Windows and Linux.

**Alternatives considered**:

- Prompt-only extension: rejected because deterministic translation and
  validation would be unproved.
- Python adapter: rejected because it introduces another runtime and duplicate
  contract implementation.
- Put adapter code in SessionIntegration: rejected because Spec Kit is an
  orchestrator adapter, not an AI session provider.

## R009 — Spec Kit 0.15.1 integration behavior

**Decision**: The extension manifest uses schema version 1.0, extension identity
`orbyss-program-kit-adapter`, version `0.1.0`, and exact
`requires.speckit_version: ==0.15.1`. It contributes the approved command set and
conditional `after_plan`, `after_tasks`, `before_implement`, and
`after_implement` hooks.

Spec Kit installation establishes only the **installed** state. The extension is
not considered available/compatible until base `doctor` validates the exact
workspace-local Program Kit release and base lock. This avoids pretending the
Spec Kit installer can authorize or activate an external factory.

The exact repository project configuration path is
`.specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml`.
The extension ships
`orbyss-program-kit-adapter-config.template.yml` beside it. The project file is
consumer-owned and version controlled; the `.local.yml` layer and environment
variable layer documented by Spec Kit are deliberately ignored by the adapter
for applicability, profile, ownership, effect, and authority decisions. Removal
uses Spec Kit's supported `--keep-config` path so this project file survives.

**Rationale**: Spec Kit 0.15.1 officially supports versioned extensions,
namespaced commands, hooks, project configuration, enable/disable/update/remove,
and manifest-aware upgrades. Its extension installer does not itself become a
Program Kit trust or authority provider.

**Alternatives considered**:

- Patch Spec Kit core templates/skills: rejected because upgrades could erase
  the integration.
- Use a custom workflow in V1: rejected because commands and hooks are enough.
- Use Spec Kit environment config as semantic default: rejected as ambient.

## R010 — Adapter commands and ownership behavior

**Decision**: Ship these final command identities:

- `speckit.program-kit.doctor`
- `speckit.program-kit.activate`
- `speckit.program-kit.disable`
- `speckit.program-kit.handoff`
- `speckit.program-kit.validate`
- `speckit.program-kit.prepare`
- `speckit.program-kit.explain`
- `speckit.program-kit.construct`
- `speckit.program-kit.evaluate`
- `speckit.program-kit.cleanup`

The adapter executable accepts one canonical adapter request file and emits one
adapter-result envelope. Commands may create absent seeded handoffs or
adapter-owned generated files. They do not rewrite an existing consumer-owned
config/handoff/review. A change to those files is applied by the human or agent
acting for the consumer, then revalidated. Cleanup deletes only unchanged
adapter-generated candidates proven by the adapter manifest.

**Rationale**: The extra cleanup command makes the design's separate explicit
cleanup boundary executable instead of hiding it in disable/remove.

**Alternatives considered**:

- Make disable imply cleanup: rejected as destructive and ownership-confusing.
- Give every command its own request schema: rejected as unnecessary surface;
  one discriminated adapter request remains exact and bounded.

## R011 — Handoff trace and staleness algorithm

**Decision**: The handoff contains explicit values; the adapter never derives
them from prose. Each output-affecting value has one trace binding to:

- a stable `FR-NNN` or `SC-NNN` block in `spec.md`;
- a stable named decision block in `research.md`/`plan.md`;
- a stable `TNNN` row in `tasks.md`;
- an explicit human handoff decision; or
- a fixed compatibility-manifest value.

For Markdown sources, the adapter resolves one exact named block and hashes a
canonical whitespace-normalized block. Whole-file bytes are provenance only.
Edits outside named blocks preserve evidence; a missing, duplicate, or changed
named block stales only target fields and their generated closure. Referenced
implementation bytes are hashed independently.

**Rationale**: This provides deterministic field-level invalidation without
claiming semantic inference from general Markdown.

**Alternatives considered**:

- Hash whole planning files: rejected because unrelated edits would trigger
  expensive false invalidation.
- Parse arbitrary prose semantically: rejected because it is heuristic.
- Trust filenames/headings without a stable identifier: rejected because they
  are ambiguous and refactor-sensitive.

## R012 — Canonicalization and safe publication

**Decision**: Reuse `program-kit.canonical-json/v1`, `System.Text.Json`, strict
JSON Schema 2020-12 validation, the existing restricted YAML intake rules, and
Program Kit logical-path/collision conventions. Adapter-owned outputs are staged
as a complete immutable set and atomically renamed only after validation.

Handoff YAML is human-authored; its canonical admitted projection is JSON.
Generated definitions, requests, results, manifests, reviews, locks, and
evidence use canonical JSON UTF-8/LF/no-BOM bytes. No generated/editable regions
share a file.

**Rationale**: These mechanisms already underpin the proved factory and avoid a
second canonicalization system.

**Alternatives considered**:

- YAML as canonical bytes: rejected because parser/emitter variation is wider.
- Per-file in-place writes: rejected because interruption could create partial
  trusted state.
- Reuse repository-wide digest generation on each command: rejected because
  only declared inputs should be hashed.

## R013 — Diagnostics and disclosure

**Decision**: The adapter owns a separate authority-qualified diagnostic catalog
with typed entries and direct production triggers. Its result embeds the exact
unmodified Program Kit JSON result when one was returned. It never parses or
rephrases rendered Program Kit prose.

All external tokens, exception data, stderr, secret-shaped values, and unsafe
paths enter the disclosure filter as withheld data. Child processes receive
exact argument arrays with shell execution disabled. Stdout must be one bounded
schema-valid JSON document; stderr is never copied into an ordinary result.

**Rationale**: This carries forward the repaired Feature 001/002 diagnostic
boundary and prevents the synthetic-catalog coverage problem from recurring.

**Alternatives considered**:

- Map Program Kit diagnostics to adapter IDs: rejected because it would obscure
  the authoritative factory result.
- Include stderr for troubleshooting: rejected because it is unclassified
  external output.

## R014 — Verification and evidence reuse

**Decision**: Extend the existing five verification tiers:

- **Edit**: affected build plus focused unit/schema/golden test;
- **Story**: relevant unit/contract and one focused consumer flow;
- **Pre-PR**: one isolated build, all unit/contract tests, formatting of changed
  files, and one local staged-extension smoke path;
- **CI**: full unit/contract/acceptance/evidence once on Ubuntu plus only the
  platform-sensitive packaged installation/lifecycle/end-to-end matrix on both
  Windows and Linux; and
- **Human**: three fresh guided consumer journeys after the exact CI candidate
  is green.

CI records claim inputs so unchanged evidence is reused. Documentation,
timestamps, branch heads, and unrelated digests do not invalidate factory
claims. Product/API/security/authority/runtime-semantic changes do invalidate
applicable human acceptance; proof-only changes do not unless claims change.

**Rationale**: This retains complete authoritative proof without running every
suite twice on every platform or locally before CI.

**Alternatives considered**:

- Full local gate after every story: rejected as redundant and slow.
- Run all test assemblies on both CI platforms: rejected because most contract
  logic is platform-neutral; only package/process/path/lifecycle proof needs the
  matrix.
- Trust only unit tests: rejected because package-only and human journeys are
  constitutional release evidence.

## Authoritative sources

- [Spec Kit 0.15.1 release](https://github.com/github/spec-kit/releases/tag/v0.15.1)
- [Spec Kit extensions reference](https://github.github.com/spec-kit/reference/extensions.html)
- `DESIGN-SPECKIT-ADAPTER.md`
- `.specify/memory/constitution.md`
- `src/ProgramKit.Cli/ProgramKit.Cli.csproj`
- `src/ProgramKit.Contracts/Schemas/operation-result.schema.json`
- `src/ProgramKit.Cli/Composition/ProgramKitComposition.cs`
- `eng/Invoke-Verification.ps1`
- `.github/workflows/vertical-slice.yml`
