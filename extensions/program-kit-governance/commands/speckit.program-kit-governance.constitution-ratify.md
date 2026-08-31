---
description: Finalize machine-checkable constitution ratification after the dedicated human gate.
scripts:
  py: scripts/governance_state.py
---

## Input

`$ARGUMENTS` must contain the dedicated constitution gate verdict. Only the exact verdict `ratify`
authorizes finalization.

## Work

From the project root, run:

```text
{SCRIPT} ratify --verdict ratify
```

Pass the actual workflow verdict, not a value inferred by the agent. The script rejects missing or
Draft-free state, template placeholders, TODOs, invalid semantic version/date metadata, and missing
amendment, versioning, or compliance governance. On success it writes a `Ratified` marker bound to
the exact constitution SHA-256 and metadata.

The script is the sole ratification finalizer. After the human gate it changes only the explicit
Draft status and, for an initial constitution, the exact `PENDING_RATIFICATION` sentinel to the
current date before hashing the final content. It never repairs principles, governance, or arbitrary
validation failures. Return to the draft and human gate when any other validation fails. Rejection,
abandonment, or any later constitution content change must not unlock architecture or specifications.
