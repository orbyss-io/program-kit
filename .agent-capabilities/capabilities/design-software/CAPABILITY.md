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
- The exact `StaticConformanceDisposition@1.0.0` decision or the information
  needed for the human to make it.
- Supplied identity, authority, time, or correlation values when durable
  artifacts require them.

Outputs:

- A reviewable design artifact.
- A separate implementation plan with bounded, dependency-ordered work units.
- An adjacent human-readable documentation projection for the canonical
  implementation-plan artifact. The projection is explicitly
  non-authoritative, identifies its canonical source, and binds the exact
  current canonical digest.
- Exactly one explicit static-conformance disposition: `reuse-existing`,
  `extend-existing`, `create-new`, human-accepted `not-justified`, or
  `blocked-unavailable`.
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
- Do not silently start `design-csharp-build-gate`, approve an empty analyzer
  selection, implement or activate a gate, or renew a temporary exception.

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
5. Ask the mandatory static-conformance disposition question. Inventory the
   design's static invariants and require exactly one explicit
   `StaticConformanceDisposition@1.0.0`: reuse an exact compatible gate, extend
   one, create one, record a human-accepted empty selection with rationale and
   residual risks, or block because required backing is unavailable. Missing,
   null, defaulted, implicit-empty, and unaccepted-empty values are invalid.
6. If no compatible layered build gate exists and the human has not accepted
   an empty selection, ask: “This design has no compatible layered build gate
   and no approved empty selection. Should we design one?” A yes is an explicit
   human start of `design-csharp-build-gate`; run
   `program-kit capabilities preflight design-csharp-build-gate
   --workspace-root .` and then
   `program-kit capabilities read design-csharp-build-gate
   --workspace-root .`. A non-ready result is a setup blocker. A no is not
   empty acceptance and must leave an explicit human decision or a blocker.
7. Resolve reversible details independently; present material alternatives and
   tradeoffs to the human.
8. Produce an Architecture Design `0.1.0-alpha.2` artifact and a separate
   Implementation Plan `0.1.0-alpha.3`. Materialize an adjacent human-readable
   documentation projection for the canonical implementation plan in the same
   operation. Label the projection as non-authoritative, name the canonical
   source, bind its exact current digest, and state that canonical bytes govern
   any disagreement. Keep work units bounded, dependency-ordered, reviewable,
   and explicit about allowed edits, outputs, verification, and stop
   conditions. For `create-new` or `extend-existing`, place the exact approved
   gate-establishment fragment before every product and closure unit and make
   downstream work depend on compatible activation evidence.
   For every non-closure work unit, select verification that fully covers its
   directly changed scope and the finite reverse dependency/consumer closure
   that can be affected by it, including affected generated outputs, fixtures,
   integrity checks, and conformance slices. Do not default a non-closure unit
   to the repository-wide or full-plan suite. Select expensive checks by
   affected behavior rather than by cost alone: run them in the work unit when
   they are inside its affected closure and defer unrelated checks.
   Make the unit's exact commands and expected observations state the included
   affected closure and what remains deliberately deferred.
   Include exactly one final `closure` work unit that depends transitively on
   every product unit. Only that final unit runs the complete repository build,
   unit, conformance, exhaustive, integration, determinism, package, and other
   full-plan profiles. If a non-closure unit's affected closure is genuinely
   repository-wide, record that impact explicitly instead of presenting a
   broad default as focused verification.
9. Define deterministic fixtures and acceptance evidence proportional to risk.
10. Validate and render the artifacts through backed Program Kit operations when
   available; verify deterministic regeneration and freshness of the
   human-readable implementation-plan projection; record exact versions and
   digests.
11. Reconcile every human comment into an explicit change, disposition, or open
   decision.
12. Present the exact review set and stop for human approval.

Judgment owns architecture and tradeoffs. Deterministic tooling validates,
hashes, renders, and compares artifacts but cannot make approval decisions.

## Verification and failure reporting

Verify traceability from intent to design decisions, plan tasks, and acceptance
evidence; verify no unresolved material decision is hidden; verify the
canonical plan has an adjacent, readable, explicitly non-authoritative
projection; verify the projection binds the current canonical identity and
digest and regenerates byte-deterministically; and report every unavailable
check. Never present raw canonical plan JSON as the only human review surface.
State deliberately unimplemented or deferred work. Never label a design as
approved without the exact human decision record. Verify the disposition is
explicit, its gate selections or accepted empty value have exact human
authority, and every create/extend plan is establishment-first.

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

## Program Kit knowledge and failure resolution

Retrieve exact schemas with `program-kit schemas read
pkid:schema:program-kit:architecture-design@0.1.0-alpha.2` and `program-kit
schemas read pkid:schema:program-kit:implementation-plan@0.1.0-alpha.3`. Use
`commands describe` before unfamiliar backed operations. For Program Kit
failures, follow the `software-change-troubleshooting` resource and use
`diagnostics explain` and `artifacts inspect`; do not reverse-engineer
assemblies or guess a contract.

Before designing a typed .NET Console host or its consumer integration seam,
retrieve and follow `dotnet-console-input-materialization-guide`,
`dotnet-console-integration-project-example`, and
`dotnet-console-integration-source-example`. Read the exact
`dotnet-console-input-materialization-request@0.1.0-alpha.1` schema. The guide,
not the schema alone, defines the single-project handler/implementation seam,
ownership boundary, semantic-request mapping, and materialize-to-generate
journey.

## Provider wrapper mapping and drift check

Codex and Claude wrappers contain only trigger metadata plus exact
`capabilities preflight` and `capabilities read` invocations. The installed
CLI verifies their recorded bytes before returning this definition. A changed,
missing, unowned, stale, or version-mismatched wrapper is a setup blocker.
Initialization renders Codex beneath `.agents/skills/` and Claude Code beneath
`.claude/skills/`; `.codex/skills/` is exact legacy migration input only.
