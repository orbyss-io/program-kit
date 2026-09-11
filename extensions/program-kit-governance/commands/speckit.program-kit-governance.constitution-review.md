---
description: Validate a drafted constitution and regenerate its current human review packet.
scripts:
  py: scripts/governance_state.py
---

## Purpose

Every initial constitution or amendment must reach the human ratification gate with deterministic
validation and a review packet bound to the exact current draft.

## Work

From the project root, run these exact commands in one shell batch with an available Python 3
interpreter:

```text
{SCRIPT} validate-constitution-draft
{SCRIPT} write-review --stage constitution
```

Copy both commands verbatim, including `--stage constitution`. Do not substitute another
`governance_state.py` subcommand, omit an argument, split validation into exploratory calls, inspect
a diff, or measure the file separately. If the batch succeeds, stop immediately.

Both commands must succeed after `speckit.constitution` finishes and before asking the user to
ratify. Show the regenerated `docs/architecture/reviews/constitution-review.md` at the dedicated
human gate. If validation fails, return to the draft; never reuse an older review packet and never
infer ratification from the drafting request.
