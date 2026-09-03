---
description: Verify implementation plans obey generic programming and lifecycle guardrails.
scripts:
  py: scripts/governance_state.py validate --require-roadmap
---

## Required checks

Run `{SCRIPT}` and read the ratified constitution and active roadmap entry before checking the
plan. A stale constitution or non-Ready/non-Active roadmap entry blocks implementation. Do not
require some other entry to remain Ready after the selected specification becomes Active.

Run `scripts/lifecycle_state.py verify-before-implement` for the active feature. It must prove that
the canonical after_tasks analysis report is unchanged, contains no HIGH/CRITICAL readiness block,
and was computed from the current byte hashes of `spec.md`, `plan.md`, and `tasks.md`. Missing,
interrupted, or stale evidence blocks implementation.

Apply `.specify/extensions/program-kit-governance/references/programming-guardrails.md`,
`software-language.md`, `vertical-slicing.md`, `modularity-and-contracts.md`, and any detected
technology profiles from their installed technology extensions.

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
- a selected external `ProgramKit.Host` profile has no repository-owned `.Host` project or
  application `Program.cs`; feature identity metadata, `shells.json`, `hostsettings.json`, package
  closure staging, and digest-bound external-host evidence are planned instead;
- exact npm graphs have successful peer/engine/platform resolution evidence without `--force` or
  `--legacy-peer-deps`;
- externally consumed .NET-to-TypeScript OpenAPI work registers a producer contract before
  implementation: the managed exporter composes the validated staged feature closure without
  listening or running shell initializers, then normalization/compatibility, an isolated generator
  lockfile, and the application TypeScript compile run in that order;
- authenticated web tasks consume the selected secure web profile rather than inventing schemes,
  claims mapping, session/refresh/logout behavior, runtime keys, CORS/CSP, denial bodies, or identity
  test fixtures inside a feature slice;
- role-protected endpoints have provider-backed contract evidence for anonymous `401`, wrong-role
  `403`, and authorized success, plus the profile's mandatory Playwright journey.
- security-sensitive web work traces its affected `WEB-C01` through `WEB-C13` controls and does not
  exceed the claims of `program-kit-web-threat-model-v1` or
  `program-kit-web-security-evidence-v1`;
- configurable security-default changes cite the matching `WEB-Dxx` rationale, Accepted risk owner,
  review condition, and negative regression evidence;

Pure functions, trivial adapters, generated code, and presentation-only code may use a documented proportional exception. An exception cannot bypass security, public-contract, data-integrity, or lifecycle invariants.

Return blocking findings and the exact plan/task changes required. Do not implement code in this check.
