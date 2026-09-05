---
description: Verify implementation plans obey generic programming and lifecycle guardrails.
scripts:
  py: scripts/governance_state.py validate --require-roadmap
---

## Required checks

Run `{SCRIPT}` and read the ratified constitution and active roadmap entry before checking the
plan. A stale constitution or non-Ready/non-Active roadmap entry blocks implementation. Do not
require some other entry to remain Ready after the selected specification becomes Active.

Run `scripts/implementation_preflight.py --repository <repository> --feature-dir <feature-dir>` for
the active feature. This mandatory deterministic preflight runs both lifecycle verification and the
complete artifact-ownership validator, including registered OpenAPI producer pins. It must prove that
the canonical after_tasks analysis report is unchanged, contains no HIGH/CRITICAL readiness block,
and was computed from the current hashes of `spec.md`, `plan.md`, and a canonical `tasks.md`. Checkbox
state is implementation progress and is excluded from the task design hash; task IDs, descriptions,
order, paths, and all other content remain hash-protected. Missing, interrupted, stale, or producer-pin-
incoherent evidence blocks implementation. Do not substitute lifecycle verification alone for this
preflight.

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
- Core/helper/implementation/provider/bridge/composition edges match the accepted graph; endpoints
  and peer implementations do not reference providers or internal models;
- semantic capability interfaces and schemas live at their owned boundaries rather than in
  speculative shared projects; generic repositories/stores/units of work and automatic
  one-interface-per-method decomposition are rejected;
- provider-specific persistence types remain private, and cross-context mappings use published
  business-semantic boundary models rather than persistence records or internal aggregates;
- inheritance or typed feature dependencies do not bypass the accepted feature-family exception policy;
- dependency injection is confined to composition and endpoints or handlers declare explicit dependencies.
- for external-host .NET work, every selected provider or bridge owns an explicitly accepted and
  `shells.json`-activated capability implementation; the exact direct `ProjectReference` and
  `PackageReference` sets in `artifact-ownership.json.runtimeComposition` match each existing
  project before source work continues. Treat unused declared references as real edges rather than
  relying only on compiled CLR type-dependency tests;
- activatable project names describe the domain/provider/protocol/bridge/composition capability and
  never contain `.Feature` or generic horizontal layer markers;
- direct Core-to-Core dependencies cite the Accepted Context Map/ADR and are used only for stable
  published language, cohesive subdomains, or a deliberately jointly owned semantic kernel; each
  exact edge appears in `runtimeComposition.coreReferences` with owned architecture-test evidence;
- domain-event handlers are awaited and independent; required results/order use a semantic
  capability or orchestrator. Reliable post-commit/background/cross-process event requirements are
  blocked on the tracked Integration Events/outbox design;
- a selected external `ProgramKit.Host` profile has no repository-owned `.Host` project or
  application `Program.cs`; feature identity metadata, `shells.json`, `hostsettings.json`, package
  closure staging, and digest-bound external-host evidence are planned instead;
- exact npm graphs have successful peer/engine/platform resolution evidence without `--force` or
  `--legacy-peer-deps`;
- externally consumed .NET-to-TypeScript OpenAPI work registers a producer contract before
  implementation: the managed exporter composes the validated staged feature closure without
  listening or running shell initializers, then normalization/compatibility, an isolated generator
  lockfile, and the application TypeScript compile run in that order;
- authenticated web tasks consume the selected Program Kit host web profile rather than inventing schemes,
  claims mapping, session/refresh/logout behavior, runtime keys, CORS/CSP, denial bodies, or identity
  test fixtures inside a feature slice. Each `.Api` project puts stable application
  permission/policy metadata on the endpoints it owns;
- permission-protected endpoints have provider-backed contract evidence for anonymous `401`,
  missing-permission `403`, and authorized success, including negative provider-role/scope mapping
  cases and the profile's mandatory Playwright journey.
- security-sensitive web work traces its affected `WEB-C01` through `WEB-C13` controls and does not
  exceed the claims of `program-kit-web-threat-model-v1` or
  `program-kit-web-security-evidence-v1`;
- project verification IDs do not redefine canonical `WEB-Cxx` meanings and preserve the managed
  registry's profile applicability;
- configurable security-default changes cite the matching `WEB-Dxx` rationale, Accepted risk owner,
  review condition, and negative regression evidence;

Pure functions, trivial adapters, generated code, and presentation-only code may use a documented proportional exception. An exception cannot bypass security, public-contract, data-integrity, or lifecycle invariants.

Return blocking findings and the exact plan/task changes required. Do not implement code in this check.
