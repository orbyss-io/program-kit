---
description: Finalize machine-checkable constitution ratification after the dedicated human gate.
---

## Input

`$ARGUMENTS` must contain the dedicated constitution gate verdict. Only the exact verdict `ratify`
authorizes finalization.

## Work

From the project root, run:

```text
python .specify/extensions/program-kit-governance/scripts/governance_state.py ratify --verdict ratify
```

Pass the actual workflow verdict, not a value inferred by the agent. The script rejects missing or
Draft-free state, template placeholders, TODOs, invalid semantic version/date metadata, and missing
amendment, versioning, or compliance governance. On success it writes a `Ratified` marker bound to
the exact constitution SHA-256 and metadata.

Do not modify the constitution to make validation pass. Return to the draft and human gate when it
fails. Rejection, abandonment, or any later constitution content change must not unlock architecture
or specifications.
