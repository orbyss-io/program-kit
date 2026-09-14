# Roadmap-to-closure evidence handoff repair

Consumer run `a103c7f2` in `program-kit-intake-nuafujsb` passed roadmap validation but failed
`prepare-closure-context`: architecture documentation was stale. The roadmap producer had correctly
made its permitted link-only edits in architecture.md and traceability.md. Their canonical map
hashes still described architecture-stage bytes. Closure validates that map before preparing its
brief, while the existing roadmap synchronization was scheduled only after compatibility execution.

This is a deterministic handoff defect, not a missing consumer answer. The earlier same-session
proxy concealed it through manual hash refreshes; that was not representative of normal execution.

The roadmap terminal batch now invokes the existing `synchronize-roadmap` helper immediately after
roadmap governance validation, then validates consistency and final synchronized output budgets.
It refreshes only the two owned document bindings and the generated DSL. Unrelated stale documents
still fail, and the helper rolls back partial synchronization on failure. The later post-proof sync
remains necessary because compatibility can change roadmap state. No workflow definition, approval
semantics, compatibility requirement or paid-agent dispatch path changed.

Regression coverage checks the batch ordering, post-sync size failures, repeated synchronization,
exact document/DSL binding and rejection/rollback for unrelated documentation drift. The original
test addition touched a shared fixture and caused a duplicate documentation ID in another suite;
the new negative case was isolated to its own test scenario instead.

The targeted context and governance tests passed, followed by the complete bounded Development
suite. Its preserved log is `artifacts/roadmap-handoff-development.log`. No Release suite was run.

The consumer received only the changed helper and roadmap command/installed skill clarification;
its previous installed copies matched the committed source. Failure state, prior documents, map,
DSL and installed files were preserved under `artifacts/roadmap-handoff-a103c7f2/before`.
Architecture and traceability repeated explanations were shortened to accommodate the actual
687-byte deterministic navigation section. Decisions, owned contracts and roadmap entries were
preserved. Line endings were normalized while retaining their text semantics.

The repaired consumer passed all six roadmap checks and the exact closure-context build that
previously failed. Final sizes: architecture 10,109 bytes, traceability 6,021 bytes, roadmap 6,130
bytes, each within its hard limit. Saved native state was verified byte-for-byte unchanged. No
coding agent, approval, compatibility probe or workflow resume was launched during this repair.

The user can resume from the same consumer root with:

```text
python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id a103c7f2
```

The engine retries closure-context preparation and continues to its closure producer. Earlier
roadmap/architecture work need not be redrafted. This fixes the demonstrated handoff and its adjacent
size failure; it does not claim that the remaining live workflow has already passed.
