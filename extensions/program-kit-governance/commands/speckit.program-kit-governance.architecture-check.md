---
description: Validate Spec Kit artifacts and implementation against accepted architecture.
scripts:
  py: scripts/governance_state.py validate --require-roadmap
---

## Scope discovery

Always validate the ratified constitution and roadmap:

```text
{SCRIPT}
```

This prerequisite check runs before `speckit.specify` as well as after later lifecycle steps. It
blocks every lifecycle step when the constitution is not ratified and hash-current. When invoked by
`before_specify`, add `--require-ready`; specification creation is blocked when no roadmap entry is
Ready. Before specification creation, return the prerequisite result without requiring a current
specification. Later checks accept the selected entry after its honest transition to Active and do
not require an unrelated entry to remain Ready.

For later lifecycle checks, locate the current specification, plan, tasks, or implementation from
the active Spec Kit context. Read the constitution, approved bootstrap decision register and
approval evidence, specification roadmap, architecture baseline, decision backlog, technology
radar, traceability model, and all relevant ADRs. If required artifacts are missing, fail with an
actionable bootstrap instruction.

For `after_specify`, use `scripts/lifecycle_state.py begin clarify` before clarification. If
`speckit.clarify` asks questions, leave that operation active while paused and resume it explicitly;
only complete with `questions-answered` after answers update the spec. If it asks nothing, complete
with `no-questions` and continue automatically. Do not re-enter an active operation.

For `after_tasks`, save the complete `speckit.analyze` result at
`.program-kit/evidence/after-tasks-analysis.md`, run `scripts/lifecycle_state.py begin analyze`, and
complete analysis against that report. HIGH or CRITICAL findings block readiness. Then run
`scripts/artifact_ownership.py` against the feature's manifest, plan, and tasks; unknown paths,
managed-path edits, or ownership drift are errors.

## Checks

- No statement conflicts with an Accepted ADR or architecture invariant.
- No statement conflicts with the ratified constitution, and no lower artifact weakens its governance.
- The work corresponds to a Ready or Active specification-roadmap entry with matching outcome, scope, ownership, contracts, lifecycle, data, quality, and dependency claims.
- Explicit intake choices, Program Kit defaults, safe derived defaults, and reviewed overrides match
  the approved bootstrap decision register and Accepted bootstrap-baseline decision.
- No Proposed technology outside that reviewed baseline is treated as accepted.
- New material choices have a Proposed ADR and are not implemented before approval.
- Domain ownership and dependency direction remain valid.
- Public APIs, events, schemas, persistence contracts, and security boundaries have compatibility and migration treatment.
- Lifecycle states, transitions, policies, terminal outcomes, admissions, retries, idempotency, and failure ownership are explicit where relevant.
- Architecture and traceability artifacts were updated when a decision changed.
- Specifications, plans, and tasks are organized around complete vertical outcomes rather than technical-layer phases.
- Every slice identifies its owner, intent, contracts, policies, effects, material failures, operational concerns, and verification in proportion to risk.
- Module and feature references match the accepted dependency graph; peer implementations and stores are not accessed directly.
- Shared abstractions, kernels, runtime feature dependencies, and feature-family extension or inheritance edges have explicit ownership and any required Accepted ADR and allowlist.
- Public endpoint, event, configuration, and schema types are distinct from domain entities and have compatibility evidence.
- Authenticated browser boundaries inherit `program-kit-web-threat-model-v1` and
  `program-kit-web-security-evidence-v1`; overrides identify the affected `WEB-Cxx`, `WEB-Dxx`, or
  residual-risk control, an owner, review condition, and executable evidence.
- A roadmap entry is not Ready when a required ADR is unresolved, and a design task is not presented as a feature specification or application implementation task.
- Managed `eng/program-kit/**` files are never implementation targets. OpenAPI, feature metadata,
  SPA serving security, toolchain, and persistence are configured only from their documented
  consumer-owned MSBuild, Vite, feature-adapter, or deployment extension points.

Return a structured report of errors, warnings, new decisions, and required artifact updates. Errors block the lifecycle step. Never silently edit an Accepted ADR to make a conflict disappear.
