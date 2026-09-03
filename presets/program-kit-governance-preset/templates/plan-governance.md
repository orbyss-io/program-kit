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

When the accepted .NET runtime is the external `ProgramKit.Host`, the plan MUST NOT introduce a
consumer `.Host` project or application `Program.cs`. It must instead name packable feature
projects and `ProgramKitFeatureIdentity`, `shells.json` activation, consumer `hostsettings.json`,
validated `runnable_host.py stage` package closure, and digest-bound external-host release evidence.
Exact npm dependencies require a repository-contained candidate package manifest and current
`.program-kit/evidence/npm-graph.json` from the strict isolated lockfile-only resolver before the
plan is implementation-ready.

If the plan identifies a new architecture decision, contract ownership conflict, or technology choice, stop and create the required design task and ADR rather than treating it as implementation detail.
