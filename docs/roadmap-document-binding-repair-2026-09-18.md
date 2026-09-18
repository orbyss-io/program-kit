# Roadmap document binding repair

Run `e34d1796` stopped at `validate-roadmap-output`: the canonical architecture map
registered `docs/architecture/bootstrap-prerequisites.json`, but roadmap authoring
changed that allowed output. Its stored documentation hash was consequently stale.
The synchronizer refreshed only architecture.md and traceability.md before validating
the whole map. This is a Program Kit ownership mismatch, not a missing consumer answer.
The earlier source-reading improvement did not change this synchronizer; its tests
missed this registration variant. A previous lifecycle synchronization regression
covered the same class of issue at a later stage, but not the roadmap handoff.

Roadmap synchronization now refreshes registered bindings for the roadmap and ledger,
as well as its two navigation views. Existing `validate_roadmap` runs first, including
prerequisite shape, source inventory, authority, phase and proof checks. No manual hash
editing, broad documentation refresh, approval rewrite or relaxed gate is introduced.
Unrelated document drift still fails and derived updates roll back atomically.

## Evidence

An isolated copy of the failed consumer reproduced the exact original diagnostic.
Replacing only governance_state.py made the existing roadmap terminal validation batch
pass all eight checks. The subsequent closure context generated successfully. Drafted
consumer decisions and prerequisites were not rewritten to make validation pass.
Local before/after evidence is in `artifacts/roadmap-ledger-replay.json`.

Regression coverage registers both mutable outputs, validates successful rebinding and
repeatability, rejects a closed prerequisite without proof, and verifies unrelated
document drift causes failure without partial derived updates. Existing lifecycle
regressions pass. The bounded Development suite also passed.

A resumed native run normally restarts the roadmap producer for this failure position.
Repair the installed helper and run its terminal validation before resuming, so context
generation sees synchronized derived bindings. Do not edit workflow state or skip the
remaining closure, compatibility and human review steps. This repair does not claim
that the unexecuted remainder of the live run has passed.

The installed helper was then repaired in the original failed consumer. Its terminal
roadmap batch passed all eight checks. A before/after hash inventory verified that the
prerequisites, roadmap, decisions and existing approvals were byte-identical; only
architecture/traceability navigation and architecture-map bindings changed. The native
run state remains failed until the user resumes it; no coding agent was launched.
