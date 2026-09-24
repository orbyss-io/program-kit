## Governance Completion Evidence *(mandatory)*

For each vertical outcome, include the task sequence that delivers and verifies the complete path before broad horizontal expansion. Include tasks for applicable contract, architecture-boundary, integration, and acceptance evidence.

- **Roadmap transition**: move the matching entry to Active only when implementation starts; record Delivered only after its verification evidence exists.
- **Architecture evidence**: update the dependency test, contract test, or ADR evidence required by the plan.
- **Non-goal protection**: do not add tasks for unapproved technology adoption, cross-feature implementation references, or unrelated platform work.
- **Path and ownership protection**: every task path must be declared by the plan's
  `artifact-ownership.json`, recognized by an accepted profile, or paired with the plan's exact
  `STRUCTURE-DELTA: <path>`. Never ask implementation to edit `.program-kit/eng/**`; name the
  consumer-owned extension point (`Directory.Build.props/targets`, feature adapter, `vite.config`,
  or consumer deployment configuration) instead.

- **External host protection**: when `Orbyss.Foundation.Host` is selected, create only packable feature
  packages and consumer activation/release inputs. Never create a repository-owned `.Host` project
  or application `Program.cs`; include `FoundationFeatureIdentity`, `shells.json`,
  `hostsettings.json`, package-closure staging, and digest-bound external-host evidence tasks.
- **Dependency graph protection**: resolve exact npm peer, engine, and platform constraints in an
  isolated lockfile-only check before implementation; never use force/legacy peer bypasses.
- **Authorization ownership protection**: test managed endpoint permission metadata and real
  resource/state/effect rules separately; never task a consumer feature with parsing provider roles
  or canonical permission claims, and do not invent an inner service for a no-effect access probe.


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
