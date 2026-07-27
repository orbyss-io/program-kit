# design-software

## Identity and trigger

`design-software` owns repository-grounded software design and implementation
planning. Use it when a human directly asks for design or planning, or explicitly
continues a routed request into the design flow.

## Purpose

Turn explicit human intent and repository-owned source truth into reviewable,
versioned design and implementation-plan artifacts. Surface assumptions,
boundaries, verification, and unresolved decisions, then stop for human
approval.

## Non-goals

- Do not approve the design or plan.
- Do not implement the plan or silently create runtime architecture.
- Do not treat a recommendation, routing result, or generated artifact as human
  authority.
- Do not create release, deployment, promotion, feed-transport, hook, watcher,
  MCP, tool-binding, or autonomous-loop behavior.
- Do not backdate receipts or claim authorship of pre-existing artifacts.

## Inputs and outputs

Inputs:

- The human's explicit design intent, scope, constraints, and requested depth.
- Applicable `AGENTS.md` guidance and repository-owned source truth.
- Existing accepted designs, contracts, schemas, plans, decisions, and evidence
  explicitly in scope.
- Supplied identity, authority, time, or correlation values when durable
  artifacts require them.

Outputs:

- A reviewable design artifact.
- A separate implementation plan with bounded, dependency-ordered work units.
- Explicit assumptions, decisions, deferred work, and blockers.
- Deterministic validation/rendering evidence and exact artifact digests.
- A human approval request; no approval decision.
- A development receipt only for the actual post-registration design event.

## Preconditions

- A human has requested the design work and named the repository or artifact
  scope.
- Required source truth exists or its absence can be reported honestly.
- Material authority decisions remain available to the human.
- Any design spike that changes files is separately and explicitly authorized.

## Allowed actions

- Read and analyze relevant files inside the named repository.
- Run non-mutating discovery, validation, rendering, graphing, and test commands.
- Create or update design, plan, fixture, and supporting documentation artifacts
  within the approved scope.
- Perform a bounded design spike only when the human explicitly authorizes that
  spike and its disposable or retained outputs.
- Request focused human decisions when alternatives materially change scope or
  architecture.

## Prohibited actions

- Do not implement application/runtime behavior under design authority.
- Do not originate approving principals, authority references, evidence, or
  approval decisions.
- Do not inspect sibling repositories or unrelated history.
- Do not access secrets or the network unless explicitly authorized and needed.
- Do not overwrite, delete, reset, or broadly move user data.
- Do not create speculative capabilities or provider wrappers.

## Stop conditions

Stop when a material decision requires human authority, repository source truth
conflicts with the requested direction, the scope would expand beyond the
request, or required evidence is unavailable. Stop after presenting a validated
review set for approval. Do not continue into implementation until the exact
design and plan have a valid, non-superseded human approval.

## Source of truth and freshness

Start from the current human intent and current repository-owned files. Re-read
documents immediately before calculating final digests. Treat generated
projections as non-authoritative unless their canonical source and freshness
binding verify. Do not import sibling-repository conventions or remembered
designs.

## Procedure

1. Confirm authority, scope, intended deliverables, and material non-goals.
2. Read applicable guidance and inspect only relevant repository-owned source
   truth.
3. Separate implemented, scaffolded, deferred, and aspirational claims.
4. Model identities, ownership, semantic boundaries, invariants, dependencies,
   failure behavior, authority, versioning, migration, and evidence.
5. Resolve reversible details independently; present material alternatives and
   tradeoffs to the human.
6. Produce a design artifact and a separate implementation plan. Keep work
   units bounded, dependency-ordered, reviewable, and explicit about allowed
   edits, outputs, verification, and stop conditions.
7. Define deterministic fixtures and acceptance evidence proportional to risk.
8. Validate and render the artifacts through backed Program Kit operations when
   available; record exact versions and digests.
9. Reconcile every human comment into an explicit change, disposition, or open
   decision.
10. Present the exact review set and stop for human approval.

Judgment owns architecture and tradeoffs. Deterministic tooling validates,
hashes, renders, and compares artifacts but cannot make approval decisions.

## Verification and failure reporting

Verify traceability from intent to design decisions, plan tasks, and acceptance
evidence; verify no unresolved material decision is hidden; verify rendered
projections match their sources; and report every unavailable check. State
deliberately unimplemented or deferred work. Never label a design as approved
without the exact human decision record.

## Authority and safety boundaries

The human owns architectural approval and any authority, identity, evidence, or
time values. Keep filesystem work inside the named repository and approved
artifact paths. Network, secret, provider, destructive, and external-system
actions require separate explicit authority.

## Compatibility and versioning

Preserve the stable capability ID for compatible procedure improvements.
Changes to approval boundaries, artifact contracts, or allowed implementation
behavior require an explicit compatibility review and new definition digest.
Renames, splits, supersession, or retirement require human approval plus index
and wrapper migration.

## Provider wrapper mapping and drift check

The Codex wrapper at `.codex/skills/design-software/SKILL.md` is a thin loader
for this file. Verify its exact pointer, confirm it contains no copied design
rules, and confirm the capability index links to both canonical and wrapper
paths.
