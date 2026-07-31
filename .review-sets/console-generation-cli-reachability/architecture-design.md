# Console generation CLI reachability design

Artifact identity:
`pkid:design:program-kit:console-generation-cli-reachability@0.1.0-alpha.1`.

State: `ready-for-human-decision`.

## Intent

Make the existing typed .NET Console host generator reachable through the
backed Program Kit `dotnet generate-host` and `dotnet refresh-host` journeys.
The fix must preserve exact-input, digest, containment, no-scan, and
human-started execution boundaries.

This is an urgent bounded amendment outside the approved
`PKAV-W010` through `PKAV-W070` alpha-transition work units. It does not alter
those work-unit boundaries.

## Current source truth

- `DotNetHostGenerationCommandService` resolves the selected Open Console
  document but constructs `DotNetHostGenerationInput` without
  `ConsoleGeneration`.
- `DotNetHostGenerationCoordinator` correctly requires a non-null
  `DotNetConsoleGenerationInput` for a Console host.
- The Console generator already validates a typed binding, verifies the exact
  consumer reference assembly, projects the document, compiles the candidate
  against exact references, and emits deterministic generated output.
- `dotnet generate-host` has no option or manifest binding for those inputs.
- `dotnet refresh-host` delegates to the same command service, so it inherits
  the same unreachable path.
- The command end-to-end test has API and Worker rows only. Its dormant Console
  branch demonstrates the missing journey rather than proving it.

## Decision

Extend the artifact-input manifest contract with a finite
`consoleGenerations` collection. Each entry binds exactly one host identity to:

1. one exact Console binding-document revision;
2. one exact consumer reference-assembly revision; and
3. an initialized, duplicate-free, ordinally stable collection of exact
   compilation-reference revisions.

Every referenced revision must occur exactly once in the existing `inputs`
allow-list. The existing resolver verifies the listed relative path,
containment, bytes, and SHA-256 before the command service creates
`DotNetConsoleGenerationInput`. The service derives physical paths only from
those verified manifest entries and the explicit manifest read root.

The binding document's Open Console revision must equal the selected host
document revision. Its consumer reference-assembly relative path and digest
must equal the resolved consumer entry. The consumer assembly must occur
exactly once in the compilation-reference set. Resolved compilation paths must
be unique and are passed to the generator in ordinal order.

The existing `--artifact-manifest` argument is the only CLI surface needed.
Refresh already carries the exact artifact-manifest path in its committed
request, so the same manifest closes both journeys without a second source of
truth. API and Worker generation continue to use their current inputs.

## Contract identity and migration

The existing
`pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0` bytes remain
immutable. A new
`pkid:schema:program-kit:dotnet-artifact-input-manifest@0.1.0-alpha.1`
contract owns `consoleGenerations`.

The model can read both contracts. API and Worker callers may continue using
the legacy contract. A selected Console host fails early and clearly unless
the manifest selects the alpha contract and supplies exactly one matching
Console entry. This is a repair of an unreachable CLI journey, not a claim
that legacy Console CLI generation ever worked.

Migration cannot invent consumer build output or compiler references. The
consumer must build its contract project, write the exact binding, enumerate
the finite reference set, calculate the digests, and update the manifest.
Program Kit then validates every byte and fails closed on stale input.

This transitional review set does not create another high-major Architecture
Design or Implementation Plan schema instance. The durable Program Kit
Architecture Design and Implementation Plan contract identities remain owned
by `PKAV-W020`, which will establish `0.1.0-alpha.2` and
`0.1.0-alpha.3`. The identities of this design and its plan are separate
pre-stable review-artifact identities.

## Invariants and failure behavior

- No current-directory, solution, output-directory, runtime-pack, assembly, or
  package-feed scan is introduced.
- No path supplied only by a Console binding becomes readable. Every file must
  also be an exact manifest input below the explicit manifest root.
- Missing, default, duplicate, unordered, cross-host, stale, digest-mismatched,
  path-mismatched, or uncontained Console inputs fail before output mutation.
- API and Worker behavior and their legacy manifest journey remain unchanged.
- Generated-output collision and integrity sealing behavior remains unchanged.
- Refresh continues to create a candidate and uses its existing atomic
  compare/replace/repair semantics.
- The CLI and refresh service do not build the consumer unless the existing
  explicit refresh `--build-consumer` authority was supplied.
- No package publication, release, promotion, JTest mutation, consumer
  migration execution, or capability change is authorized.

## Journey

```text
explicit shell + selected host + exact artifact manifest
  -> resolve exact selected host document
  -> Console?
       no  -> existing API/Worker generation
       yes -> require one host-keyed consoleGenerations entry
           -> resolve and hash binding + consumer assembly + references
           -> cross-check document, path, digest, uniqueness, and order
           -> construct DotNetConsoleGenerationInput
  -> existing coordinator and typed Console generator
  -> existing integrity seal
  -> generate-host result or refresh candidate
```

## Static conformance disposition

Disposition: `reuse-existing`.

The selected gate remains:
`pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`
with digest
`sha256:e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1`,
activated by
`pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`
with digest
`sha256:bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b`.

It covers Program Kit-owned C# source structure. Schema/model agreement,
exact-input negative cases, CLI reachability, and refresh behavior remain
executable test obligations. No new analyzer or gate extension is justified
for this bounded adapter repair.

## Acceptance

- The Console command end-to-end row runs the real composed CLI and emits a
  valid integrity-sealed typed Console host.
- A real refresh journey creates the same Console host from a committed
  request and the same exact manifest, then reports unchanged on repetition.
- Negative tests prove missing/duplicate/stale/mismatched/uncontained inputs
  fail before output mutation.
- Schema registration and model-schema conformance include the new alpha
  contract while preserving the legacy bytes.
- The mandatory private C# gate, focused unit tests, and repository conformance
  profile pass.

## Deliberately outside this amendment

- The remaining alpha-version transition work units.
- The broader routing and capability-contract audit.
- Publication of additional reusable analyzers.
- JTest repository edits or automatic migration.
- Redesign of generated Console project-reference placement during local
  application publication. This amendment makes the shared generation service
  reachable; it does not claim a new local-publish topology.
