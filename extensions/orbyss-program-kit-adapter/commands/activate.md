---
description: Propose an explicit feature activation without selecting authority or constructing.
---

Invoke the deterministic adapter `activate` operation with the exact workspace
and request. Present its proposal for human review. Do not infer applicability,
profile selection, authority, or effect from prose.

Use only `.specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml`.
Ignore local configuration, environment variables, path globs, installation
order, and machine-global defaults. The executable only proposes an exact
consumer-owned edit; a human or agent acting for the consumer applies it and
then requests a new handoff review. Never initialize Program Kit, record
authority, select a grant, or construct.
