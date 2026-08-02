# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`

**Created**: [DATE]

**Status**: Draft

**Input**: User description: "$ARGUMENTS"

## Intent, Authority, and Scope *(mandatory)*

**Intent Owner**: [named human or accountable role]

**Decision Authority**: [who resolves product ambiguity and accepts scope changes]

**In Scope**: [bounded outcomes this feature is authorized to deliver]

**Out of Scope**: [explicit non-goals and deferred boundaries]

**Unresolved Meaning**: [questions that require human clarification, or "None"]

## User Scenarios & Testing *(mandatory)*

<!--
  Order stories by value. Each story must be independently demonstrable and
  have positive, negative, and interruption/failure behavior where applicable.
-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe the user journey in plain language.]

**Why this priority**: [Explain the value and priority.]

**Independent Test**: [Describe the smallest public-boundary demonstration.]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [invalid, ambiguous, unavailable, drifted, or faulted state], **When** [action], **Then** [bounded diagnostic/result and permitted continuation]

---

[Add further prioritized stories as needed.]

### Edge Cases

- [Boundary condition and required result]
- [Invalid or ambiguous input and required result]
- [Unavailable dependency, interruption, drift, or fault and required result]
- [Sensitive or adversarial input and disclosure-safe result]

## Requirements *(mandatory)*

### Functional Requirements

<!--
  Keep stable FR identifiers. State behavior and observable boundaries, not an
  implementation design. Every MUST will receive an owner and proof in plan.md.
-->

- **FR-001**: System MUST [specific, testable capability]
- **FR-002**: System MUST [specific negative or failure-path behavior]
- **FR-003**: System MUST [specific contract, authority, or safety constraint]

### Requirement Classification

<!--
  Class is one of: behavior, contract, quality, safety, governance.
  Proof class is one of: executable-invariant, evidence-backed, human-review,
  aspirational. "Aspirational" cannot satisfy a release-blocking MUST.
-->

| Requirement | Class | Authority | Acceptance Boundary | Proof Class |
|-------------|-------|-----------|---------------------|-------------|
| FR-001 | [class] | [owner] | [observable outcome] | [proof class] |
| FR-002 | [class] | [owner] | [observable negative outcome] | [proof class] |

### Key Entities *(include if feature involves data)*

- **[Entity 1]**: [Meaning, identity, and relevant lifecycle]
- **[Entity 2]**: [Meaning and relationship]

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: [Technology-agnostic measurable outcome]
- **SC-002**: [Measurable negative-path, quality, or repeatability outcome]

## Assumptions and Dependencies

- **Assumption**: [Bounded default that does not grant new authority]
- **Dependency**: [External or internal dependency and owner]
- **Invalidation trigger**: [Change that requires the assumption to be revisited]
