# Program Kit consumer contract-surface hardening implementation plan amendment

Artifact identity:
`pkid:plan-amendment:program-kit:consumer-contract-surface-hardening@0.1.0-alpha.1`.

Implements only the exact architecture amendment
`pkid:design-amendment:program-kit:consumer-contract-surface-hardening@0.1.0-alpha.1`.

State: `ready-for-human-decision`.

No work unit in this plan is authorized until the human approves the exact
design and plan SHA-256 digests. The completed PKCJ-W010/PKCJ-W010A bytes and
the `0.1.0-alpha.2` package handoff remain immutable.

## Source and version basis

- source commit:
  `e206f8cbfc2e61e909b18d7a3b91cc04a8d51a35`;
- completed base design:
  `9d336e3015daa8a8ec771d8e8aacc29020175a10174df7964d23088656468648`;
- completed base plan:
  `1e0d8b2090445e327459767a8360d11f48acf6b394516d87b4a5c2c586180246`;
- completed Console amendment design:
  `9fb6d810dd89232135d048dd54ebfba8d67ac45a46704d7855ef466c0ebb787f`;
- completed Console amendment plan:
  `7303ca2ba0c096d98e71b6cd3474ace8e350a0b9cff72d1d24e9993ebdc98621`;
- current immutable package release:
  `0.1.0-alpha.2`;
- proposed coordinated implementation candidate:
  `0.1.0-alpha.3`, selected only by repository source before implementation.

## Work-unit graph

```text
PKCJ-W020 strict JSON diagnostics
          |
          v
PKCJ-W030 PKID + schema/design-flow closure
          |
          +------------------+
          |                  |
          v                  v
PKCJ-W040 Console       PKCJ-W050 C# gate
contract/scaffold       lock/target
          |                  |
          +--------+---------+
                   |
                   v
PKCJ-W060 manifest-driven feed pack
                   |
                   v
PKCJ-W070 coordinated package-only proof
```

Each completed work unit is one bounded commit pushed promptly. A later unit
must not conceal a failed earlier acceptance condition.

## PKCJ-W020 — strict typed JSON failure provenance

### Scope

1. Add one metadata-backed strict-read failure locator to
   `Orbyss.ProgramKit.Serialization.JSON`.
2. Preserve `JsonException.Path` and enrich it using the selected
   source-generated `JsonTypeInfo`; do not use unbounded reflection or parse
   implementation-specific exception prose.
3. Represent the first exact failure as RFC 6901 path, member name, expected
   CLR type, and reason.
4. Update `ProgramKitJsonException` construction so its
   `ProgramKitDiagnostic.Path` is exact.
5. Update `CommandApplication`, `ConsoleInputMaterializer`, NuGet lock reads,
   and every other strict-reader adapter to compose, not overwrite, the
   serializer path.
6. Keep the public command diagnostic envelope unchanged; use the exact stable
   message form from the design.
7. Add generic serializer tests plus command/materialization tests for every
   failure category.

### Acceptance

- The 57 KB Console request fixture with one deeply nested invalid value emits
  PKCIM001 at the exact pointer and names the JSON member and expected CLR type.
- Missing required, null, wrong scalar, wrong object/array, invalid enum/PKID,
  unknown member, and root failures all satisfy the contract.
- Diagnostics never echo the complete document, absolute paths, or sensitive
  values.
- Existing successful reads and canonical writes are byte-identical.
- Focused build, unit tests, and the repository static gate pass.

### Stop conditions

- Stop if exact type/member location requires parsing runtime exception prose.
- Stop if implementing the contract requires a breaking diagnostic-envelope
  change not described by the approved design.

## PKCJ-W030 — canonical PKID and schema dependency closure

### Scope

1. Implement the exact four-segment/dotted-name PKID grammar once and use it
   from `ProgramKitIdentifier`, its converter, validators, and diagnostics.
2. Add Artifact Definitions `0.1.0-alpha.2` with the exact canonical pattern.
3. Replace divergent PKID definitions in new current-writer schema revisions
   with exact references/compositions over Artifact Definitions alpha.2.
4. Add `diagnostics explain PKART001` grammar, positive examples, and failure
   examples.
5. Add Static Conformance Disposition alpha.2, Architecture Design alpha.3,
   and Implementation Plan alpha.4 schemas/models/migrations. Each current
   writer requires the exact `$schema` property.
6. Preserve all earlier versioned bytes and readers. Add deterministic
   loss-rejecting migration fixtures and compatibility metadata.
7. Replace the special C# gate composite module with a generic transitive
   closure provider based on `SchemaCatalog` registered dependencies.
8. Route `validate`, `artifacts inspect`, C# gate schema validation, and
   schema-backed commands through that provider.
9. Add optional exact `--schema` selection to `validate` for immutable legacy
   documents without `$schema`.
10. Add module/source digest, dependency-closure, parser/schema parity, and
    design-flow document regressions.

### Acceptance

- `pkid:approval-record:jtest:jtest-2.0` is accepted by runtime and every
  current-writer schema that accepts a general PKID.
- Uppercase, underscore, repeated/trailing dot or hyphen, empty/extra segments,
  and parser/schema disagreement fail.
- `schemas read` and `diagnostics explain PKART001` expose the same exact
  grammar.
- Architecture Design alpha.3 and Implementation Plan alpha.4 validate their
  cross-module artifact references offline through both `validate` and
  `artifacts inspect`.
- Static Conformance Disposition alpha.2 accepts its required exact `$schema`
  and rejects unknown properties.
- A legacy alpha.1 disposition validates only through exact explicit schema
  selection; its bytes are unchanged.
- Missing/unregistered/network `$ref` values fail closed.
- Full schema pin-versus-source conformance remains green.

### Stop conditions

- Stop on any requirement to alter a prior versioned schema byte.
- Stop if schema closure would require assembly discovery, directory search,
  or network resolution.
- Stop if migration cannot retain every source semantic value.

## PKCJ-W040 — Open Console style, examples, and request scaffolding

### Scope

1. Add the versioned Open Console contract-style catalog and the finite
   `dotnet describe-console-contract --format text|json` descriptor/operation.
2. Add Open Console alpha.2 typed/schema contracts with:
   - distinct positive host exit-code roles;
   - exact per-command request/result/diagnostic schema sets;
   - non-null stream schema revisions; and
   - current parsing/type/binding rules.
3. Replace `ContainsOrAbsent` result validation for alpha.2 with exact set
   reconciliation. Keep the exact 1.0.0 reader behavior immutable.
4. Add Console materialization request alpha.2 and a deterministic old-reader
   compatibility/migration boundary.
5. Add the Console command-sketch alpha.1 model/schema/validator.
6. Add
   `dotnet scaffold-console-request <sketch> --workspace-root
   --consumer-project --output`.
7. Derive only mechanical product structure, mirrored sets, ordering, and
   digests. Do not inspect source, restore, build, or infer consumer semantics.
8. Preflight the complete final request through schema and strict typed reads;
   write BOM-less staging bytes and atomically promote to a new output.
9. Promote a complete valid request example and command-sketch example into
   the capability resource allow-list.
10. Rewrite the Console materialization guide from the shared catalog and
    include complete integration-project, handler/implementation/validator,
    scaffold, materialize, generate, verify, and troubleshooting journeys.
11. Bind the new resources to the capability closures named in the design and
    update manifest digests.

### Acceptance

- Text and JSON describe output are deterministic projections of the same
  catalog and enumerate all five requested semantic rules.
- Host-role collision/zero, incomplete/duplicate exit map, null stream schema,
  wrong repeated CLR type, and request/result/diagnostic set superset/subset all
  fail with paths.
- The exact packaged examples are retrievable through
  `capabilities read-resource` and are validated/built in an isolated fixture.
- A small complete sketch plus one exact project produces the canonical
  materialization request twice at identical bytes.
- The scaffolder refuses placeholders, missing semantics, scans, escaping
  paths, existing output, stale artifact digests, BOM/invalid input, and
  interrupted promotion without partial output.
- The scaffolded request succeeds through materialize-console-inputs and
  generate-host without hand-authored mirrored contract data.

### Stop conditions

- Stop if the sketch must infer an operation, identity, schema meaning,
  authority, handler contract, or business value from source.
- Stop if Open Console alpha.2 cannot represent exact result sets without a
  further approved shape change.

## PKCJ-W050 — selection-lock scaffold and generated verification target

### Scope

1. Add the C# gate lock-intent/scaffold request alpha.1 contract.
2. Add `csharp-gate scaffold-lock <definition> <lock-intent>
   --repository-root --output`.
3. Centralize activation, expected-receipt, artifact-reference, inventory, and
   lock ordering keys in one exact component used by validators, definition
   materialization, scaffold, bind, and description.
4. Derive local assets, expected receipts, canonical ordering, input digest,
   and output digest exactly as specified by the design.
5. Add the selection-lock alpha.1 typed/schema contract and make scaffold and
   bind recompute both digests.
6. Expand `csharp-gate describe-definition` with:
   - activation and receipt composite keys;
   - ordinal code-unit ordering and the observed punctuation example;
   - digest projections;
   - expected-receipt derivation; and
   - generated-project target/package ownership.
7. Make PKCG002 ordering diagnostics name the exact key and first adjacent
   mismatch.
8. Generate one shared non-empty `Directory.Build.targets` for Console,
   API, and worker hosts. Define the configuration target and
   `ProgramKitVerifyGeneratedProject` no-restore Build entry point.
9. Prove interaction with
   `Orbyss.ProgramKit.GeneratedOutputIntegrity.Build` and an enabled
   `Orbyss.ProgramKit.CSharpBuildGates.Build` generated-output activation.

### Acceptance

- One exact definition/intent/repository state produces a byte-deterministic
  complete bind request.
- `inputDigest`, `outputDigest`, expected receipts, and all orderings are
  recomputed and tamper-detected by scaffold and bind.
- `cli-tests|...` is accepted before `cli|...`; reversed order reports both the
  composite key and adjacent values.
- Missing, duplicate, stale, changed, escaping, or unowned local assets fail
  without output.
- Generated Console, API, and worker targets are byte-equal and invoke
  `ProgramKitVerifyGeneratedProject` successfully with `/restore:false`.
- The target executes integrity verification and the configured
  generated-output C# gate row, producing the expected receipts.

### Stop conditions

- Stop if the target requires a new host/gate binding contract beyond the
  approved generated targets and existing package imports.
- Stop if receipt identity requires a semantic value absent from lock intent.
- Stop rather than scan for analyzer assets or repository state.

## PKCJ-W060 — manifest-driven coordinated local feed

### Scope

1. Add a canonical repository release-package manifest enumerating exact
   package ID, project path, role, coordinated-version requirement, and
   first-party dependency closure for the current 29 packages.
2. Add conformance proving every packable coordinated first-party project is
   represented exactly once and no non-selected project is packable by the
   release operation.
3. Extend `ProgramKit.Pack.proj` with one manifest-selected aggregate pack
   target using bounded parallel MSBuild and explicit
   `NoRestore=true;NoBuild=true`.
4. Add
   `build/Invoke-PackConsumerFeed.ps1 -OutputRoot <new-dir>`.
5. Run one locked/audited restore and one build before aggregate pack.
6. Inspect output for exact ID/version/file/content/dependency closure and emit
   a flat-feed manifest plus SHA-256 sums.
7. Change `Invoke-ConsumerCliColdProof.ps1` to consume the canonical manifest
   rather than a separate hard-coded 29/package/version rule.
8. Document the source-contributor local-feed journey in README without
   changing the release-asset consumer journey.

### Acceptance

- Instrumented tests prove one restore, one build, and one aggregate pack
  invocation; no project pack can restore or rebuild.
- Output contains exactly the manifest-selected package set at the canonical
  `0.1.0-alpha.3` version and no extra bytes.
- Missing/extra package, ID/version mismatch, dependency-closure mismatch,
  existing output, failed restore/build/pack, and partial output fail closed.
- The script changes no global NuGet configuration and publishes nothing.

### Stop conditions

- Stop if package correctness requires disabling lock, source mapping, audit,
  package inspection, or gate verification.
- Stop if a project must restore or build during pack; repair the aggregate
  build graph rather than documenting the slow loop.

## PKCJ-W070 — coordinated alpha.3 package-only proof and handoff

### Scope

1. Run formatting, Release build, all unit tests, all routine conformance
   tests, all schema/digest tests, and the complete private C# gate profile.
2. Pack the exact coordinated alpha.3 feed only through W060.
3. Inspect the CLI tool package, first-party dependency closure, embedded
   capabilities/resources/schemas, and generated build packages.
4. Install the CLI from only the flat feed into an isolated tool path with
   isolated NuGet cache/config and reviewed external sources.
5. Initialize Codex and Claude, verify the lock, and retrieve every capability
   and supporting resource at exact bytes.
6. Run strict diagnostic, PKID, schema read/explain, design-flow validation,
   Console describe/scaffold/materialize/generate/verify/build, gate
   describe/scaffold/bind/generated-project-verify, and tamper negatives.
7. Prove no Program Kit checkout, project reference, source capability path,
   test fixture path, custom helper, or hand-authored reference closure exists
   in the isolated consumer.
8. Produce a deterministic ZIP and checksum in a bounded local temporary
   handoff directory only. Do not publish it.
9. Record exact package, ZIP, command, capability, schema, generated target,
   and evidence digests in the review manifest after completion.

### Acceptance

- Every prior work-unit acceptance condition passes against package-installed
  alpha.3 bytes.
- The full cold journey starts from a small Console sketch and consumer source,
  not a pre-canned materialization request.
- Design-flow documents validate through both public validation paths.
- Modified example/resource/schema/package/wrapper/request/lock/generated
  target bytes all fail at the correct boundary.
- The local downloadable ZIP and a concise JTest prompt are produced only
  after all verification succeeds.

### Stop conditions

- Stop on any package/source/project-reference leakage.
- Stop on any mismatch between source, package, resource, schema, lock, or
  generated bytes.
- Stop rather than publish to GitHub, NuGet.org, GitHub Packages, or another
  feed.

## Verification profiles

Every work unit runs its focused tests plus:

```text
dotnet restore ProgramKit.sln --configfile NuGet.Config --locked-mode
dotnet build ProgramKit.sln -c Release --no-restore
dotnet test ProgramKit.sln -c Release --no-build --no-restore
build/Invoke-CSharpGateTestPlan.ps1
```

Where a focused command can reuse an already verified restore/build it must do
so. W070 reruns the complete profiles from a clean bounded output/cache
boundary.

## Commit and approval boundaries

- Commit 1: PKCJ-W020 strict diagnostic provenance.
- Commit 2: PKCJ-W030 PKID/schema/design-flow closure.
- Commit 3: PKCJ-W040 Console contract and scaffolding.
- Commit 4: PKCJ-W050 gate lock and generated target.
- Commit 5: PKCJ-W060 feed manifest/packer.
- Commit 6: PKCJ-W070 final proofs, review evidence, local package handoff, and
  JTest prompt.

Only review artifacts are created before approval. Implementation begins only
after the human approves the exact design and plan digests and authorizes
PKCJ-W020 through PKCJ-W070.

Material deviation includes any need to:

- change an immutable prior schema/package byte;
- alter the canonical PKID grammar;
- merge host exit-code roles;
- infer consumer semantics;
- scan ambient consumer state;
- add a new gate per design;
- add a host/gate binding contract not described by the design;
- weaken restore, audit, schema, package, or gate verification; or
- publish packages or releases.

On material deviation, preserve the current work-unit boundary, update the
review set, validate new exact bytes, and stop for human approval.
