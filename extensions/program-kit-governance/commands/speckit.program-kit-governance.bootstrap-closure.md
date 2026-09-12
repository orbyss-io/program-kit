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

For each open architecture dependency of the intended first slice, execute one bounded compatibility
task. Author a Python recipe under `docs/architecture/compatibility/` that uses exact selected pins
and source identities and proves only required restore/runtime/port compatibility in its scratch
working directory. The recipe must declare inputs, versions, licenses and observable pass criteria,
fail nonzero on failed checks, terminate its child processes, and keep credentials out of output.
Run `python .specify/extensions/program-kit-governance/scripts/bootstrap_lifecycle.py proof --id
<agent-selected-prerequisite-id> --recipe <agent-created-relative-python-path> --timeout 120`.
This stage authorizes temporary compatibility projects/restores; architecture drafting itself does
not scaffold or restore the consumer. Do not write application files, launch coding agents, alter
machine toolchains or use this as a feature implementation task. An unavailable provider or runtime
produces an open blocker with evidence and a next action, never fabricated compatibility.

The runner retains a unique receipt and both streams for each attempt. Add the successful receipt
path/hash/kind to the prerequisite evidence and close only the proven dependency. Include design
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

When working from a recovery handoff, use `bootstrap_recovery.py synchronize --run-id <handoff-run>`
then `bootstrap_recovery.py review --run-id <handoff-run>` instead of the fresh-run batch below.
These commands allow the exact scoped follow-on Proposed bundle during review while readiness
and completion continue to require Accepted authority.

1. `python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-prerequisites`
2. `python .specify/extensions/program-kit-governance/scripts/governance_state.py synchronize-lifecycle`
3. `python .specify/extensions/program-kit-governance/scripts/governance_state.py synchronize-roadmap`
4. `python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-bootstrap`

Report executed proof results, exact affected slices, remaining blockers/owners/actions and paths.
Structural success is not readiness. Final approval reviews changed scope and dispositions;
the readiness producer subsequently owns its honest verdict.
