---
description: Supply applicable architecture and coding guidance before work.
scripts:
  py: scripts/phase_obligations.py
---
Locate the current Spec Kit feature. Run `{SCRIPT} project --feature-dir <feature> --phase planning`
before planning. Run `{SCRIPT} check --feature-dir <feature> --phase after-plan` before tasks,
and `check --phase implementation` before coding so the planned compilation graph is enforced.
Use the returned summaries as the default context. The focused section pointers are optional
lookup for a concrete unresolved choice, not a checklist to reread every source. Use `--only <id>`
for a focused follow-up. Apply their conditions to concrete design/code choices;
record decisions, exceptions and actual required tests in the existing plan and tasks.
Use the project's analyzers and targeted tests during implementation. Do not create phase-context,
obligation-design/review, semantic-contract or proof-attestation files. No renewed human approval
is needed for generated context, changed toolkit bytes or test execution.

## Task drafting and resume (before_tasks)

For tasks, use `--phase after-plan` even when resuming. Inspect existing tasks.md first.
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
