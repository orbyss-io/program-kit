# Typed Console host generation validation report

## Result

The `1.0.0` review set and its exact approved implementation are complete. They
materialize the fully generated Spectre Console host, explicit .NET binding
compiler, host-kind-neutral generated-output integrity, safe refresh/repair
flow, and inert installable maintenance capability converged with the human
reviewer.

Canonical Architecture Design `2.0.0` instance:
`72bfa056c3e0f19d1765d9feae9aa5eb4ccb546a07896f2682a276294abcd4ca`.

Canonical Planning `3.0.0` instance:
`207c47c0150bb91df564937225fdbb44f30dd2b403f21c6468d6abac70fbe273`.

The human approved both exact digests together. PKTCH-W010 through PKTCH-W110
then completed without a material design deviation.

## Source truth and disposition

- Source commit:
  `60006928a7f29423dd777ee5971aa1431ea263cf` on `main`.
- The reusable C# build-gates implementation is integrated into that source
  truth.
- Static-conformance disposition `reuse-existing` is exact, schema-valid, and
  human-selected.
- The selected Program Kit private gate, current build-spine activation
  matrix, exhaustive verification profile, private selection lock, and
  materialized closure evidence are digest-bound.
- No new analyzer or C# gate is proposed. The existing public generated-source
  analyzer is selected only for generated consumer hosts.

## Validation performed

- Every review JSON file parsed successfully.
- `architecture-design.json` passed `JsonSchemaWorkbenchValidator` against
  `pkid:schema:program-kit:architecture-design@2.0.0`
  (`2698ce65a29cb0d5007b2ab1773d7e387385df7c8b72495804b292b6af696198`).
- `implementation-plan.json` passed `JsonSchemaWorkbenchValidator` against
  `pkid:schema:program-kit:implementation-plan@3.0.0`
  (`0f3b8f524b29ec7b5871ce411f06852e1b06326a5e1da616184627df0b5ea1b6`).
- `static-conformance-disposition.json` passed
  `JsonSchemaWorkbenchValidator` against
  `pkid:schema:program-kit:static-conformance-disposition@1.0.0`
  (`834902de4706a7c6859390bd7ee5e4fd6a3e7e455486348c02a1cb84604d15bd`).
- The focused schema checks ran in one temporary review-only Program Kit unit
  test and passed. The harness was then removed.
- Targeted semantic checks passed for domain/component/project/package
  ownership and references; exact requirement/trace equality; unique work
  units; known dependencies; `reuse-existing` gate state; materialized gate
  artifacts; exact per-unit activation/profile references; and closure
  reachability across every product work unit.
- Re-running `materialize-review-set.ps1` produced byte-identical JSON for the
  design basis, decision source, disposition, private selection lock,
  architecture design, and implementation plan.
- `dotnet restore ProgramKit.sln --locked-mode` passed.
- `dotnet build ProgramKit.sln --no-restore --maxcpucount:1
  --property:UseSharedCompilation=false` passed with the mandatory private C#
  gate, zero warnings, and zero errors.
- The Program Kit unit project rebuilt with the mandatory gate, zero warnings,
  and zero errors; its direct MSTest executable passed 502 of 502 tests.
- `git diff --check` passed.

The standalone `program-kit check` transport was attempted and correctly
returned `PKCLI004` because that Workbench operation adapter is not registered.
It is not cited as validation evidence.

## Authority and exclusions

Implementation did not publish packages, release or deploy Program Kit, modify
JTest, activate a provider wrapper in the Program Kit authoring workspace,
write user-global configuration, or grant autonomous authority. Package
publication, release qualification, promotion, deployment, JTest changes,
external repositories, and material architectural deviations still require
separate authority.

## Implementation closure

- The generated .NET host uses pinned Spectre.Console.Cli `0.55.0` as its sole
  token parser and native scalar binder. No second parser, untyped parse-result
  dictionary, or indirect command-routing layer exists.
- An isolated JTest-shaped fixture proves `run`, `validate`, and `describe`
  through three typed requests, three mandatory handlers, one optional
  validator, and one CShells feature. Actual child-process exit codes `17`,
  `23`, and `29` pass through unchanged.
- Wrong native input and consumer validation failures exit `2`; consumer
  validation prevents its handler; commands without validators invoke their
  handlers directly.
- Two generations produced byte-identical outputs.
- Generated-output integrity passed modified, missing, unexpected,
  consumer-owned-file, build-rejection, publication-rejection, and explicit
  quarantine/repair proofs without runtime source-tree verification.
- Locked restore and the full mandatory-gate solution build passed with zero
  warnings and errors. All `562` unit tests passed. Full conformance passed
  `171` tests with zero failures and one pre-existing opt-in Linux Keycloak
  skip.
- The exact capability bundle packed and verified, and explicit initialization
  into an isolated consumer produced five owned Codex wrappers. Source
  authoring and user-global initialization remain fail-closed.
- `dotnet format ProgramKit.sln --no-restore --verify-no-changes` passed.
- Detailed immutable evidence is recorded in
  `implementation-evidence/closure.json`.
