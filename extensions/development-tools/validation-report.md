# Development Tools review validation

Status: passed for the candidate design review set. Implementation and runtime
acceptance were not performed.

## Source basis

- Program Kit committed source basis:
  `f555745e77ebce234f7e54665869a32cc555ba45`.
- The completed Program Kit health-patching commits were inspected as current
  source truth and were not edited or widened.
- The current mainline manifest-digest hardening changes build-gate evidence,
  not the Development Tools product contract.
- The later completed alpha-3 package-only consumer proof and feed handoff are
  preserved as existing delivery/cold-session foundations for dogfood; the
  merged-branch cleanup policy changes repository workflow only.

## Repository-backed schema validation

The repository's own `program-kit artifacts inspect` operation validated:

- `architecture-design.json` against
  `pkid:schema:program-kit:architecture-design@0.1.0-alpha.2`,
  schema digest
  `e94b5e1dab8292066669ccee5069f27a6e220962906051931fc1f1607fe2dbf7`;
- `implementation-plan.json` against
  `pkid:schema:program-kit:implementation-plan@0.1.0-alpha.3`,
  schema digest
  `774c6b945ac2b63c2e4beca0afab9c282669274f0c7d4eb4b9e936ba38460c7c`;
- `static-conformance-disposition.json` against
  `pkid:schema:program-kit:static-conformance-disposition@0.1.0-alpha.1`,
  schema digest
  `9de8f2dfcc52bb629ef802db26bd67ffc38687d73d08084292127f6eeda29811`.

All three returned `Valid: yes`. The Program Kit CLI and its current dependency
graph compiled successfully as part of the first inspection. Locked restore
succeeded after using the user's readable NuGet configuration.

## Structural and semantic review validation

`validate-review-set.ps1` checks:

- JSON parsing for every review JSON artifact;
- exact intent, convergence, static-basis, human-decision, disposition,
  gate-definition, activation-matrix, verification-profile, closure-evidence,
  architecture, plan, and selection-lock digest bindings;
- the exact `reuse-existing` disposition and current Program Kit-only gate
  scope;
- unique, preceding work-unit dependencies and complete requirement trace;
- no unresolved architecture or plan decision;
- an adjacent human-readable implementation-plan projection that is explicitly
  non-authoritative and binds the exact current canonical plan digest;
- exactly 42 unique acceptance fixtures, each assigned to one evidence profile;
- `awaiting-human-approval`, `not-started`, and no inferred approval record;
- exact review-manifest file digests; and
- two consecutive byte-identical materializations of both
  `implementation-plan.json` and `implementation-plan.md`.

The final validator run passed.

## Design-capability maintenance verification

The repository-owned `design-software` capability now requires every canonical
implementation plan to have an adjacent digest-bound, explicitly
non-authoritative human-readable projection. Its stable capability identity and
provider triggers are unchanged.

- The canonical capability definition, canonical index, generated catalog, and
  exact capability-bundle manifest were refreshed.
- The alpha version-intent inventory and reusable-gate compatibility evidence
  were rebound to the current manifest bytes.
- A fresh content-only
  `Orbyss.ProgramKit.CapabilityBundle.0.1.0-alpha.3.nupkg` built with zero
  warnings/errors and passed `program-kit capabilities verify-bundle`.
- Focused `CapabilityDeliveryConformanceTests` passed 10/10.
- Focused `CapabilityCatalogRendererTests` and
  `CapabilityBundleVerifierTests` passed 11/11.
- No capability was initialized or activated in the authoring workspace.

## Current static-conformance binding

- Gate definition:
  `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`,
  digest
  `e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1`.
- Activation matrix:
  `pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`,
  current `Directory.Build.targets` digest
  `9603f5e67d256b381df4e69dce99fd9aafeaded20c947cfe699adb9dec7ecd8b`.
- Exhaustive verification profile digest:
  `80978c4209e5119c8df468f47f972ea8dc622bbeb907681e48721d5d8f12738d`.
- Reusable-gate closure-evidence digest:
  `7f4a6fbe84c42fc983880abb5e9c18b31eae6cbc6588171a76490f558c7d140b`.

The historical Development Tools lock used an older activation-matrix and
closure-evidence digest. The candidate review set rebinds the same existing gate
identity to current committed bytes; it does not create, extend, or activate a
new gate.

## Provider-contract freshness

Official current documentation was rechecked on 2026-07-30:

- MCP 2026-07-28 modern `server/discover`, tools, schemas, metadata, and
  transports;
- MCP 2025-11-25 legacy initialize, tools, and transports;
- current Codex project MCP configuration, project trust, and skill
  explicit/implicit activation;
- current Claude Code project MCP, skills, tool search, settings, permissions,
  and cloned-repository approval boundaries.

The design therefore keeps MCP as executable transport, uses provider-native
skill/capability selection, supports the modern and legacy MCP eras without a
startup protocol flag, and preserves provider-owned trust and permissions.

## Deliberately not validated under design authority

- No prospective runtime, CLI, schema, package, MCP, provider adapter,
  application outcome capability, workspace catalog, lock, or lifecycle
  behavior was implemented. The existing `design-software` procedure and inert
  bundle metadata were documentation-only maintenance explicitly requested by
  the human.
- The prospective 42-fixture implementation acceptance matrix was not executed.
- No Codex or Claude Code project configuration, trust, permission, tool
  registration, or capability initialization was mutated.
- No genuine provider cold-session acceptance was run.
- No package was published, promoted, released, or deployed.
- No external or sibling repository was inspected or changed.

Those checks belong to the dependency-ordered implementation work units after a
separate exact human approval of the canonical design and plan digests.
