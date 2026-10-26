## Program Kit vertical delivery notes

Preserve the native task checklist and the project's own structure. Group related implementation
and verification around runnable outcomes; place minimal enabling dependencies beside their first
consumer. Retain relevant authorization, ownership, storage/migration, provider and recovery checks.
Use test-first where risk justifies it; check generated scaffolds before dependent behavior. Record
actual test owners/commands and run affected regressions when shared contracts change.
Keep implementation tasks aligned with selected framework mechanisms. Challenge a task introducing
a replacement runner, wrapper or lifecycle before implementing it; record a concrete unmet requirement
or correct the task. Tests of a custom mechanism alone do not justify its existence.

For each consequential approach, link the plan/research/ADR section that establishes its owner,
method or pattern, preserved semantic commitments, local adaptation and checks. Keep these decisions
usable in the task that consumes them without duplicating the full research. Put focused source
review/checks on the first coherent case of a new or uncertain approach before replicating it;
this technical review adds no automatic human checkpoint or per-task full-app acceptance run.
Private file/class refinements can evolve within the agreed contracts.

When implementation or review invalidates an assumption, use the shared
[engineering feedback method](.specify/extensions/program-kit-governance/references/engineering-feedback.md)
to correct the owning document and dependent tasks. Preserve unrelated decisions, completed IDs and
checkmarks, and actual human dispositions. A task is not authority to retain an invalid design.

Use short readable notes for progress, unresolved failures, local choices and agreed review pauses.
For example:

| Outcome | Checks and walkthrough | Agreed review | Current disposition |
|---------|------------------------|---------------|---------------------|
| Request registration | Focused tests; register a request and observe its identity | Requester reviews runnable story | Pending; pause dependent work |

This table is optional. Existing prose or another readable task format is sufficient. Preserve
actual acceptance, change requests and bounded deferrals when the human provides them. Reviews
already agreed in the constitution or plan remain binding. Do not infer acceptance from checkmarks,
tests or time. No hidden checkpoint, timing ledger, hash receipt or toolkit state is needed.
