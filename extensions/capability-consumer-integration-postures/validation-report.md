# Capability consumer integration postures validation report

## Result

The candidate review set is coherent, schema-valid, and semantically valid.
It is ready for an exact human design-and-plan decision and authorizes no
implementation by itself.

Canonical candidate digests:

- Architecture Design `2.0.0`:
  `666cf457a32702cd8ecf29fbdf412a99bd7187e953c5e1696d82bd4d6fa9d1b0`;
- Planning `3.0.0` implementation plan:
  `2d9bbfe4d45289322fad65c7971dce2618be43197f31ca3b64cf5831d334106e`;
- Static Conformance Disposition `1.0.0`:
  `aa422e16ebbfc5fb038a29adbfd5d9072122292543f82b07ca9e8c87cbb340af`;
- private-gate selection lock:
  `1cfb2a26ecf273cacae5062f04c4f42e95eb88e08323998a99a8d6aa6ad4291a`.

## Source reconciliation

The Program Kit source baseline is commit
`00ab82b33061495a90d2e8c2e6bfec669828e370`; the parent Domain Semantic
Engine baseline is commit `e3eb7f0b68a300a4df5995fa9598b7940e69c7ab`.

The exact inspected capability manifest, provider documentation, initializer,
single-provider lock, command catalog, unit tests, and delivery conformance
bytes are recorded in `source-baseline.json`,
`sha256:2487c2f242199996536deca8e02904b3dd8d10b4cd082338f6fd6883eb0859f9`.

That baseline establishes:

- finite current Codex and Claude provider support;
- current Codex `.codex/skills` and Claude `.claude/skills` output;
- a version `1.0.0` lock that records only the latest initialized provider;
- preservation of earlier provider wrapper bytes without preserving their
  ownership evidence;
- no exact provider-removal command;
- pending parent consumer initialization to CapabilityBundle `3.0.0`.

The unrelated dirty `web-publication-static-react` implementation, package-lock
changes, and other human work in the Program Kit and parent worktrees were
preserved and excluded as design authority.

## Provider contracts

Official Codex and Claude Code documentation was read on `2026-07-30` and
recorded in `provider-contract-evidence.json`,
`sha256:49417e246aad9d54ce3c543fd79be857d6e6bd6186ee00359028fc91dea01b3f`.

The design selects:

- Codex repository skills at `.agents/skills`;
- Claude Code project skills at `.claude/skills`;
- legacy Codex `.codex/skills` only as exact ownership-verified migration
  input.

The evidence grants no installation, trust, permission, registration,
execution, Git-policy, or runtime authority. Every affected implementation
unit must recheck the official provider contract and stop on material drift.

## Schema and semantic validation

A temporary review-only unit test used the repository's compiled validators.
The test and its three primitive JSON converters were removed after execution.

Passed:

- `architecture-design.json` through `JsonSchemaWorkbenchValidator` against
  `pkid:schema:program-kit:architecture-design@2.0.0`, schema SHA-256
  `2698ce65a29cb0d5007b2ab1773d7e387385df7c8b72495804b292b6af696198`;
- `ArchitectureDesignV2Validator` over `ArchitectureDesignValidator` and
  `ArtifactDecisionValidator`;
- `implementation-plan.json` through `JsonSchemaWorkbenchValidator` against
  `pkid:schema:program-kit:implementation-plan@3.0.0`, schema SHA-256
  `0f3b8f524b29ec7b5871ce411f06852e1b06326a5e1da616184627df0b5ea1b6`;
- `ImplementationPlanDocumentV3Validator` over
  `ImplementationPlanDocumentValidator`;
- `static-conformance-disposition.json` through
  `JsonSchemaWorkbenchValidator` against
  `pkid:schema:program-kit:static-conformance-disposition@1.0.0`, schema
  SHA-256
  `834902de4706a7c6859390bd7ee5e4fd6a3e7e455486348c02a1cb84604d15bd`;
- exact stable-order equality of the 12 requirement IDs and 12 trace records.

The focused observation was:

```text
passed CandidateReviewSetPassesCurrentSchemaAndSemanticValidators
total: 1, failed: 0, succeeded: 1
```

Compilation of the temporary validator harness passed the mandatory private
Program Kit C# gate. An initial harness location and type layout were correctly
rejected by the gate and were corrected before the passing validation. A
`dotnet test` filter invocation then reported zero tests because of the current
test-platform transport; the directly executed current test application found
and passed the exact test and is the cited result.

## Trace, gate, and projection integrity

Passed:

- every plan design reference equals the exact canonical design digest;
- `PKCI-R001` through `PKCI-R012` each have exactly one stable-order trace;
- seven unique work units form the exact serial dependency chain
  `PKCI-W010` through `PKCI-W070`;
- the closure unit transitively reaches all six product work units;
- every work unit binds the exact current activation matrix and verification
  profile;
- the plan and design bind the same exact static-conformance disposition;
- the disposition, materialized gate, materialized selection lock, and
  materialized existing activation evidence agree with `reuse-existing`;
- reviewer Markdown names the exact canonical design and plan digests;
- all review JSON parses successfully.

## Static-conformance decision

The human-selected disposition is `reuse-existing`.

- gate:
  `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`,
  `e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1`;
- activation matrix:
  `bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b`;
- verification profile:
  `80978c4209e5119c8df468f47f972ea8dc622bbeb907681e48721d5d8f12738d`;
- existing activation evidence:
  `c4b247449959317dd95eca5aab4baf61d709ff27155e84cae0a9d111f0e4b09b`.

The selection applies only to Program Kit-owned C#. It creates no new gate,
extends no analyzer, and attaches no private gate to consumer-owned source.
Provider discovery, filesystem ownership, Git posture, clean-session behavior,
migration, and removal remain executable-test and human-review obligations.

## Deliberately not performed

- No initializer, remover, lock, provider registry, adapter, capability bundle,
  consumer wrapper, README posture, hook, MCP binding, runtime, or package
  behavior was implemented.
- No `.gitignore`, Git index, commit, provider-global configuration, trust,
  permission, credential, or user-home state was changed.
- No provider process or AI development procedure was started.
- No package was published and no release or deployment was performed.
- No full solution suite, clean-checkout provider discovery, or runtime
  dependency closure is claimed at design time; those are exact
  `PKCI-W070` implementation outcomes.
- No human approval of the canonical design and plan digests is inferred from
  prior conceptual approval.

## Approval boundary

Implementation may start only after a human explicitly approves both exact
canonical digests together:

```text
design sha256:666cf457a32702cd8ecf29fbdf412a99bd7187e953c5e1696d82bd4d6fa9d1b0
plan   sha256:2d9bbfe4d45289322fad65c7971dce2618be43197f31ca3b64cf5831d334106e
```

Any material change to either canonical artifact requires new validation,
digests, and human approval.
