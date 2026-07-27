# ProgramKit corrective reconstruction review set

This is one independent, human-led review set. It designs exact implementation
ownership, human corrective decisions, package-only clean-room reconstruction,
and honest cross-model/review evidence. It implements none of them.

Review in this order:

1. `design-intent.md` — recorded human outcome and exact decisions.
2. `architecture-design.md` — reviewer projection.
3. `architecture-design.json` — canonical design.
4. `implementation-plan.md` — work-unit projection.
5. `implementation-plan.json` — canonical plan.
6. `acceptance-fixtures.json` — deterministic positive/negative acceptance
   catalog.
7. `validation-report.md` — validation, digests, assumptions, and deferrals.
8. `review-manifest.json` — exact approval boundary and artifact digests.

Approval must name review set
`pkid:approval:program-kit:corrective-reconstruction-review-set@1.0.0` and the
exact canonical design and plan SHA-256 values in the manifest. Approval
authorizes only `PKCR-W010` through `PKCR-W060` through the registered
`implement-software-plan` flow. Development Tools is a separate review.
