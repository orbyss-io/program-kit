# ProgramKit Development Tools review set

Status: **convergence in progress**.

This is the sole active, human-led review set. The original `1.0.0` artifacts
remain a validated baseline, but they are no longer an approval candidate. The
human reopened the design to include Claude Code alongside Codex and to converge
the product section by section before a replacement exact review set is issued.
See `convergence-notes.md` for the current rulings and provider research.

The converging shape is a provider-neutral executable Development Tool
contract, one provider-neutral MCP stdio bridge, an exact generated Console
proof, and thin explicit-registration integrations for Codex and Claude Code.
It implements none of them.

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

Do not approve or implement the current `1.0.0` canonical design and plan. A
replacement review set with new versions and digests will be rendered and
validated after convergence. Only the replacement exact review set may be
approved through the registered `implement-software-plan` flow.

Corrective Reconstruction is held on the backlog and is not part of this
convergence.
