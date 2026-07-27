# ProgramKit Development Tools review set

This is one independent, human-led review set. It designs a provider-neutral
executable Development Tool contract, an exact generated Console proof, and one
explicitly registered thin Codex MCP adapter. It implements none of them.

Review in this order:

1. `design-intent.md` — recorded human outcome and exact decisions.
2. `architecture-design.md` — reviewer projection.
3. `architecture-design.json` — canonical design.
4. `implementation-plan.md` — work-unit projection.
5. `implementation-plan.json` — canonical plan.
6. `provider-contract-evidence.json` — authoritative Codex/MCP basis and drift
   gate.
7. `acceptance-fixtures.json` — deterministic positive/negative acceptance
   catalog.
8. `validation-report.md` — validation, digests, assumptions, and deferrals.
9. `review-manifest.json` — exact approval boundary and artifact digests.

Approval must name review set
`pkid:approval:program-kit:development-tools-review-set@1.0.0` and the exact
canonical design and plan SHA-256 values in the manifest. Approval authorizes
only `PKDT-W010` through `PKDT-W050` through the registered
`implement-software-plan` flow. Corrective Reconstruction is a separate review.
