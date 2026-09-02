---
description: Normalize a user-provided design into a compact, provenance-bound bootstrap brief.
---

## Input

Treat `$ARGUMENTS` as the exact path to the user-provided initial design. Read that file in full.
Do not read Program Kit architecture, technology, tooling, or default-adoption references during
this step. Normalization records what the user said; it does not apply Program Kit defaults,
perform current research, or make architecture decisions.

## Output

Create `docs/architecture/bootstrap-brief.json` as a concise JSON object matching
`.specify/extensions/program-kit-governance/references/bootstrap-brief.schema.json`.

The brief must:

- bind `source.path` and `source.sha256` to the exact initial-design file, expressing the path as a
  project-relative forward-slash path even when the input argument is absolute;
- summarize the project in at most two short sentences;
- record explicit facts with stable IDs and exact `path:line` evidence;
- record explicit exclusions separately from facts;
- list actors, observable journeys, quality requirements, and ambiguities only when the design
  supplies evidence for them;
- populate routing signals for languages, frameworks, interfaces, and explicitly included or
  excluded capability surfaces;
- use empty arrays when the design is silent;
- preserve ambiguity instead of resolving it; and
- contain no recommendations, researched versions, Program Kit defaults, inferred technology,
  implementation plan, architecture proposal, or copied reference prose.

Keep the file under 16 KiB. Do not modify the initial design or create any other project artifact.
After writing it, run:

```text
python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py validate-brief --run-id <workflow-run-id>
```

When the workflow-run ID is not available to the command integration, leave validation to the next
deterministic workflow step. Report only the brief path, byte size, fact count, exclusion count, and
ambiguity count; do not print the full JSON.
