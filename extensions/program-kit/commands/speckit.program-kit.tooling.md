---
description: Turn researched capabilities into a staged repository quality system.
---

## Input

`$ARGUMENTS` identifies the initial design, assessment, and tooling evaluation.

## Work

Create or update `docs/architecture/quality-system.md` containing:

1. A capability matrix mapping each quality risk to prevention, static detection, test detection, runtime detection, owner, and evidence artifact.
2. A staged adoption plan: bootstrap gates, first-code gates, first-contract gates, first-deployment gates, and scale/compliance gates.
3. Exact trigger conditions for reevaluating optional tools and Spec Kit extensions.
4. A CI policy that is the authoritative enforcement layer. Spec Kit hooks provide early feedback but are not the sole control.
5. Upgrade policy: pin versions, inspect release notes and scripts, exercise representative fixtures, and promote only after compatibility checks pass.

Generic programming guardrails apply automatically. Project-specific tool selection and architecture choices remain Proposed until their ADR is accepted. Avoid duplicating capabilities already supplied effectively by the language toolchain, platform, or accepted repository tooling.

