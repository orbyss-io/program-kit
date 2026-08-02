---
description: Propose a bounded handoff from approved Spec Kit meaning.
---

Invoke the deterministic adapter `handoff` operation only when applicability is
explicit. Treat the proposal as seeded input requiring named human review; it
is not authority and must not be inferred from free prose.

Resolve applicability first from the exact project config at
`.specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml`.
Ignore local/environment/ambient layers. Return immediately for disabled or
not-applicable work; inherited `assist` with unresolved applicability is
non-blocking. Only unresolved `required` may request a decision. Never
initialize Program Kit, record authority, select a grant, or construct.
