# Coding guidance in native phases

Program Kit supplies relevant knowledge to ordinary Spec Kit planning, tasks, implementation and
review. It does not impose a parallel delivery engine, operation-brief eligibility gate or hidden
completion ledger. Product decisions, architecture, plans and tasks retain their normal ownership.

The implementation prehook renders a compact reference index. Read applicable details explicitly:

```text
python .specify/extensions/program-kit-governance/scripts/phase_obligations.py check --feature-dir specs/001-notes --phase planning
python .specify/extensions/program-kit-governance/scripts/phase_obligations.py project --feature-dir specs/001-notes --phase implementation --only persistence-adoption
```

Use `--page` when a focused reference continues. The CLI supports `project` and `check`; historical
`prepare`/`reconcile`, operation coding units and checkpoint protocols are not the current phase
entrypoint. Retained historical reports and pattern experiments do not restore those prerequisites.

## Select useful context

Read relevant constitution, product intent, ADRs, spec, plan, tasks and source. The helper uses feature
prose, selected native files and optional scoped architecture to identify applicable responsibilities.
Its lexical discovery can miss behavior or overselect it. Correct the scoped understanding through
normal engineering review rather than interpreting an index as semantic analysis.

The registry resolves attributable source rules. Initial output includes the general framework reuse
rule and, when installed/applicable, native EF migration guidance. Focused lookup returns the full
selected rules, including design-time context creation. Optional technology references can be absent;
that limits tooling guidance and supplies no compatibility result. Using knowledge does not require
adopting a generator, changing an existing lock or starting an entire application.

## Resolve implementation choices

Reuse selected framework mechanisms and supported extension points. Challenge the necessity of new
projects, runners, wrappers, parsers and lifecycle owners before implementing them. Inspect exact
selected-version contracts and record concrete unmet requirements and alternatives in existing
plan/ADR notes when a replacement is justified. Agent-written tasks and green checks do not supply
that justification. Keep business policy and genuine replacement boundaries application-owned.

For EF persistence use provider-owned migrations, model snapshots, EF history and EF deployment
artifacts. Deployment credentials and read-only runtime admission remain separate. Consult the
[native EF/Foundation example](../extensions/program-kit-dotnet/references/examples/postgresql-lifecycle/README.md).
For authentication, HTTP clients, serialization and frontend effects/state, use the selected
framework's actual supported lifecycle/configuration seams before inventing equivalents. This does
not select a new frontend framework, enable every optional library feature or qualify every stack.

## Verify and review

Use actual compiler/analyzer, architecture, security and behavioral checks appropriate to the change.
Run focused checks at the first coherent increment. Provider/database/browser tests own their actual
prerequisites and proof limits. A graph pass establishes dependency structure, not project necessity;
tests establish exercised behavior, not architecture suitability or human product acceptance.

Keep unresolved findings, changed decisions and agreed human review points in normal tasks/review
notes. Honor actual pauses before dependent work. No automatic independent reviewer or coding agent
is started by deterministic validation. [Completion review](coding-evaluation.md) describes the current
handoff; [consumer engineering](consumer-engineering.md) describes the common ownership rules.
