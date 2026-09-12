---
description: Grill and confirm one proposed feature before speckit.specify creates or updates its specification. Runs automatically as a mandatory pre-specification hook and resumes interrupted feature interviews.
---

## Entry and scope

This is the feature-intake gate for `speckit.specify`. Read and follow the shipped interview method at
`.specify/extensions/program-kit-governance/commands/speckit.program-kit-governance.grilling.md`
in the same conversation. Read `references/specification-intake.md` for its artifact and CLI contract.
The user need not invoke grilling separately. A missing method is an incomplete installation.

Use the triggering feature request and select its exact specification-roadmap entry from the
configured roadmap. Resolve an unambiguous match yourself; if multiple entries fit, ask which one.
An unrelated Ready entry does not authorize this feature. A new feature requires a Ready entry;
an existing specification may resume its Active entry. A missing/Blocked entry needs roadmap or
architecture work before this gate can proceed. Do not relabel an entry just to pass validation.

Run `scripts/specification_intake.py begin --entry <ID> --request <feature-request>` from the consumer
root. This validates installation, ratification and the selected entry and resumes existing evidence.
Keep the interview under `.program-kit/specification-intake/<ID>/`. Until the gate passes, do not
create a spec directory, branch, `spec.md`, or `.specify/feature.json`; do not call `speckit.specify`
recursively. Other pre-hooks that create branches must be ordered after this gate.

## Interview and review

Compare the current request with any saved brief before reusing its confirmation. A saved receipt
does not authorize new scope. Preserve settled answers and stable question IDs. Reopen changed
decisions and their dependents; inspect changed governance sources to identify affected branches.
Bootstrap intake is context, not feature confirmation. Reuse approved facts and applicable defaults.

Work through the problem, affected users, observable outcome, scope and non-goals, main journeys,
failure cases, dependencies and measurable acceptance criteria. Explore permissions, data/lifecycle
effects and operational constraints where they materially affect this feature. Keep depth proportional
to uncertainty and risk; do not impose a minimum question count. A clear small feature can proceed
directly to a concise review with disclosed facts/defaults and their provenance.

Save the draft brief and decision record after each round so an interrupted conversation can resume.
Do not generate the spec while waiting for answers. Investigate accessible facts yourself. Defer
planning details only when they do not block scope or feasibility, with an owner/next action and
trigger. Material architecture choices remain subject to the existing ADR gates.

Once the interview is complete, run `review`, present its complete concise synthesis to the user,
and wait for explicit confirmation of that exact review. This is the grilling method's one
shared-understanding review, not an additional approval round. Existing explicit approval of the
exact presented synthesis counts. Silence, partial answers, "accept all" for a question round,
bootstrap approval and automatic workflow approval settings cannot confirm a feature review.

Only after that confirmation, run `confirm` with the presented review hash, the user's actual
confirmation text, and its conversation message/turn reference. Never invent confirmation evidence.
Run `check --entry <ID>` immediately before returning success to the waiting `speckit.specify`.
A missing, invalid or stale review/receipt is a blocking result; resume the affected interview.

## Handoff

Return the confirmed brief path, SHA256 and roadmap ID from `check`. Tell the waiting specify command
to use that brief as the elaborated feature description, preserving explicit scope, exclusions,
defaults and deferred items. Do not claim `BRANCH_NAME` or `FEATURE_NUM`: this hook creates neither.
Include the exact brief path and hash in the spec's Governance Traceability fields from the preset.
For standalone intake, report readiness; do not start specification unless the user requested it.
The existing `after_specify` clarification still runs. If drafting/clarification introduces material
scope changes, reopen affected intake decisions and reconfirm before proceeding to planning.
