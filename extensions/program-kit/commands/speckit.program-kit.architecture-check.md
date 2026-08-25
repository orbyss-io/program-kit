---
description: Validate Spec Kit artifacts and implementation against accepted architecture.
---

## Scope discovery

Locate the current specification, plan, tasks, or implementation from the active Spec Kit context. Read the architecture baseline, decision backlog, technology radar, traceability model, and all relevant ADRs. If required architecture artifacts are missing, fail with an actionable bootstrap instruction.

## Checks

- No statement conflicts with an Accepted ADR or architecture invariant.
- No Proposed technology is treated as accepted.
- New material choices have a Proposed ADR and are not implemented before approval.
- Domain ownership and dependency direction remain valid.
- Public APIs, events, schemas, persistence contracts, and security boundaries have compatibility and migration treatment.
- Lifecycle states, transitions, policies, terminal outcomes, admissions, retries, idempotency, and failure ownership are explicit where relevant.
- Architecture and traceability artifacts were updated when a decision changed.

Return a structured report of errors, warnings, new decisions, and required artifact updates. Errors block the lifecycle step. Never silently edit an Accepted ADR to make a conflict disappear.

