---
description: Supply applicable architecture and coding guidance before work.
scripts:
  py: scripts/phase_obligations.py
---
Locate the current Spec Kit feature. Run `{SCRIPT} project --feature-dir <feature> --phase planning`
before planning. Run `{SCRIPT} project --feature-dir <feature> --phase tasks` before tasks.
The after-plan hook already checked the planned graph; task drafting carries those choices without
immediately repeating that check. The after-tasks and combined implementation-check hooks validate
the current graph before affected coding. Do not invoke phase-context again before implementation.
Use the returned phase actions and canonical decision constraints before choosing patterns.
Their conditions, prohibitions and exceptions are binding guidance, not optional explanation.
Scoped accepted targets and feature ownership inform routing before a plan or project exists.
Resolve reported associations/conflicts; repository-wide adoption does not select every owner's mechanisms.
Use focused section lookup for a concrete unresolved choice, not a checklist to reread every source. Use `--only <id>`
for a focused follow-up. Apply their conditions to concrete design/code choices;
record decisions, exceptions and actual required tests in the existing plan and tasks.
Use the project's analyzers and targeted tests during implementation. Do not create phase-context,
obligation-design/review, semantic-contract or proof-attestation files. No renewed human approval
is needed for generated context, changed toolkit bytes or test execution.

## Retained feature planning decisions

The projection names open feature-plan prerequisite IDs, owners and tasks from retained history.
Draft their resolutions in the normal plan/contracts; pending review does not forbid that drafting.
After the actual normal design review, record each exact resolution with:
`python .specify/extensions/program-kit-governance/scripts/feature_plan_decisions.py record --feature-dir <feature> --prerequisite <id> --evidence "<feature>/plan.md#Exact heading" --reviewer "<actual reviewer>" --provenance "<actual review context>"`.
This preserves a small inline plan record and binds its reviewed section and existing intent/condition.
It creates no separate receipt or new human gate. Never invent human approval or substitute an agent's
review for a required ADR acceptance. Changed evidence reopens only its dependent decision.
Readiness and implementation consume this same resolution without changing the approved bootstrap ledger,
confirmed intake, constitution, ADR history or original approval hashes. A plan cannot close compatibility,
delivery, rights or production evidence. Missing legacy annotations are diagnosed for the affected decision;
do not automatically rewrite an existing approved plan.

## Task drafting and resume (before_tasks)

For tasks, use `--phase tasks` even when resuming. Inspect existing tasks.md first.
Run the ordinary setup_tasks script once to resolve the feature and composed tasks template;
reuse its result in the same turn. For a new draft, read spec.md, plan.md and the constitution,
then immediately persist a draft before optional
documents, detailed reference lookup or whole-plan validation. Use the installed
`python .specify/extensions/program-kit-governance/scripts/task_draft.py prepare --feature-dir <feature> --phases setup foundation US1 ... polish dependencies`
with the actual story phase identifiers from the specification. All progress stays in tasks.md;
the inline checkpoint records drafting progress, not acceptance, approval or test evidence.

On resume, run `prepare` before repeating design preparation. It returns completed/remaining phases and changedInputs without replacing
the draft. Reuse saved phases and preparation when inputs are unchanged; do not reload every
optional document or repeat broad reference preparation. Preserve IDs, checked boxes and edits.
For changed inputs, review only affected phases and their dependencies, edit those tasks in place,
then use `acknowledge-inputs` after that review. An unmarked existing tasks.md is preserved:
inspect and fill only gaps directly rather than starting over.

Write each completed phase to an ignored temporary content file, then persist it with
`task_draft.py save-phase --feature-dir <feature> --phase <id> --content-file <file>`.
Continue unique task IDs from the saved draft. Save Setup, Foundation and each story as soon
as it is ready; dependencies/parallel examples and the final coverage pass come last.
This incremental persistence replaces any instruction to hold all phases in memory before
writing tasks.md. Include constitution-required tests before their implementation tasks,
security, ownership and real-provider checks. Missing compatibility inputs/admission work
become owned prerequisite tasks with explicit dependencies; do not run probes, provision
services, restart bootstrap, alter approvals or change accepted pins while drafting.

After every planned phase and the final coverage/format review are saved, run
`task_draft.py finalize --feature-dir <feature>` for a marked draft. For an unmarked existing
document, finish that same review directly without requiring helper metadata. Then dispatch mandatory after_tasks hooks,
including read-only speckit.analyze. Do not invoke analyze on an incomplete draft or after
each phase write, and do not claim task generation completed while a draft remains.
