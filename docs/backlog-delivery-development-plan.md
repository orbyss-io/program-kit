# Program Kit team delivery: development plan

Date: 2026-09-12. Status: Phase 0 complete; Phase 1 interview is next. The [Phase 0 evidence](delivery/phase-0-evidence.md) records the contract and provider capability proof. Consumer delivery integrations and later-phase acceptance are not yet implemented.

The supporting [template research](backlog-delivery-template-research.md) contains the source evidence, field mappings, four work-item templates, and a worked requirement. Product choices below were accepted during the interview. Technical mechanisms remain subject to the explicit verification gates in this plan.

## How we will work

Use one integration branch, `codex/backlog-delivery`, for every phase. Do not create per-phase subbranches or SpecKit specifications for this development effort. References elsewhere in this plan to consumer specifications describe the product's integration with onboarded repositories, not a requirement to use SpecKit to develop Program Kit itself.

Before starting each phase, conduct a grilling interview with the user about the phase's unresolved technical decisions. Investigate repository and provider facts first; present recommendations and tradeoffs; record the agreed decisions and exit criteria here or in linked phase notes. Obtain shared understanding before implementation of that phase. Phase 0 addresses common contracts and cross-cutting uncertainties; later phases resolve their own remaining decisions immediately before work begins.

Implement and validate each agreed phase on this same branch. When a phase is complete, commit its changes and push `codex/backlog-delivery` to origin, then review its outcome with the user before the next phase's interview. The user explicitly authorized publishing this branch and committing/pushing each completed phase; do not ask again for those routine actions. Keep commits focused and reviewable. Merge the integration branch into main only after the combined result passes the agreed validation and review. Branch pushes are not approval to merge to main, create release tags, or publish packages.

The initial worktree is `artifacts/worktrees/backlog-delivery`, created from the available `origin/main` at `514a9c6`. The main checkout contains unrelated ongoing work, which is deliberately outside this branch. Recheck integration points against this branch and any subsequently incorporated main changes during each phase; some research observations described newer uncommitted governance work in the original checkout.

## Intended result

A business owner defines an epic directly in the platform or through a Program Kit session. Program Kit refines it into features, requirements, and useful tasks tied to the accepted architecture. Team members can identify and claim ready work, work in parallel where contracts permit, and demonstrate delivery through linked evidence. Changes made by humans are reconciled explicitly before affected implementation continues under an invalid plan.

The initial capability is complete only when this journey works with both Azure DevOps and GitHub, including mixed repository hosting and externally owned dependencies. Azure DevOps is the first pilot.

## Accepted product contract

| Concern | Decision |
|---|---|
| Module boundary | Optional delivery module, disabled by default. Enabled mode selects one authoritative backlog provider per delivery space. No standalone local team-backlog backend in v1. |
| Core planning | Local architecture, roadmap, specifications, plans, tasks, and technical evidence remain core capabilities. Disabling delivery does not disable governance. |
| Hierarchy | Epic → Feature → Requirement → optional Tasks. Requirements normally describe small observable vertical outcomes. Tasks exist when they provide a useful contribution, assignment, investigation, or handoff. |
| Azure default | Agile process, mapping canonical Requirement to native User Story. |
| GitHub default | Organization issue types and native hierarchy/dependency relationships, with a designated delivery Project and explicit field authority. Capability discovery determines supported field mappings. |
| Epic intake | Title, problem/outcome, and attributable business owner suffice for initial capture. Guided refinement supplies decision-relevant detail. Both platform forms and Program Kit-led epic creation use the same contract. |
| Authority | Platform owns business intent, acceptance requirements, priority, ownership, dependencies, milestones, and delivery state. Git owns technical specifications, architecture, implementation plans, code, tests, and versioned configuration. |
| Ownership | Business, technical, and acceptance responsibilities are explicit. One human can hold all three. Agent session identity is recorded separately from accountable human ownership. |
| Allocation | Support assigned work and developer self-selection; self-selection is the small-team default. Refresh readiness and ownership before a claim; never silently take assigned work. |
| Planning | Continuous prioritization and explicit milestones; iterations and estimates are optional. Estimates include assumptions and never silently become commitments. |
| Changes | One coherent proposal per planning/revision session, then apply its approved changes without per-item approval. Mechanical synchronization follows configured rules. Business and architecture decisions remain attributable human decisions. |
| Dependencies | Model what activity/transition is blocked and what evidence satisfies it. Contracts and independent tests enable parallel work. Separate integration tasks represent real coordination obligations. |
| Code overlap | Versioned planned/observed change footprints identify paths, contracts, and resources; tags/labels expose concise categories. Broad overlap is advisory; confirmed incompatibility requires scoped coordination. Refresh on material scope or source changes. |
| Completion | Distinguish implementation completion, verified delivery, and business acceptance. Closed children do not prove an epic's business outcome. |
| Synchronization | Session/checkpoint-driven. Recheck at session start, claim, before implementation, between substantial phases, before PR/equivalent publication, and before delivery completion. Continuous monitoring is deferred. |
| Outages | Cloud authority persists. Permit visibly stale local analysis, proposals, and bounded continuation of claimed work. Defer new shared claims, commitments, and governed completion until reconciliation. |
| Activation | Same workflow during bootstrap and later enablement; no repeat onboarding. Review configuration and initial backlog proposal. Preserve identity/provenance of existing roadmap entries. |
| Profiles | Shared consumer-controlled Git profile at an explicit revision, plus repository/team bindings. Single-repository consumers can colocate both. Upgrades are explicit and compatibility-checked. |
| Disconnection | Deliberate handoff preserving history, active-work accounting, and unresolved governance obligations. No silent change of authority or deletion of cloud records. |

Repository hosting and delivery authority are independent. A delivery space can own work for GitHub and Azure-hosted repositories. An external upstream issue is a reference to someone else's work; an internal dependency item records the receiving team's need, owner, and acceptance evidence. Do not implement full bidirectional issue mirroring as the default.

## Proposed implementation structure

Use a separately activated delivery extension, with conversational commands/skills guiding deterministic operations. Names and package layout will follow existing repository conventions during implementation. Provider writes, identity resolution, validation, and recovery must not depend on an agent repeatedly improvising API calls.

The common contract should cover:

- Delivery-space identity, selected provider, shared profile revision, participating repository bindings, roles, field mappings, and capabilities.
- Stable logical work identity plus provider IDs/locators, hierarchy, scope, acceptance IDs, assignments, dependencies, and milestones.
- Observed provider state, accepted business/design basis, readiness verdict, and evidence provenance. These are distinct records rather than overloaded status values.
- Change proposals, revision-specific decisions, resumable operations, conflict results, and execution claims.
- Change footprints with repository/base/plan identity, planned versus observed write scope, affected contracts/resources, assessment basis/freshness, and mapped display categories. Distinguish missing information, possible overlap, and confirmed incompatibility.
- Versioned adapters for capability discovery, reads, history/delta observation, proposals, writes, claims, relationship maintenance, and evidence lookup.

The shared profile defines semantics and mappings. Repository bindings select a compatible revision and identify repository/team/artifact locations. Authentication references use supported credential facilities; credentials do not belong in shared profile content or generated evidence.

Prefer provider-owned durable coordination records and existing evidence artifacts where they meet the contract. Local caches may accelerate reads and retain drafts, but cannot arbitrate cross-machine claims. Do not assume that a new hosted service is necessary or that native provider operations supply every needed guarantee. Choose the storage/coordination mechanism after the phase-0 proof.

A generated execution brief gives the working session the accepted business revision, current spec/plan/ADR references, scope, target repository/base, acceptance IDs, dependency conditions, shared-contract constraints, validation instructions, and expected evidence. Keep technical plans authoritative in Git rather than copying them into every platform item.

## Development sequence and exit criteria

### Phase 0 — Contracts and provider capability proof

The [Phase 0 decision record](backlog-delivery-phase-0-decisions.md) contains accepted technical choices. The [completed capability proof](delivery/phase-0-evidence.md) records schema examples, source-hashed live probes, deterministic fixtures, provider differences and limitations.

Write the common schema and adapter conformance contract, then test the difficult provider behaviors in explicitly selected disposable platform scopes. Define profile versioning and authority per field before implementing synchronization.

Investigate both providers here, even though the Azure journey is implemented first:

- Conditional updates and conflicting claims, including races with direct human edits.
- Durable operation identity, duplicate prevention, partial write recovery, and verification after uncertain responses.
- Changes to descriptions, comments, fields and relationships; deletion, access loss, missing history, pagination, and rate-limit handling.
- Actual process/field capabilities, cloud/server edition differences, supported credentials, and isolation of test configuration.
- Durable reconciliation/claim storage and profile compatibility detection across machines.
- Representative footprint cases: same-category independent work, overlapping writes, incompatible cross-repository contracts, generated-artifact sources, incomplete/stale scope, and actual scope expansion.

**Exit:** recorded capability matrix; chosen storage and adapter transports; precise supported guarantees; schema examples; deterministic conflict/recovery fixtures. A read-then-write check or machine-local lock is not accepted as cross-machine claim exclusion. Unsupported atomicity must lead to a demonstrated serialization mechanism or an explicit blocked operation, never an invented guarantee.

Cloud-hosted defaults are the initial proof target; do not advertise on-premises or enterprise-customized compatibility until tested. Any resulting product-scope change returns to review.

### Phase 1 — Optional module, profiles, and work-item contract

Add the typed activation setting, shared profile/repository binding, capability validation, role mapping, templates, and common required-at-intake versus required-at-readiness rules. Add the same semantic validator to platform-form input and agent-created items.

Implement the core authority seam: disabled repositories retain existing local behavior; enabled repositories use provider-backed delivery state and explicit local projections while preserving existing technical checks. Do not redefine current governance readiness merely to match a board column.

**Exit:** disabled-mode regression checks pass; incompatible configuration is diagnosed; clean default mappings validate; draft epics are accepted with minimal input; insufficiently refined requirements cannot be declared implementation-ready. Installation adds no unsolicited platform writes.

### Phase 2 — Azure activation and epic-to-requirement journey

Implement the common activation operation for bootstrap and later use. Discover the selected project/process, produce a reviewable setup/backlog proposal, and apply it after the appropriate decision. Preserve existing local roadmap identity and provenance when establishing work-item records.

Provide guided epic creation/refinement and generation of Feature → User Story → optional Task records using the accepted templates, native fields, and relationships. Link approved technical artifacts. Capture milestone ownership, conditions, and target dates without inventing commitments.

**Exit:** an empty Azure test scope supports both human-created and Program Kit-created epics through a reviewed, traceable requirement backlog. Repeated activation/refinement does not duplicate items or overwrite unrelated work. Bootstrap and later activation produce compatible bindings.

### Phase 3 — Reconciliation and governed revision

Compare the last observation, current platform state, accepted business/design basis, and repository evidence. Preserve human text/comments and existing item identity. Classify cosmetic changes, feedback, business changes, technical conflicts, missing information, and external dependency changes.

Material changes invalidate affected readiness and produce the necessary intake/refinement, planning, or architecture revision proposal. Do not reinterpret a platform edit as an accepted ADR. Record approvals against the revised inputs, then update work items and technical artifacts through their respective authorities. Preserve superseded decisions/work instead of routinely deleting history.

Implement resumable application, conflict detection, visible stale/unknown states, and the accepted outage/disconnect rules. A new observation after proposal preparation must invalidate or rebase any conflicting proposed write.

**Exit:** human edits made during planning survive; changed architecture assumptions block only impacted work; retries and interrupted applications preserve identity and history; inaccessible or incompletely observed dependencies never appear satisfied by default. No stale approval is applied to a materially changed proposal.

### Phase 4 — Azure parallel delivery and evidence

Implement ready-work recommendations, ownership/claim operations, execution records, checkpoint refresh, dependency evaluation, and evidence-backed progression. Compare planned and observed change footprints, map concise area/contract/coordination tags or labels, and include declared shared-contract/resource conflicts and team eligibility when explaining parallel work. Keep broad overlaps advisory and scope confirmed conflict gates to the activity that actually needs coordination; do not serialize whole modules merely because their labels match.

Use native predecessor/successor links between properly bounded activities. Add readable satisfaction conditions and evidence where native relations are insufficient. An external dependency records the internal receiving obligation; an upstream issue closing alone does not clear it.

Implement deterministic delivery checks for existing consumer validation paths, with explicit activation guidance for relevant CI gates. Reuse the consumer's quality system and propose missing integration checks; do not turn this into general-purpose pipeline provisioning or release orchestration.

**Exit:** two repositories can contribute to one milestone with parallel eligible work, enforced claims, explicit integration obligations, and artifact-bound evidence. Manual status changes and merge/close automations cannot bypass technical or acceptance gates. New baselines invalidate affected evidence without erasing historical results.

### Phase 5 — GitHub adapter and equivalent outcomes

Implement GitHub activation, types/hierarchy, authoritative Project/issue field mappings, dependencies, reconciliation, claims, and evidence operations against the common conformance contract. Handle the distinction between issue identity, Project-item identity, issue state, Project status, and close reason.

Choose supported fields through capability discovery. Keep a documented mapping fallback for unavailable optional capabilities; do not require every provider to look identical or silently weaken a mandatory behavior.

**Exit:** the same business journey and failure cases pass with GitHub as backlog authority. Mixed hosting and external dependencies work without requiring writes to the upstream repository. Concurrent coordination meets the phase-0 guarantee. Both adapters are required before the initial capability is declared complete.

### Phase 6 — Consumer acceptance, packaging, and documentation

Package the extension, profile schema/defaults, command guidance, deterministic validators, adapter requirements, and activation/upgrade/disconnect instructions. Confirm later activation works in an already onboarded consumer. Test explicit profile upgrades and incompatible bindings without silently changing active-work rules.

Run the acceptance scenarios below and retain evidence identifying profile, adapter, source, configuration, and tested artifact revisions. Publication is a separate user decision governed by the repository's release policy.

**Exit:** reviewer-readable evidence demonstrates the outcomes; disabled consumers retain their established workflow; both connected profiles are usable; documentation accurately distinguishes supported behavior, degraded operation, and unverified editions.

## Acceptance scenarios

| Scenario | Required result |
|---|---|
| Default disabled | Existing architecture/specification/development flow works without provider credentials or delivery calls. Mandatory governance remains active. |
| Two epic entry paths | Platform entry and guided Program Kit creation produce semantically equivalent records; unknown business details remain explicit until refinement. |
| Existing consumer activation | Preview and apply initial mapping without duplicate records, lost provenance, or rerunning bootstrap. |
| Parallel work | An accepted contract permits eligible provider/consumer implementation and test preparation concurrently; actual integration obligations remain visible. |
| Competing claims | Two independent sessions attempt the same work. At most one obtains the execution entitlement; the other receives a clear conflict. Human reassignment is detected and reconciled. |
| Changed business scope | An epic edit invalidating an accepted plan is detected at the next required checkpoint; impacted work requires explicit revision. Unrelated work remains eligible where justified. |
| Comments and manual tasks | Human feedback is retained and classified; completing a human task is reflected without treating unsupported technical evidence as passed. |
| Shared-contract conflict | Otherwise ready items touching a declared shared contract/resource require coordination instead of receiving an unconditional parallel recommendation. |
| External upstream work | Observe upstream issue/PR/release information without assuming control; require the receiving team's artifact/compatibility evidence. |
| Partial writes and retries | Interrupt a multi-item operation and retry it from another session; preserve identity, human edits, progress, and audit history. |
| Stale or missing evidence | Old tests, unavailable artifacts, mismatched contract versions, or missing provider access cannot establish current delivery. |
| Outage and reconnection | No fallback authority or new shared claims during outage; reconcile before governed completion and resolve intervening edits. |
| Milestone acceptance | Child completion updates progress but does not automatically establish the business outcome or move commitments. |
| Profile upgrade/disconnect | Review the impact, retain history, account for active claims/obligations, and prevent accidental governance bypass. |
| Provider parity | Exercise the full applicable matrix for Azure and GitHub; preserve outcome guarantees despite different native representations. |

Quantitative failure targets for deterministic/concurrency scenarios are zero duplicate entitlements, zero lost human edits, zero duplicate logical items from retries, and zero unsupported readiness/completion claims. In guided reviews, assess whether people can identify outcome, owner, next eligible work, blocker, and evidence without reconstructing an entire repository. Capture corrections and unnecessary blocking; do not use generated item count or story-point volume as success metrics.

## Existing integration and validation surfaces

Changes must remain consistent across intake, authority wording, state readers/writers, projections, lifecycle checks, and packaging. Relevant current sources include:

- `extensions/program-kit-governance/references/bootstrap-intake.schema.json`: typed intake and choice provenance. Delivery backend selection must be distinct from the workflow's existing coding-tool `integration` setting.
- `workflows/program-kit-bootstrap/workflow.yml`: intake/tooling/roadmap handoff and common activation entry point.
- `extensions/program-kit-governance/commands/speckit.program-kit-governance.roadmap.md`: current local roadmap authority contract.
- `extensions/program-kit-governance/scripts/governance_state.py`: state validation, configuration, and generated projections/authority wording.
- `presets/program-kit-governance-preset/templates/tasks-governance.md`: current local Active/Delivered transition instructions.
- Core implementation preflight/lifecycle scripts and mandatory extension hooks: retain their architecture, design, and evidence guarantees while adding enabled-mode delivery conditions.

Targeted checks observed during research include `tests/validate_governance_state.py`, `tests/validate_bootstrap_intake.py`, `tests/validate_bootstrap_semantics.py`, `tests/validate_intake_authoring.py`, `tests/validate_bootstrap_context.py`, `tests/validate_components.py`, `tests/validate_lifecycle_profiles.py`, and installed preflight coverage in `tests/validate_local_upgrade.py`. The newer `tests/validate_bootstrap_lifecycle.py` was part of concurrent uncommitted governance work in the original checkout; do not assume it is present until that work is incorporated. Confirm the available checks at each phase's baseline.

New delivery schemas, adapters, profile activation, reconciliation, claim concurrency, and recovery require new targeted coverage. These tests are planned, not existing coverage. Use relevant targeted checks plus the bounded `scripts/Test-ProgramKit.ps1` Development suite. Do not broaden Development with whole release-only validators or run complete Release after each edit.

Use chromium/webkit where local browser checks apply; Firefox acceptance remains in CI. Full local Release is the separate user-owned-terminal publication gate under AGENTS.md. Deterministic tests and connector exercises must not start paid coding agents; optional live acceptance remains separately user-invoked under the existing manifest rules.

## Explicitly deferred

- A local team-backlog backend and full bidirectional issue mirroring.
- Continuous background monitoring and autonomous reprioritization, staffing, or commitment changes.
- General pipeline/environment provisioning, patch campaigns, and coordinated release orchestration.
- Broad enterprise process migration, automatic adaptation to arbitrary custom rules, and unverified server editions.
- Full federation of independently authoritative delivery spaces across organizations/providers.

## Review boundary

The product direction is settled. Exact adapter transports, durable coordination storage, capability fallbacks, schemas, and packaging are technical decisions to resolve with the user in the relevant phase's grilling interview, informed by repository research and the phase-0 proof. If a required guarantee cannot be met within the accepted boundary, report the concrete limitation and return the affected scope decision for review rather than silently weakening behavior.

Phase 0 produced the common contract and provider capability proof, including explicitly approved disposable platform writes. The next step is the Phase 1 interview before implementing the optional module and core authority seam.
