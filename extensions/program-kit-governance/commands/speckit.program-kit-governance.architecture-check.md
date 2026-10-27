---
description: Review actual design or implementation, resolve consequential choices and preserve accepted architecture.
scripts:
  py: scripts/phase_obligations.py
---

Before a feature directory exists, review the request and relevant constitutional/architectural
context directly. Do not create a feature or require toolkit metadata merely to run a hook.
For after-plan or after-tasks, `{SCRIPT} check --feature-dir <feature> --phase after-plan`
(or `after-tasks`) supplies relevant references without changing files or running engineering.
Read the relevant sources behind that index. Rendering references does not perform this review.

## Post-plan technical review

After planning, inspect the actual spec, research, plan, contracts/data model where relevant,
constitution and applicable accepted architecture/ADRs. Trace consequential choices to the outcomes
they serve and the selected dependency versions. Read focused authoritative documentation, relevant
coding patterns, security guidance and Program Kit integration knowledge; do not load a whole catalog.
Use the phase index as a starting point and correct missing or irrelevant context through inspection.

Review in proportion to the uncertainty and consequences:

- Fit to required behavior, authorization, ownership, domain boundaries and failure outcomes.
- Alternatives, especially the selected framework's native mechanisms and supported extension points.
  Explain the concrete unmet requirement before adding equivalent custom infrastructure.
- Source applicability and exact selected-version facts. Distinguish documented facts, assumptions,
  justified decisions and unknowns requiring a focused experiment or platform qualification.
- Contract promises, lifecycle transitions, data ownership, compatibility and security consequences.
  Application/process owners coordinate business workflow; providers own concrete mechanisms, SDKs,
  platform identifiers and reconciliation state. Keep infrastructure capabilities at their cohesive
  semantic boundary rather than placing every shared contract in a business-domain Core.
- Selected coding approaches, their important invariants and permitted adaptation, and the focused
  checks that can challenge them. A local design needs actual contracts and checks, not catalog approval.
- Technical risks and useful early experiments. Plan review is not compilation, runtime execution,
  provider compatibility or human acceptance; identify which evidence remains to be obtained.

Planning fixes responsibilities, contracts, consequential constraints and important lifecycle/failure
semantics. A suggested private file/class arrangement may evolve during coding. Do not require a
human decision for every internal refinement. Resolve material changes to those commitments through
the owning decision rather than labeling them private implementation detail.

Present a concise technical walkthrough linking the decisions, source facts, reasons and meaningful
trade-offs in ordinary research/plan/ADR content. Make selected methods, commitments, adaptation points
and checks usable by task generation without imposing a mandatory table or duplicate architecture model.
For a new or uncertain approach, identify a first coherent increment for focused source review and
checks before replication; this does not automatically create a new human checkpoint for every task.

Investigate accessible facts yourself. For a genuinely unsettled product or architectural choice,
reuse `speckit.program-kit-governance.grilling`'s interview method in this conversation:
ask only the dependent questions that matter, with evidence, a recommendation and material trade-offs.
Keep the scope to that choice, preserve accepted decisions and apply supported authorized defaults.
Do not force an interview about settled defaults or launch another coding agent. Use the relevant
existing human review point for the resulting synthesis; existing explicit acceptance of the exact
decision counts. An agent recommendation or Proposed ADR does not supply human acceptance.

Resolve material questions before dependent task generation. Use
[engineering feedback](references/engineering-feedback.md) for consequential findings and owning
document corrections. Continue independent ready work and preserve unrelated accepted decisions.

## Other phase and implementation review

Compare actual responsibilities, boundaries, contracts and important failure paths across spec,
plan, tasks and changed code. Preserve accepted decisions; reopen substantive contradictions with
source locations and a concrete correction. Missing toolkit history is not an application failure.
Select compiler/architecture/security/behavior checks appropriate to the selected technology and action;
planning describes needed checks rather than claiming application execution.
Optional .NET graph and SDK helpers remain with their engineering owner; a graph pass alone cannot
establish that ownership labels match real behavior.

Challenge the necessity of new infrastructure as well as its dependencies. Compare each new project,
runner, wrapper and lifecycle with the selected framework's existing mechanism and supported extension
points. A task prescribing a replacement does not justify it. Report the concrete unmet requirement
and evidence, or correct the affected plan/tasks to use the native mechanism before dependent work.
For EF, separate deployment identity does not imply a custom migration runner or parallel journal.

Inspect the first coherent operation before replication: its method bodies, authoritative state
types/keys and transitions, pure policy versus provider effects, effective configuration and required
snapshots, complete deadlines and resource teardown. Review the actual project-local placement and
mirrored tests; do not accept unrelated root accumulation merely because files compile. The selected
.NET API uses Operations/<Operation>; a small cohesive project may stay flat. Challenge a malformed,
denied, stale or faulted case through its actual check owner. These are semantic review duties;
reference routing and static analysis do not automatically detect or certify them. See the canonical
[first-operation review](references/programming-guardrails.md#typed-boundaries-and-design-evidence) and
[project-local placement](references/modularity-and-contracts.md#semantic-capability-contracts).

Keep unresolved findings and agreed human review pauses in normal task/review notes. Independent
ready work remains available. After implementation, report actual checks, semantic review, remaining
work and human dispositions separately. Run complete applicable acceptance at feature closure;
do not run a whole-app command for each progress update or infer acceptance from checked tasks.
Use normal native analysis and its read-only output; report findings before any separately authorized
correction, following engineering feedback. Do not create approval/proof dossiers.

For .NET host/exporter choices, apply `principle.dotnet-host-default` in
references/tool-selection.md. Review a custom-host proposal against actual human opt-out,
keep unresolved choices visible, and resolve the effective profile before reading versioned
package knowledge. A proposal, helper pass or profile listing supplies no human acceptance.

For background/queued work or replaceable providers, consult references/asynchronous-workloads.md
before choosing shared contracts. Research the relevant source-map alternatives, explicit environment
closures and failure semantics; keep coordination, execution and exchange separate. Use only the
focused references needed by this journey. Synthetic tests do not qualify an actual platform.

## Return to the native caller

When invoked as a configured hook, complete the substantive review before returning. If a material
decision needs a human answer, pause dependent work and resume this review after the answer; then
return to the outer native command so it can continue its remaining configured hooks and completion
report. Returning from this hook does not finish the caller's flow. Preserve disabled/removed hooks
and native condition handling; this command does not add another reviewer or re-enable configuration.

The native after-plan dispatch must actually invoke this command and wait. An `EXECUTE_COMMAND:`
marker, reference-helper output or recommendation to run architecture-check later is not execution.
In the phase report name the review actually performed, key decisions, unresolved findings, actual
human dispositions and next action. Report unavailable or blocked review honestly. Missing toolkit
files or historical status alone do not block native delivery; unresolved decisions and engineering
failures constrain the work that depends on them.
