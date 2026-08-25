---
description: Determine whether the repository is ready to begin feature specifications.
---

## Input

`$ARGUMENTS` identifies the bootstrap scope.

## Readiness gate

Inspect the initial design, architecture baseline, decision backlog, ADRs, technology radar, tooling evaluation, quality system, and traceability model. Report `READY`, `CONDITIONALLY READY`, or `NOT READY`.

`READY` requires that implementation-blocking architecture decisions are Accepted, significant risks have owners and verification, technology statuses are honest, architecture views are internally consistent, and the first specification can be written without smuggling in an unreviewed architecture choice.

Unresolved decisions may remain only when they do not block the proposed first specification. List each remaining decision with the earliest lifecycle point at which it must be resolved.

Do not change an ADR status while evaluating readiness.

