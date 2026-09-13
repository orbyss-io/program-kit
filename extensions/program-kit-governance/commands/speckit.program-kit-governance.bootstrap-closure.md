---
description: Close scoped bootstrap architecture prerequisites with bounded compatibility evidence.
---

You are the architecture owner of the lifecycle handoff after roadmap drafting and before final
bootstrap review. Read `references/bootstrap-lifecycle.md` in this extension, the approved decision
register, canonical map, referenced ADR conditions and proposed first slice. Use existing context;
do not reopen intake or ask users for paths, target IDs, filenames or manifests.

Create or reconcile `docs/architecture/bootstrap-prerequisites.json` using the contract reference.
Inventory every unresolved/deferred register item and every condition retained in every cataloged
ADR, including Accepted ADRs. Use `bootstrap_lifecycle.py source-hashes` to obtain source bindings;
fill condition references from source inspection, never infer that an empty list proves closure.
Keep the approved register and Accepted ADRs unchanged. Trace closure or changed disposition through
new follow-on decisions; their Proposed metadata and exact map scope are reviewed at the final gate.

Scope architecture prerequisites to the actual anonymous/public/admin journeys that depend on them.
Synthetic business inputs remove authoring dependencies only. They cannot prove a required durable
store, renderer, runtime or provider. Routine field rules, feature behavior tests and choices wholly
inside accepted boundaries belong to feature-plan. Production and later-release policy remain at
their actual triggers. Record the reason and source authority for every such disposition for review.

For each open architecture dependency of the intended first slice, prepare one bounded compatibility
task. Author a Python recipe under `docs/architecture/compatibility/` that uses exact selected pins
and source identities and proves only required restore/runtime/port compatibility in its scratch
working directory. Add the adjacent `.contract.json` with exact JUnit runtime case names. If
packages are needed, declare `fixtures` (scratch path to repository source file) and
`dependencyTargets` (bound csproj/package.json paths). The coordinator copies those inputs,
uses shared toolchain/source configuration, and executes shared renew plus locked restore before
running the probe. Under live acceptance, only the supervisor receives registry credentials;
the native shell executor submits the bounded handoff after this agent stage returns. Do not issue a separate
network restore or implement another package resolver inside the recipe.
The recipe must declare inputs, versions, licenses and observable pass criteria,
fail nonzero on failed checks, terminate its child processes, and keep credentials out of output.
Write `docs/architecture/bootstrap-proof-plan.json` with `schemaVersion: 1`, `probes`
(each has prerequisite `id`, repository-relative `recipe`, `timeout` from 1–600 seconds),
and `readyWhenProven` (each has roadmap `id`, the exact complete affected architecture
`prerequisites` list, and rationale that those are its only remaining readiness conditions).
Use empty arrays when no probe or conditional transition is needed. Keep prerequisite status
open and roadmap entries Blocked until execution succeeds. In a native workflow, return now;
the next shell step runs `bootstrap_proof_plan.py`, attaches successful receipts and applies
only those conditional transitions. Do not spend agent turns polling restores or running probes.
For a standalone owner-invoked closure, run that same deterministic executor once after preparation.
This stage authorizes temporary compatibility projects/restores; architecture drafting itself does
not scaffold or restore the consumer. Do not write application files, launch coding agents, alter
machine toolchains or use this as a feature implementation task. An unavailable provider or runtime
produces an open blocker with evidence and a next action, never fabricated compatibility.

The runner retains a unique receipt and both streams for each attempt and attaches successful
evidence to the exact prerequisite. It stops at the first failure; preserve that open blocker. Include design
authority evidence as appropriate. A failing attempt remains preserved; diagnose it before another
bounded attempt. No repeated truncation or ad hoc byte assertions.

Update the roadmap producer's artifact after evidence changes: affected entries stay Blocked until
their architecture prerequisites close. Write the explicit acceptance scope for founding and any
follow-on decisions; include only reviewed map elements/relationships with those decision refs.
Leave unfinished storage and unrelated proposals outside that scope. Replace duplicated current
status prose with source links or explicitly dated historical descriptions. Never edit or reratify
the constitution to replace status words. Escalate a necessary constitutional change through its
governed amendment procedure.

Run these commands as one terminal batch, stopping on the first failure:

When working inside a workflow continuation, return the corrected artifacts to the engine instead
of running the fresh-run batch below. Its native synchronization and review steps allow the exact
scoped follow-on Proposed bundle; readiness and completion still require Accepted authority.

1. `python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-prerequisites`
2. `python .specify/extensions/program-kit-governance/scripts/governance_state.py synchronize-lifecycle`
3. `python .specify/extensions/program-kit-governance/scripts/governance_state.py synchronize-roadmap`
4. `python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-bootstrap`

Report executed proof results, exact affected slices, remaining blockers/owners/actions and paths.
Structural success is not readiness. Final approval reviews changed scope and dispositions;
the readiness producer subsequently owns its honest verdict.
