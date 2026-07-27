# Typed Console host generation validation report

## Result

The `1.0.0` review set is a validated approval candidate. It materializes the
fully generated Spectre Console host, explicit .NET binding compiler,
host-kind-neutral generated-output integrity, safe refresh/repair flow, and
inert installable maintenance capability converged with the human reviewer.

Canonical Architecture Design `2.0.0` instance:
`6014341c0a94aaf7dd58f5d90adb82915ce60bf36455403a3084d67ee6231f1b`.

Canonical Planning `3.0.0` instance:
`9e53b1b6bbd91b0f5262bf4643f899fb9c1ac7ae3dd1c60e92512dd0e598223b`.

Implementation remains blocked until the human explicitly approves those two
exact digests together.

## Source truth and disposition

- Source commit:
  `65a102b83dd35cc16fb433793e49c25e0f4c098f` on `main`.
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

The review set does not implement runtime or generator code, publish packages,
release or deploy Program Kit, modify JTest, initialize a capability, activate
a provider wrapper, write user-global configuration, or grant autonomous
authority.

Implementation may begin only after exact design/plan approval and must follow
PKTCH-W010 through PKTCH-W110. Package publication, release qualification,
promotion, deployment, JTest changes, external repositories, and material
architectural deviations require separate authority.
