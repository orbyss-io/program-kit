---
description: Validate exact config, applicability, handoff, review, trace, and ownership state.
---

Invoke the deterministic adapter `validate` operation. Use only its structured
result. Disabled and not-applicable features must remain non-blocking and must
not launch Program Kit or create feature artifacts.

Resolve applicability first from the exact project config at
`.specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml`;
ignore local/environment/ambient layers. Inherited `assist` with unresolved
applicability is non-blocking; unresolved `required` requests an explicit
applicable, disabled, or not-applicable decision. Validation never initializes
Program Kit, records authority, selects a grant, or constructs.
