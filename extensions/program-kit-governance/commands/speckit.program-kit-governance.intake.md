---
description: Inventory an initial design and create an evidence-based bootstrap assessment.
---

## Input

Treat `$ARGUMENTS` as the path to the user-provided initial design. If the path is absent or unreadable, stop and report the exact problem. Do not infer a different design file when multiple candidates exist.

## Required reading

Read the entire initial design and every file under `.specify/extensions/program-kit-governance/references/`. Also read existing repository guidance and architecture artifacts without overwriting user-authored work.

## Work

Create or update `docs/architecture/bootstrap-assessment.md` with:

1. Purpose, actors, primary journeys, domain concepts, external systems, data classes, trust boundaries, quality attributes, deployment assumptions, and operational constraints found in the design.
2. A technology inventory. Mark every detected or suggested technology `Proposed` unless an existing Accepted ADR explicitly accepts it.
3. Contradictions, ambiguities, missing evidence, and risky assumptions with exact design references.
4. A decision backlog grouped by architecture significance. Include security, tenancy, authorization, isolation, consistency, delivery semantics, versioning, reproducibility, supply chain, observability, operability, and recovery when applicable.
5. A traceability table from design statements to architecture concerns and future decision tasks.

Create `docs/architecture/decision-backlog.md`. Each item must have a stable ID, question, why it matters, decision owner, dependencies, evidence needed, status, and the artifact that will close it.

Do not accept decisions, select final tools, initialize application code, or modify the initial design during intake.
