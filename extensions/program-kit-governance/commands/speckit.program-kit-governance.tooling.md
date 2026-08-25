---
description: Turn researched capabilities into a staged repository quality system.
---

## Input

`$ARGUMENTS` identifies the initial design, assessment, and tooling evaluation.

Validate and read the ratified constitution before producing the quality system. Stop when the
constitution-ratification hash is missing or stale.

## Work

Create or update `docs/architecture/quality-system.md` containing:

1. A capability matrix mapping each quality risk to prevention, static detection, test detection, runtime detection, owner, and evidence artifact.
2. A staged adoption plan: bootstrap gates, first-code gates, first-contract gates, first-deployment gates, and scale/compliance gates.
3. Exact trigger conditions for reevaluating optional tools and Spec Kit extensions.
4. A CI policy that is the authoritative enforcement layer. Spec Kit hooks provide early feedback but are not the sole control.
5. Upgrade policy: pin versions, inspect release notes and scripts, exercise representative fixtures, and promote only after compatibility checks pass.
6. Dependency enforcement for the accepted bounded-context, module, feature, and contract graph. Include forbidden project/package/assembly edges, cycles, shared-store access, exception allowlists, and ownership evidence.
7. Slice-completeness evidence covering public schema compatibility, composition, authorization, observable outcomes, and architecture tests at the earliest reliable lifecycle stage.

Generic programming guardrails apply automatically. Project-specific tool selection and architecture choices remain Proposed until their ADR is accepted. Avoid duplicating capabilities already supplied effectively by the language toolchain, platform, or accepted repository tooling.
