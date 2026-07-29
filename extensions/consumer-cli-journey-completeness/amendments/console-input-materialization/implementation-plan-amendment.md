# Program Kit Console input materialization implementation-plan amendment

Artifact identity:
`pkid:plan-amendment:program-kit:consumer-cli-console-input-materialization@0.1.0-alpha.1`.

Design amendment:
`pkid:design-amendment:program-kit:consumer-cli-console-input-materialization@0.1.0-alpha.1`.

Amends, without changing, the exact approved plan
`pkid:plan:program-kit:consumer-cli-journey-completeness@0.1.0-alpha.1`
with SHA-256
`1e0d8b2090445e327459767a8360d11f48acf6b394516d87b4a5c2c586180246`.

State: `ready-for-human-decision`.

This is the smallest additive amendment required by the JTest-discovered
Console input-authoring defect. The already authorized `PKCJ-W010` remains
incomplete and atomic. No implementation, cold-proof claim, package handoff,
commit, or push may proceed until the human approves the exact amendment design
and plan digests and authorizes `PKCJ-W010A`.

## `PKCJ-W010A` Close Console input materialization

Required outcome: the installed package-only Program Kit CLI transforms one
complete explicit consumer-owned Console materialization request plus one exact
consumer project build into the full canonical generation input closure, then
the existing packaged Console generator consumes it successfully.

Depends on:

- the existing uncommitted `PKCJ-W010` implementation candidate;
- the exact approved base design and plan digests named above; and
- compatible active Program Kit repository gate evidence for the
  `reuse-existing` disposition.

Atomicity: `PKCJ-W010A` is a required amendment slice inside the original
single-commit `PKCJ-W010` boundary. It must not land, package, or be handed to
JTest separately. Failure of this slice leaves the entire work unit incomplete.

Allowed edits:

- `src/Orbyss.ProgramKit.CommandLine/` for the finite command descriptor,
  request transport, strict serialization, contained process orchestration,
  transactional output ownership, diagnostics, help, and composition;
- `src/Orbyss.ProgramKit.DotNet/` for provider-neutral typed request/output
  contracts, project-build reference evaluation, binding/materialization
  mechanics, schema registration, validation, and deterministic rendering;
- `schemas/dotnet/` for immutable request and materialization-lock alpha.1
  schemas;
- `.agent-capabilities/` for the exact materialization guide, affected
  consumer capability/resource/schema closure declarations, troubleshooting
  diagnostics, and recalculated bundle/payload digests;
- focused unit/conformance fixtures and the package-only cold proof;
- root and CLI package READMEs for the exact supported command sequence;
- coordinated manifest/version/digest projections mechanically affected by
  these bytes; and
- this amendment's validation/report manifest after implementation.

Implementation obligations:

1. Register
   `dotnet.materialize-console-inputs` in the one finite descriptor catalog with
   positional request, required `--workspace-root`, required `--output`, and
   required valueless `--build-consumer`; project exact help and
   `commands describe` output from that descriptor.
2. Add strict source-generated
   `DotNetConsoleInputMaterializationRequest@0.1.0-alpha.1` and lock/evidence
   models plus their registered retrievable schemas. Reject unknown/duplicate/
   missing/defaulted values and all path escapes.
3. Represent shell, Open Console, and CLR binding semantics as explicit request
   intent. Populate no semantic field from source, metadata, naming
   conventions, provider guesses, or defaults.
4. Define and document the selected project as one consumer-owned Console
   integration project, separate from the generated host and not a
   contracts-only assembly. Require its exact selected reference assembly to
   contain every binding-visible request, public per-command handler interface,
   optional validator, validation result, Console `IShellFeature`, and public
   sealed concrete implementations. Publish the `I<Command>Handler` naming
   convention and exact
   `ValueTask<int> HandleAsync(TRequest, CancellationToken)` structural contract
   without guessing a metadata name.
5. Add the exact supporting resource
   `dotnet-console-input-materialization-guide`. It must contain one complete
   compiling `net10.0` class-library project file with exact
   `CShells.Abstractions` and
   `Microsoft.Extensions.DependencyInjection.Abstractions` references; complete
   request, `I<Command>Handler`, handler implementation, optional validator,
   validation-result, and `IShellFeature` sources; exact scoped registrations;
   the matching semantic-request example; and the ordered materialize then
   generate commands. State that a contracts/implementation project split is
   unsupported and must return to design rather than being silently inferred.
6. Preflight the complete request, workspace containment, authoring marker,
   project path, supplied artifact digests, output ownership, transaction
   state, framework/configuration/platform, and every prospective write before
   invoking the build.
7. Invoke only the exact project through the existing shell-free process
   runner as `dotnet build` with exact configuration/framework and
   `--no-restore`. Bind cancellation, exit code, and redacted diagnostics. Do
   not build a solution or weaken restore/source policy.
8. Query `TargetRefPath` and `ReferencePathWithRefAssemblies` from the same
   project evaluation and global properties through finite `dotnet msbuild`
   arguments. Parse only the documented machine-readable result and reject
   additional/unparseable output.
9. Verify one current managed consumer reference assembly and one complete
   finite managed compilation reference set. Form the generation compiler
   closure as the exact union of `TargetRefPath` and
   `ReferencePathWithRefAssemblies`, with the consumer reference exactly once.
   Detect missing, stale, changing, escaping, aliased, duplicate, and
   divergent-identity reference results.
10. Validate the complete Console integration seam from that selected assembly
    before promotion. Refuse absent or non-public request/handler/validator/
    validation-result/feature types, non-interface or generic handlers, any
    wrong `HandleAsync` signature, binding-visible implementations outside the
    selected assembly, or a contracts-only selection. Preserve the existing
    generated runtime audit for exact scoped unkeyed registrations.
11. Copy every exact assembly through a content-addressed staging path, verify
   the post-copy digest, and ordinally order the closure by managed assembly
   identity and digest without ambient directory/cache/feed scans.
12. Materialize and cross-validate canonical shell, Open Console, binding,
   supplied artifact copies, alpha.1 artifact manifest with one
   `consoleGenerations` binding, content-addressed references, and ownership
   lock. Reuse existing schema/semantic/metadata validators rather than
   duplicating their rules.
13. Implement transactional `created`, `unchanged`, `updated`, and `refused`
    results. Existing exact owned output must be re-evaluated against the
    current build before unchanged is reported. Modified/unowned/partial output
    is never silently repaired.
14. Ensure cancellation or failure promotes no partial Program Kit output and
    writes no ownership lock. Explicit ordinary consumer build outputs may
    remain and must be disclosed by help/evidence.
15. Add stable diagnostic/remediation entries for request, build, evaluation,
    reference, metadata, staleness, containment, collision, transaction, and
    authoring-workspace failures.
16. Add the embedded Console materialization guide and extend exactly the
    `design-software`, `maintain-software`, `implement-software-plan`, and
    `publish-dotnet-application-locally` knowledge closures with the command,
    guide, diagnostics, and all transitive schemas. Keep canonical knowledge
    read-only.
17. Update canonical procedures and README journeys so an agent retrieves the
    complete guide and request schema before designing or authoring the
    integration project or materializing inputs. Make explicit that the agent
    authors ordinary consumer-owned source but never edits Program Kit-owned
    materialized/generated bytes.
18. Replace the cold proof's `ConsoleFixtureRoot`/pre-canned-input dependency
    with consumer source plus one semantic request. The proof must install only
    from the 29-package flat feed, materialize inputs, run packaged Console
    generation, and verify the generated host.
19. Add positives for Codex/Claude capability and exact guide retrieval,
    help/describe/schema discovery, compiling the guide's project/source and
    matching request without repository fixture lookup, create/unchanged/
    update, deterministic clean roots, actual project reference evaluation,
    the exact public per-command handler interface seam, Console generation,
    and generated-host verification.
20. Add negatives for absent build authority, Program Kit authoring workspace,
    restore/build failure, stale supplied artifacts, missing/escaping/changing
    consumer or compilation references, duplicate path, divergent assembly
    identity, request duplicates, internal/class/generic/missing/wrong-signature
    handler contracts, contracts-only or split-project bindings,
    symlink/reparse escape, modified/unowned output, cancellation, and
    interrupted transaction.
21. Prove the materialized reference closure exactly equals the evaluated
    compiler closure and contains no source/project/solution/cache/feed path in
    promoted artifacts or portable evidence.
22. Recalculate every affected schema, capability, adapter, resource, bundle,
    payload, version-intent, testing-manifest, and compatibility-matrix digest
    without changing the exact approved base design/plan bytes or protected
    historical evidence.
23. Run format verification, solution build with zero warnings/errors, the
    complete unit suite with at least 584 tests, routine conformance, exhaustive
    repository gate, capability/payload verification, package-content and
    dependency-closure inspection, and the amended package-only cold proof.
24. Discard the incomplete pre-amendment local package candidate as
    non-deliverable; build a fresh exact 29-package alpha.2 feed only after all
    source and digest bytes are final.
25. Create the final flat-feed ZIP, package/asset manifest, `SHA256SUMS`, ZIP
    checksum, and JTest prompt. The prompt must select the actual active provider
    and exercise materialize-to-generate without a custom helper or pre-canned
    inputs.
26. Review the combined diff against the base and amendment allow-lists, create
    one understandable atomic commit for `PKCJ-W010` plus `PKCJ-W010A`, and push
    that exact commit to `origin/main`.

Verification evidence:

- exact descriptor/help/schema/knowledge-closure tests;
- strict request/lock serialization and semantic validation tests;
- exact Console integration-project topology, per-command handler contract,
  implementation ownership, and generated registration tests;
- an executable conformance projection proving the retrieved guide's exact
  class-library project, sources, package versions, request, and command
  sequence remain complete and buildable;
- contained process argument and cancellation tests;
- real project build and evaluated reference-closure evidence;
- deterministic materialization and transaction/ownership receipts;
- package-only materialize-to-generate-to-verify proof;
- 29 exact coordinated `.nupkg` files at `0.1.0-alpha.2`;
- package manifest and SHA-256 evidence;
- zero Program Kit checkout, custom helper, project reference, or pre-canned
  Console input in the cold consumer; and
- full gate/test counts and pushed commit identity.

Stop conditions:

- stop before implementation unless the exact amendment design and plan
  digests and `PKCJ-W010A` are explicitly approved;
- stop if MSBuild cannot return the complete compiler reference closure through
  one finite exact-project query without a scan or custom consumer helper;
- stop if a semantic value would have to be inferred rather than supplied;
- stop if containment, stale-input detection, no-partial-output behavior, or
  complete package-only cold proof would require weakening;
- stop on any product version change, restore/feed mutation, publication,
  GitHub Release, JTest mutation, or unrelated health-patch work; and
- stop on any material architecture beyond this exact additive amendment.

Compatibility:

- the coordinated product remains the not-yet-delivered
  `0.1.0-alpha.2` candidate;
- existing `dotnet generate-host` and alpha.1 artifact-manifest contracts remain
  unchanged;
- the request and lock schemas begin at independent
  `0.1.0-alpha.1` revisions; and
- no base approved design/plan byte is modified or superseded.

Static conformance:

- disposition: `reuse-existing`;
- gate:
  `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`,
  `sha256:e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1`;
- activation matrix:
  `pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`,
  `sha256:bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b`;
- scope: the gate is established once at Program Kit repository scope; this
  amendment references that compatible active binding and creates no per-design
  gate.

This amendment does not authorize package/feed publication, GitHub Release
creation, release/version selection, JTest mutation, or any other health-patch
work.
