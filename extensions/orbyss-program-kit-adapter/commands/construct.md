---
description: Explicitly construct from reviewed inputs and one caller-supplied exact grant.
---

Invoke the deterministic adapter `construct` operation only after the human has
approved the current proposal and a configured repository authority provider
has recorded one exact grant. Never select, create, widen, or reuse a grant.

Use only `.specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml`
for semantics; ignore local/environment/ambient layers. Resolve applicability
before profiles and pass exactly the caller-supplied grant. This command does
not initialize Program Kit or record authority itself.
