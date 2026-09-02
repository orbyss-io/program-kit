## Governance Completion Evidence *(mandatory)*

For each vertical outcome, include the task sequence that delivers and verifies the complete path before broad horizontal expansion. Include tasks for applicable contract, architecture-boundary, integration, and acceptance evidence.

- **Roadmap transition**: move the matching entry to Active only when implementation starts; record Delivered only after its verification evidence exists.
- **Architecture evidence**: update the dependency test, contract test, or ADR evidence required by the plan.
- **Non-goal protection**: do not add tasks for unapproved technology adoption, cross-feature implementation references, or unrelated platform work.
- **Path and ownership protection**: every task path must be declared by the plan's
  `artifact-ownership.json`, recognized by an accepted profile, or paired with the plan's exact
  `STRUCTURE-DELTA: <path>`. Never ask implementation to edit `eng/program-kit/**`; name the
  consumer-owned extension point (`Directory.Build.props/targets`, feature adapter, `vite.config`,
  or consumer deployment configuration) instead.
