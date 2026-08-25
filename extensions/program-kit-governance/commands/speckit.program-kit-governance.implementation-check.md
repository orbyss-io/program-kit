---
description: Verify implementation plans obey generic programming and lifecycle guardrails.
---

## Required checks

Run `python .specify/extensions/program-kit-governance/scripts/governance_state.py validate
--require-roadmap` and read the ratified constitution and active roadmap entry before checking the
plan. A stale constitution or non-Ready/non-Active roadmap entry blocks implementation. Do not
require some other entry to remain Ready after the selected specification becomes Active.

Apply `.specify/extensions/program-kit-governance/references/programming-guardrails.md`,
`software-language.md`, `vertical-slicing.md`, `modularity-and-contracts.md`, and any detected
technology profiles.

Confirm:

- dependency direction and explicit public contracts;
- SOLID/cohesion principles without speculative abstraction;
- identity, intent, context, authorization, policy decisions, transitions, effects, admissions, and outcomes are explicit where meaningful;
- lifecycle invariants and legal transitions have tests;
- all request paths have explicit terminal outcomes; asynchronous acceptance returns an operation identity and durable ownership;
- required admission and optional observation are distinct;
- persistence, transport, framework, and orchestration details do not obscure domain intent;
- cancellation, timeouts, retries, idempotency, concurrency, errors, logging, metrics, and tracing are designed where relevant;
- tests are assigned at the cheapest reliable level and include architecture/contract checks when applicable;
- no implementation task depends on an unresolved blocking ADR;
- tasks complete thin end-to-end slices before broad horizontal expansion and name the observable outcome they enable;
- peer modules and features do not reference one another's implementations, persistence, or internal models;
- interfaces and schemas live at their owned boundaries rather than in speculative shared projects;
- inheritance or typed feature dependencies do not bypass the accepted feature-family exception policy;
- dependency injection is confined to composition and endpoints or handlers declare explicit dependencies.

Pure functions, trivial adapters, generated code, and presentation-only code may use a documented proportional exception. An exception cannot bypass security, public-contract, data-integrity, or lifecycle invariants.

Return blocking findings and the exact plan/task changes required. Do not implement code in this check.
