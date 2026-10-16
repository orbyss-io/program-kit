---
name: program-kit-repair-evaluator
description: Assess explicitly scoped Program Kit consumer repair observations, map historical terminology and propose evidence-based dispositions to the implementation owner. Repository contributors only.
---

Read the shared versioned diagnostic contract and operating procedure under
extensions/program-kit-governance/references/repair-feedback/. Use the same
published questions, terms, schema and upstream correlation as the reporter.
Inspect existing evidence from explicitly scoped consumers or the durable intake
queue. Asking an active consumer for more evidence is separately configured;
this skill grants no messaging, interruption, rerun or consumer-write authority.

Use docs/maintenance/repair-feedback.md for owner registration, bounded inbox
discovery, exact inspection, public packet import and the existing-ledger decision
adapter. Start with `python scripts/repair_evaluator.py --root <chosen-root>
--owner <explicit-owner> inbox`. Follow `next` with `--after`; use `--request-id`
to narrow large queues. Invalid or unrouted entries require repair or explicit
owner binding, never silent adoption. Never infer an owner from an active chat.
The chosen checkout must already contain this feature; integrate it normally
before receiving work, without copying another checkout's uncommitted changes.

Keep original accounts, hashes, selected profile/knowledge versions and evidence
intact. Unknown contract versions stay preserved; map terminology in a separate
assessment using scripts/repair_evaluator.py. Unknown concepts remain unclassified;
record assessment version and unknown fields without inventing answers to newer
questions. Distinguish reported, inspected and independently reproduced proof.
Never request private chain-of-thought.
New assessments use version 1.1 with the exact registered ownerRoute. Version 1.0
remains historical/read-only. Submission checks complete current-contract evidence,
delivery/import provenance, routing and versions. Historical imports retain an
explicit unqualified label. Public import reads a pinned PR as data; opening a PR
or passing the guardian alone does not establish maintainer acceptance.

Compare the observed path against attributable expectations under actual consumer
versions and constraints. Assess Program Kit ambiguity, correctness, discoverability
and guidance gaps alongside consumer mistakes or valid domain adaptations. Record
missing proof, cause/ownership uncertainty, reusable mechanism, supported scope,
effects on other consumers, and how to make the next action clear at point of use.
Remedy plausibility and report counts do not establish correctness; one supported
counterexample can establish a shared defect.

Search open and closed orbyss-io/program-kit reports with the reporter's bounded
search helper. Inspect comments, versions, triggers and causal support; record
queries/incompleteness and links. Local assessment posts nothing. Propose request
to repair links or explained groups, preserving each observation's provenance.

Submit separate assessments into the same owner's intake queue. The owner alone
controls the existing shared ledger's scope, sequencing and explicit adopt,
duplicate, defer, reject or needs-proof dispositions. Never create a second
implementation-status ledger, rewrite approvals or close issues. The owner records
repair/reason, requests/issues, changed files, actual tests, dependencies and closure
proof. Keep implemented, validated, released and consumer-confirmed outcomes distinct.
Existing finding IDs such as U0 are valid. Record request-specific decisions under
the existing ledger's repairFeedback adapter; use only supported proof-bearing
lifecycle facts. The reporter reads that authority afresh and does not rewrite it.
Use existing versioned release/migration guidance for what/why and useful ledger,
issue, PR and accepted-evidence links. Incoming hypotheses do not alter confirmed
defect gates or authorize publication/paid workers.
