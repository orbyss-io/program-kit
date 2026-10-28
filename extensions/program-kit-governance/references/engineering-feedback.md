# Engineering discoveries and corrections

Use this method when research, review, implementation or a check exposes a consequential gap.
Keep the finding in the owning document or ordinary readable review/progress notes. No finding
database, mandatory schema, fingerprint, approval file or new lifecycle state is required. Missing
bookkeeping alone does not prevent native delivery; a real unresolved decision or engineering
failure constrains the work that depends on it.

## Find the correction owner

| Discovery | Owning correction | Dependent action |
| --- | --- | --- |
| Missing or contradictory user behavior, scope or rule | Spec; clarify with the human when needed | Revisit affected design and tasks |
| Invalid technical assumption, responsibility or contract | Research, plan or ADR | Resolve the choice and update dependent tasks |
| Missing coverage, dependency or task ordering | Tasks | Correct affected checks and sequence |
| Code violates a still-valid decision | Implementation | Repair and check the affected behavior |

Investigate accessible facts before asking for a decision. Cite the evidence/source location,
explain the consequence, propose a resolution and identify affected work. Distinguish documented
selected-version facts, local assumptions, experiments and unknowns. A task authored by an agent
is no authority for an unjustified design; a previous plan cannot defend an invalid assumption.

## Resolve and resume

1. Identify the actual product or technical decision owner. Resolve routine facts through focused
   research. For an unsettled material choice, present the alternatives, recommendation and
   consequences to that owner; preserve an existing applicable human decision.
2. Resolve the finding, or explicitly defer it with bounded scope, owner, next action and trigger.
   Keep dependent work paused while its prerequisite is unresolved; continue independent ready work.
   An explicit deferral cannot manufacture a working contract or waive an engineering failure.
3. Correct the owning spec, research, plan/ADR, tasks or source openly. Record the reason for a
   consequential change; do not silently amend the plan to justify a coding deviation. A Proposed
   ADR remains a proposal until its actual acceptance. Human review pauses retain their agreed
   meaning; agent recommendations, tests and silence cannot become human acceptance.
4. Reopen only dependent conclusions. Preserve unrelated accepted decisions, completed task IDs,
   checkmarks, authored customizations and history. Update affected tasks rather than regenerating
   the entire task plan. Private file/class refinements need no new decision when the agreed
   responsibilities, contracts, lifecycle/failure behavior and constraints still hold.
5. Rerun relevant review and checks whose inputs or conclusions changed. Reuse unaffected evidence
   with its real scope. Report unresolved findings and the next action in the normal phase handoff,
   then resume the remaining native flow and configured hooks when their prerequisites are resolved.

Native Analyze is **strictly read-only**: report its findings first. Any authorized correction is
a separate, explicit step after that report, performed through the owning documents/source; do not
edit files inside Analyze or describe a proposed repair as executed. Repeat affected analysis or
checks after correction when their inputs changed. Source review, executed checks, observed agent
behavior and actual human acceptance remain separate claims.
