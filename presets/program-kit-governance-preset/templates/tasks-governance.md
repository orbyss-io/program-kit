## Program Kit vertical delivery notes

Preserve the native task checklist and the project's own structure. Group related implementation
and verification around runnable outcomes; place minimal enabling dependencies beside their first
consumer. Retain relevant authorization, ownership, storage/migration, provider and recovery checks.
Use test-first where risk justifies it; check generated scaffolds before dependent behavior. Record
actual test owners/commands and run affected regressions when shared contracts change.
Keep implementation tasks aligned with selected framework mechanisms. Challenge a task introducing
a replacement runner, wrapper or lifecycle before implementing it; record a concrete unmet requirement
or correct the task. Tests of a custom mechanism alone do not justify its existence.

Use short readable notes for progress, unresolved failures, local choices and agreed review pauses.
For example:

| Outcome | Checks and walkthrough | Agreed review | Current disposition |
|---------|------------------------|---------------|---------------------|
| Request registration | Focused tests; register a request and observe its identity | Requester reviews runnable story | Pending; pause dependent work |

This table is optional. Existing prose or another readable task format is sufficient. Preserve
actual acceptance, change requests and bounded deferrals when the human provides them. Reviews
already agreed in the constitution or plan remain binding. Do not infer acceptance from checkmarks,
tests or time. No hidden checkpoint, timing ledger, hash receipt or toolkit state is needed.
