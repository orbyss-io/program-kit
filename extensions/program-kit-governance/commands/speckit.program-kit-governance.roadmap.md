---
description: Create the governed project-level portfolio of candidate feature specifications.
scripts:
  py: scripts/governance_state.py
---

## Preconditions

Validate the ratified constitution before doing any work:

```text
{SCRIPT} validate
```

Read the constitution, architecture baseline, ADRs, decision backlog, tooling evaluation, quality
system, traceability model, and candidate vertical slices. Stop if ratification is missing or stale.

Read the approved bootstrap decision register and Accepted bootstrap-baseline decision. Explicit
intake choices and adopted Program Kit defaults do not appear as unresolved ADR prerequisites.
Genuinely unresolved decisions block only the roadmap entries they materially affect. Deferred
production, scale, retention, recovery, or long-running-operation choices do not block an unrelated
first vertical slice before their named trigger.

## Output

Create or update `docs/architecture/specification-roadmap.md`. This is a portfolio—the specification
of candidate specifications—not an implementable feature specification and never an input to
`speckit.implement`.

For each record use the heading `### <ID>: <Title>` and include exactly these bold fields:

- **User-visible outcome**
- **Scope**
- **Non-goals**
- **Required Accepted ADRs**
- **Dependencies**
- **Owned public contracts**
- **Owned lifecycle portions**
- **Owned data**
- **Quality scenarios**
- **Verification responsibility**
- **Recommended sequence**
- **Status**

Statuses are `Candidate`, `Blocked`, `Ready`, `Active`, `Delivered`, and `Superseded`. Bootstrap may
create Candidate, Blocked, and Ready records. A record is Ready only when every required ADR is
Accepted, its dependencies and ownership are explicit, and writing its feature specification would
introduce no hidden architecture choice.

Design tasks remain separate. They produce evidence, alternatives, Proposed ADRs, updated views, and
unlocked roadmap entries; they are not feature specifications or application implementation work.

After writing the roadmap, run:

```text
{SCRIPT} validate-roadmap
```

Report blocked records and the exact design task or ADR that can unlock each one.
