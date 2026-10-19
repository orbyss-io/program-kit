---
name: program-kit-development
description: Develop and repair the Program Kit repository through existing owners, proportional validation and guided human review. Use for contributor changes; consumer application delivery and release execution retain their separate workflows.
---

# Program Kit Development

Read the selected checkout's [AGENTS.md](../../../AGENTS.md), relevant nested
instructions and [validation procedure](../../../docs/validation.md). Repository
policy can differ across branches; historical checkpoint commands are evidence,
not current instructions. This skill guides contributor work, without requiring
the consumer Spec Kit lifecycle or a new runner, ledger or approval artifact.

## Investigate and agree the outcome

- Inspect actual branch/commit, dirty and untracked changes, worktrees, ownership,
  user intent, constraints and existing approvals. Protect other owners' work;
  use an isolated checkout when needed without importing unfinished changes.
- Trace the relevant producer, callers, native implementation, canonical guidance,
  tests and installed/package representation where affected. Check selected
  dependency/profile/toolchain facts before promising a runnable demonstration.
  A reference or historical finding does not establish a current defect or gap.
- Resolve routine implementation choices yourself. For material product, ownership,
  compatibility, data/security or architecture uncertainty, present the facts,
  recommendation and concrete inspectable outcomes. Grill only consequential
  unsettled choices when the grilling skill is available; do not reopen approvals.
  Confirm shared understanding before implementing the affected uncertain scope.
  Continue independent authorized work where safe.

## Scale the work and implement through its owners

A small edit can proceed directly to its diff and appropriate checks. For a bug,
establish the trigger/cause and a meaningful regression where practical. For
substantial work, agree useful sections, observable outcomes, proof limits and human
review boundaries before implementation. By default, finish the current section,
guide its review and wait before the next; the human can authorize several together.
Do not impose one section per session or ask approval for every local choice.

Extend existing source, generators, native contracts and maintained validation
owners. Inspect emitted/installed output when that is the changed contract. Preserve
authored customizations and history; generation or hashing supplies no new authority.
Review semantic responsibilities and behavioral preconditions as well as structure.
Use [consumer engineering](../../../docs/consumer-engineering.md) and the relevant
coding documents when changing those product mechanisms, rather than copying their
policy into this skill. Concrete missing support needs an owner and repair route.

## Validate the claim

Follow actual AGENTS.md and the single [inventory](../../../tests/validation-inventory.json).
Inspect selection, prerequisites and existing bounds; add maintained coverage for a
new contract when needed. Choose expensive/manual scenarios for a concrete affected
risk. Unknown coverage and missing tools stay visible; do not invent a full-suite
fallback. Keep dependency upgrades in their separate [maintenance procedure](../../../docs/maintenance/dependency-review.md).

When claiming a safeguard, rejection, freshness or preservation guarantee, exercise a
representative violation and the intended rejection, plus relevant preservation or
unaffected behavior. Derive expectations independently of generated metadata. For
compiled behavioral negatives, require a successful build before the intended failure
marker; setup/import/compiler failure cannot satisfy that claim. Simple prose edits
do not automatically need adversarial fixtures.

Keep source fixed during input-bound validation. Retain actual commands, both streams,
source/dirty-input identities, relevant environment, outcomes and measured cost through
existing diagnostics. Preserve original failures and explain focused repairs; later
passes do not rewrite earlier results. Functional success can still exceed its budget.
Respect known host limits, including local Firefox, under actual AGENTS.md. Never
weaken product behavior or assertions to accommodate a fixture or host failure.

## Walk through actual output and hand off

Explain the delivered happy path using useful inline source/diff/output excerpts,
then relevant negative behavior and open findings. Name what to inspect and why.
For a small edit, chat plus the diff/results can suffice. For substantial review,
retain a short index linking exact files, outputs, before/after snapshots and
reproduction instructions. Review material stays available across sessions; a
passing test does not finish human review or authorize cleanup.

Distinguish automated execution, authored semantic review, observed agent behavior
and human acceptance. Label fictional authoring and simulated decisions. A selected
skill, status JSON, hash or screenshot cannot establish all four. State unexecuted
scope, uncertainties and what each result actually proves.

Hand off exact checkout/source state, settled decisions, completed section, actual
checks/costs, remaining findings, retained material and the precise next action.
Keep concise observed lessons and suggestions distinct in the existing handoff.
Implementation does not grant paid-worker/provider, messaging, consumer restart,
cleanup, commit/push, PR or publication authority. For authorized contribution or
release work, follow [README](../../../README.md#development-and-release) and
[releasing](../../../docs/releasing.md); do not duplicate their lifecycle.

Read [examples](references/examples.md) when choosing the scale or review format.
Read [observed lessons](references/observed-lessons.md) when examining this workflow's
evidence and limits; ordinary edits need not load the F1–F8 history.
