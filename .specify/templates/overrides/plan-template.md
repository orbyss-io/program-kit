# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This project-local override is resolved ahead of the Spec Kit core
template. It is filled by `$speckit-plan`; it is not a fork of Spec Kit core.

## Summary

[Primary requirement, bounded technical approach, and smallest vertical proof.]

## Technical Context

**Language/Version**: [version or NEEDS CLARIFICATION]

**Primary Dependencies**: [dependencies or NEEDS CLARIFICATION]

**Storage**: [storage or N/A]

**Testing**: [test frameworks and project/suite boundaries]

**Target Platform**: [platforms or NEEDS CLARIFICATION]

**Project Type**: [library/CLI/service/etc.]

**Performance Goals**: [measurable goals or N/A]

**Constraints**: [security, determinism, offline, compatibility, etc.]

**Scale/Scope**: [bounded delivery size]

## Change Risk and Boundaries *(mandatory)*

**Risk Level**: [low / medium / high] — [reason]

**Affected Public Boundaries**: [contracts, CLI, schemas, artifacts, diagnostics]

**Affected Authority/Ownership**: [human and system owners]

**Dependencies and External Assumptions**: [exact dependencies and failure behavior]

**Explicitly Unaffected Areas**: [areas that do not require regression proof]

## Constitution Check

*GATE: Complete before Phase 0 research and re-check after Phase 1 design.*

Use `covered`, `unowned`, `deferred-approved`, or `not-applicable`; a bare
`PASS` is insufficient. Every applicable MUST must name its enforcement mode,
owner, evidence, failure disposition, and task/proof destination.

| Principle / MUST | Status | Enforcement Mode | Owner | Evidence / Boundary | Failure Disposition | Planned Task/Proof |
|------------------|--------|------------------|-------|---------------------|---------------------|--------------------|
| [reference] | [status] | [mode] | [owner] | [evidence] | [disposition] | [task/proof] |

## Requirement and Proof Matrix *(mandatory)*

Every FR, buildable SC, applicable constitutional MUST, public negative path,
and human-review obligation must appear exactly once as an owned row. Multiple
rows may share a proof, but no requirement may have an empty implementation or
proof owner.

| Requirement | Implementation Boundary | Proof Obligation | Proof Owner | Verification Tier | Invalidated By |
|-------------|-------------------------|------------------|-------------|-------------------|----------------|
| FR-001 | [boundary] | [test/evidence/review] | [owner] | [edit/story/pre-pr/ci/human] | [paths or semantic change] |
| SC-001 | [boundary] | [test/evidence/review] | [owner] | [tier] | [invalidation set] |

## Verification Strategy *(mandatory)*

| Tier | Purpose | Required Checks | Explicitly Excluded |
|------|---------|-----------------|---------------------|
| Edit | Seconds-scale feedback | Affected build and focused unit tests | Restore, evidence regeneration, full acceptance |
| Story | Prove one independent slice | Relevant unit/contract and focused acceptance | Unrelated suites and cross-platform matrix |
| Pre-PR | Catch local integration errors once | Isolated integration build, unit/contract, formatting of changed files | Full acceptance/conformance and cross-platform proof |
| CI | Authoritative merge proof | Full acceptance/conformance/evidence on required platforms | Duplicate local rerun |
| Human | Subjective intent/fitness | Named review of bounded claims and limitations | Mechanizable proof already established by CI |

**Evidence Reuse Rule**: [Define which exact inputs invalidate each proof. An
unchanged input set reuses the existing result; a timestamp or unrelated commit
alone does not invalidate semantic evidence.]

**Acceptance Invalidation Rule**: [Separate product/API behavior changes,
proof-only changes, and docs/format/metadata-only changes.]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
[Replace with the concrete repository paths affected by this feature.]
```

**Structure Decision**: [Explain the selected boundaries. Paths are planned
locations, not independent requirements unless the architecture makes them so.]

## Complexity Tracking

> Fill only for justified constitutional or architectural complexity.

| Complexity | Why Needed | Simpler Alternative Rejected Because | Removal/Revisit Trigger |
|------------|------------|-------------------------------------|-------------------------|
| [item] | [need] | [reason] | [trigger] |
