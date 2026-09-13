## Architecture Realization *(mandatory)*

- **Roadmap entry and status transition**: [Entry ID and intended Ready -> Active transition]
- **Vertical-slice path**: [Actor/trigger -> intent -> decision -> effects -> observable outcome]
- **Module and dependency edges**: [Owned modules, contracts, and allowed dependency direction]
- **ADR and technology evidence**: [Accepted ADRs and approved technologies relied on by this plan]
- **Verification ownership**: [Who proves contracts, architecture boundaries, and user-visible behavior]
- **Artifact ownership manifest**: Maintain `artifact-ownership.json` beside this plan using the
  Program Kit schema. Declare every expected path/pattern as managed, scaffold-once, consumer-owned,
  generated, or evidence, with data classification and lifecycle. Predeclare
  `.program-kit/evidence/runtime-closure.json`, `.program-kit/evidence/host-image.json`,
  `.program-kit/evidence/after-tasks-analysis.md`, `docs/security/security-ledger.md`, the feature
  `quickstart.md`, and `tests/fixtures/program-kit/local-contract.json` when applicable.
- **Structure deltas**: A path outside the manifest or an accepted profile convention must be added
  to this plan as `STRUCTURE-DELTA: <path>` before task generation completes.

When the accepted .NET runtime is the external `Orbyss.Foundation.Host`, the plan MUST NOT introduce a
consumer `.Host` project or application `Program.cs`. It must instead name packable feature
projects and `FoundationFeatureIdentity`, `shells.json` activation, consumer `hostsettings.json`,
validated `runnable_host.py stage` package closure, and digest-bound external-host release evidence.
Its `artifact-ownership.json` MUST also contain `runtimeComposition`: accepted architecture
authority paths, every planned project's role and exact direct `ProjectReference` and
`PackageReference` sets, selected feature identities, and a binding for every provider or bridge.
Each binding names the semantic capability, its owning Core project, concrete implementation,
implementing project, registration entry point, and that project's activated feature identity.
The required `coreReferences` array is empty by default. Every direct Core-to-Core edge needs one
exact entry naming its `subdomain`, `published-language`, or `shared-kernel` relationship, an
Accepted decision included among the authorities, and owned architecture-test evidence.
Do not create `.Feature`, generic `Domain`, `Contracts`, `Application`, or `Infrastructure` layer
projects. Never make an endpoint implementation reference a persistence provider to manufacture a
composition path; the external host activates both implementations through `shells.json`.
Exact npm dependencies require a repository-contained candidate package manifest and current
`.program-kit/evidence/npm-graph.json` from the strict isolated lockfile-only resolver before the
plan is implementation-ready.

For authenticated .NET endpoints, keep provider mapping in deployment, canonical permission
normalization/policy evaluation in the selected Program Kit authentication feature, and only genuine
resource/state/effect authorization in consumer code. A bodyless/no-effect probe uses managed
`permission:<identity>` endpoint metadata and must not introduce a second permission service/parser.

If the plan identifies a new architecture decision, contract ownership conflict, or technology choice, stop and create the required design task and ADR rather than treating it as implementation detail.


## Applicable knowledge and proof

Read the generated `phase-context.md` before authoring this artifact. Follow the installed
`program-kit-governance/references/phase-evidence.md` contract for `obligation-design.json`,
`semantic-contract.json`, `verification-plan.json` and `obligation-review.json` in this feature.
Where capabilities are selected, also create `capability-adoption.json`. Name actual test cases
for every applicable requirement and task their implementation; future test paths are valid at
planning, but only executed, current results satisfy delivery. Review Core/Abstractions ownership,
policy purity, legal transitions, required acknowledgement, extension resolution and public API
compatibility in proportion to this slice. Explicitly explain nonapplicability for simple cases.
Keep all declared design references and test/build inputs in the verification scope; use
`inputPaths` for consumer adapters or dependencies outside owned project directories.

At completion, run the declared suites through `phase_obligations.py verify`, perform the
current delivery review, and pass `lifecycle_state.py verify-delivery` before marking the
roadmap entry Delivered. A green repository aggregate alone does not satisfy this contract.

For applicable .NET boundaries, write `architecture-proof.json` alongside the ownership manifest.
Bind named graph checks, actual shell registration/resolution tests and extension compatibility
checks for every capability binding; include executable coverage for accepted Core-reference
exceptions. Follow the installed phase-evidence contract. Empty bindings are valid for a simple
feature with no extension point; do not manufacture abstractions merely to fill the artifact.
