# ProgramKit Development Tools replacement review validation

## Result

The canonical Architecture Design `2.0.0`, Planning `3.0.0` implementation
plan, and `StaticConformanceDisposition@1.0.0` validate against their exact
ProgramKit schemas and semantic validators.

Canonical candidate digests:

- design:
  `918db6923687e0098d2b5c59936714c4f804235dfa18299bd6d6830535c7d5cb`;
- plan:
  `051f5ad4ce778b404707e9b9c94445c36677ffa235320c8aa3665b9445b53e56`;
- disposition:
  `6092894ece0f6691dcd59a27ca24eb6365bac2c01739a54bfb45856a86960697`;
- private-gate selection lock:
  `66a62b56eea04e09fc905f6074cc991b88096648415ffa670c7a8641bd1edde4`.

These bytes are candidates for human approval. They are not approved by this
report and authorize no implementation.

## Source reconciliation

The design source baseline is ProgramKit commit
`ce97d8601523b9112207a6a05fd9fb6bb7c56f83`.

At that baseline:

- neutral Open Console ownership is implemented at
  `schemas/open-console/open-console-1.0.0.schema.json`, SHA-256
  `f8e5128e6c81ad7f9e6d2ae43beb345c5c404bf4cf6f6bfa6ed1bfbe796cb780`;
- the exact .NET Console binding contract is implemented at
  `schemas/dotnet/dotnet-console-binding-1.0.0.schema.json`, SHA-256
  `d5db01326609f83b39dbc1275afbde67b43ac9664d3915a2cdbc300b06da47e9`;
- the current generated-host renderer is
  `src/Orbyss.ProgramKit.DotNet/Generation/DotNetHostSourceRenderer.cs`,
  SHA-256
  `16e45788d604a05c7df5c18aae5e9d306a979b5f1c24593d00e414f999e37c6c`;
- the still-current dispatcher contract is
  `src/Orbyss.ProgramKit.DotNet/Generation/ConsoleCommands/DotNetConsoleCommandDispatchContract.cs`,
  SHA-256
  `503647fe8533d1bdecc1cddccdbb61829a421a81ae7d0914730fbdcf84ea2799`;
- the separately approved typed Console design is
  `72bfa056c3e0f19d1765d9feae9aa5eb4ccb546a07896f2682a276294abcd4ca`;
  its neutral Open Console ownership and exact .NET binding work units are
  implemented at the source baseline.

Development Tools therefore binds the exact neutral Open Console document and
consumer package/executable bytes. It does not bind the current dispatcher or
future Spectre host internals. Every affected implementation unit has a
material-Console-drift stop condition.

Concurrent typed Console implementation work after the source baseline and the
unrelated `extensions/web-publication-static-react/` worktree were preserved
and are not treated as Development Tools design authority or validation
evidence.

## Schema and semantic validation

A temporary review-only executable used the repository's compiled ProgramKit
validators and was removed after the check.

Passed:

- `JsonSchemaWorkbenchValidator` against
  `pkid:schema:program-kit:architecture-design@2.0.0`, schema SHA-256
  `2698ce65a29cb0d5007b2ab1773d7e387385df7c8b72495804b292b6af696198`;
- `ArchitectureDesignV2Validator` over
  `ArchitectureDesignValidator` and `ArtifactDecisionValidator`;
- `JsonSchemaWorkbenchValidator` against
  `pkid:schema:program-kit:implementation-plan@3.0.0`, schema SHA-256
  `0f3b8f524b29ec7b5871ce411f06852e1b06326a5e1da616184627df0b5ea1b6`;
- `ImplementationPlanDocumentV3Validator` over
  `ImplementationPlanDocumentValidator`;
- `JsonSchemaWorkbenchValidator` against
  `pkid:schema:program-kit:static-conformance-disposition@1.0.0`, schema
  SHA-256
  `834902de4706a7c6859390bd7ee5e4fd6a3e7e455486348c02a1cb84604d15bd`.

The final focused observation was:

```text
passed schemas=3 requirements=16 workUnits=7 fixtures=32 design=sha256:918db6923687e0098d2b5c59936714c4f804235dfa18299bd6d6830535c7d5cb
```

## Determinism, trace, and integrity

Passed:

- all review JSON parses successfully;
- two consecutive plan-materializer runs are byte-identical and retain plan
  SHA-256
  `051f5ad4ce778b404707e9b9c94445c36677ffa235320c8aa3665b9445b53e56`;
- all 16 requirement IDs have exactly one stable-order trace record;
- all trace work-unit references resolve;
- seven unique work units have exact serial sequence `10` through `70` and
  each unit depends on its accepted predecessor;
- the closure unit transitively reaches every product unit;
- every plan design reference equals the exact canonical design bytes;
- architecture and plan bind the same exact disposition;
- the plan binds the exact materialized gate definition, selection lock, and
  activation evidence;
- the disposition has exactly one `reuse-existing` gate selection;
- all 32 fixture IDs are unique and partition exactly once across the five
  evidence profiles;
- the reviewer projections name the exact canonical design and plan digests;
- `git diff --check -- extensions/development-tools` passes.

## Static-conformance selection

The human-selected disposition is `reuse-existing`.

- gate:
  `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`,
  `e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1`;
- activation:
  `pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`,
  `bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b`;
- verification:
  `pkid:profile:program-kit:private-csharp-gate-exhaustive@1.0.0`,
  `80978c4209e5119c8df468f47f972ea8dc622bbeb907681e48721d5d8f12738d`;
- existing activation evidence:
  `c4b247449959317dd95eca5aab4baf61d709ff27155e84cae0a9d111f0e4b09b`.

The selection applies only to ProgramKit-owned implementation C#. It creates no
new or extended gate and never attaches the private gate to consumer-owned
source.

## Provider evidence

Official Codex, Claude Code, and MCP sources were re-read on `2026-07-28` and
recorded in `provider-contract-evidence.json`, SHA-256
`c9044e62f3079c3e87e4affc5ff2e63c170cd97bf1eb89eb105ad932c4cc9130`.

The design selects one neutral MCP `2025-11-25` stdio bridge, one exact
project-scoped Codex `.codex/config.toml` entry, and one exact project-scoped
Claude Code `.mcp.json` entry. It forbids the registration writers from
granting trust/permissions, writing global configuration, or starting a
process. Material official-contract drift is a work-unit stop.

## Rendering

Repository `program-kit render` was invoked for both canonical artifacts and
returned `PKCLI004`: the standalone Workbench renderer adapter is not
registered in the current CLI composition. This is recorded as unavailable,
not as a pass or failure of the artifacts.

The reviewer Markdown projections were therefore authored directly from the
canonical review content and mechanically checked to contain the exact
canonical identity/version/digest bindings. The JSON remains authoritative.

## Repository build and test boundary

Focused builds of `Orbyss.ProgramKit.Architecture` and
`Orbyss.ProgramKit.Planning` passed the mandatory private C# gate with zero
warnings and zero errors while the review was produced.

Full locked restore could not be rerun in this sandbox because the .NET/NuGet
SDK resolver requires the user-level NuGet configuration outside the repository.
An unsandboxed restore was not authorized because it could use unspecified
configured/authenticated feeds. This is recorded as unavailable, not failed or
passed.

A subsequent `dotnet test ProgramKit.sln --no-restore` found the existing test
assemblies but ran zero tests and returned exit `5`; without the unavailable
locked restore, that observation is not a valid suite result and is not cited
as a pass or a product failure. No result is inferred from another session's
in-progress typed Console build.

## Assumptions and deferrals

- Current official provider contracts remain stable until each provider work
  unit rechecks them.
- The human can run the exact Claude Code external acceptance kit on the other
  machine and return genuine evidence.
- Genuine Claude Code runtime acceptance and overall cross-provider closure
  remain future `PKDT-W070` outcomes.
- Corrective Reconstruction remains backlogged.
- Remote MCP, native provider bindings, plugins/skills as transport, other
  providers, publication, release, deployment, production data,
  infrastructure, secret values, operational history, and autonomous behavior
  remain deferred or excluded.

## Deliberately not performed

- No Development Tool runtime, schema, bridge, provider writer, binding,
  registration, permission, capability, or application operation was
  implemented.
- No provider project/user/global configuration was changed.
- No Codex or Claude Code cold-session acceptance was attempted under design
  authority.
- No Domain Semantic Engine or program-kit-website path was edited.
- No approval was created.
