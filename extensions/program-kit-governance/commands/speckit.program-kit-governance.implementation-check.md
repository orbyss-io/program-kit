---
description: Verify implementation plans obey generic programming and lifecycle guardrails.
---

## Required checks

Apply `.specify/extensions/program-kit-governance/references/programming-guardrails.md`, `software-language.md`, and any detected technology profiles.

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
- no implementation task depends on an unresolved blocking ADR.

Pure functions, trivial adapters, generated code, and presentation-only code may use a documented proportional exception. An exception cannot bypass security, public-contract, data-integrity, or lifecycle invariants.

Return blocking findings and the exact plan/task changes required. Do not implement code in this check.
