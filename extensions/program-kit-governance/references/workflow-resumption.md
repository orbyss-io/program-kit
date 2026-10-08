# Governed workflow resumption

Program Kit owns stage selection and invalidation; Spec Kit's workflow engine owns execution,
human gates, dispatch and the terminal outcome. Use the installed `scripts/workflow_lifecycle.py
run` or `resume --run-id <existing-id>` from the human-owned terminal. Agents derive run IDs
and all mechanical paths. Do not start an outer worker workflow inside an ordinary agent stage.

Run, resume and reopen verify bare Python through the actual workflow shell mode
before worker policy, schema setup, execution locks or history changes. On Windows,
Program Kit automatically prepares the workflow PATH for cmd.exe: it removes duplicate
and missing directories, keeps the recorded Python first, and preserves all usable
tool directories, including Node for npm-installed coding-agent launchers. When needed,
existing Windows short directory names reduce length without changing directory identity.
The prepared PATH applies only to this invocation and its children; caller and persistent
settings remain unchanged. No manual PATH adjustment is needed for oversized paths that
can be represented safely. Useful directories are never truncated to fit the shell.

The probe binds the same recorded Python and scoped environment used by native steps
and requires its structured success marker and interpreter identity. A genuinely
unrepresentable usable PATH, missing runtime, or failed shell probe still stops before
dispatch or workflow-history changes. Saved state and approval gates need no manual edits.
For installed releases predating this preparation, use the source launcher in the
[current bootstrap instructions](https://github.com/orbyss-io/program-kit#windows-bootstrap-path-correction).

A failed producer or validator resumes from its affected producer stage. Successful prefix
stages remain recorded. The transition archives prior state, saved workflow and downstream
authority artifacts, invalidates downstream step results and completion eligibility, and clears
old verdict inputs before new review. Unaffected assessment/ratification approvals remain valid.
Non-interactive human gates pause; resume supplies only explicitly approved verdicts.

An already-approved readiness failure, including the recognized historical abort-only failure,
uses a linked native continuation workflow. Its source remains unchanged with its original
terminal status. This is continuation of accepted artifacts, not new intake. Proof and approvals
are preserved. Changed authority goes through correction and review; readiness, eligibility and
completion execute as native steps. Already recovered valid authority can be reused.
Semantic user rejection is never converted into technical recovery.

A completed bootstrap can explicitly enter bounded post-bootstrap maintenance from the
human-owned terminal:

```text
python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id <completed-source-id> --post-bootstrap
```

Plain resume of a completed run retains its existing meaning. This maintenance path is for
changed architecture authority. Ordinary feature-plan decision resolutions belong in
the selected plan and normal design review, consumed by phase-context and native eligibility;
they do not reopen bootstrap or rewrite its approved ledger. Retained compatibility and delivery
execution still require their actual evidence. For maintenance, the explicit flag verifies
the bound completed engine and intact approval, validates current ratification, and recovers
the historical constitution/readiness bytes by their exact completion hashes. It
preserves the source run, completion, approval and current artifacts in content-addressed
recovery storage before correction. Confirmed intake, assessment, ratification and existing
Accepted ADRs remain protected. Current architecture/roadmap evolution is proposed authority;
the review discloses every changed artifact against the previous approved bundle, including
changes predating preparation. It always requires fresh human approval, even with no changes.

A constitution amended and ratified after bootstrap is current authority. A regenerated
readiness report is current output, not approval. Neither needs to match the old completion's
file hashes. Preparation finds the historical bytes in current files, prior content-addressed
recovery archives, or local Git history at the same canonical paths; it checks the raw SHA-256
and archives them separately as `historical_completion`. Git lookup is read-only, uses no
network, and never checks out historical files. A caller-authored evidence JSON is not authority.
Missing historical bytes, an unratified current constitution, changed bootstrap approval or
invalid completed engine binding still blocks admission. The review packet identifies both
historical hashes and current constitution/ratification hashes. Current ratification is frozen
during this continuation; a later amendment uses its own governed review. Native readiness
and new engine-bound completion bind the current authority, while the old completion stays archived.

This path admits current passing architecture compatibility receipts into the existing ledger
and repairs authored roadmap sizing through review. Ready/Active/Delivered entries keep their
status; a before-implementation condition gates source work. The proof step validates the latest
attempt against the exact planned recipe, contract, runtime fixtures, selected design/pins,
toolkit, named executed tests and both streams. It never revives an older success after a
newer failed or incomplete attempt. Changed tooling or execution inputs require renewed native
proofs; historical receipts are retained. Accepted-input renewal is allowed only in the matching
running native continuation proof step, with unchanged decision/pin authority.

For preparation without worker dispatch, use
`bootstrap_recovery.py prepare --run-id <completed-source-id> --post-bootstrap`.
After maintained correction, synchronization and review have passed, the human-owned terminal
may combine `--post-bootstrap --reuse-prepared-recovery` on the initial resume to avoid repeating
correction authoring. Neither preparation nor reuse approves the review. Resume the linked
continuation normally at its actual human gate. A new approval explicitly supersedes the mutable
bundle and records the previous approval hash; it never edits the archived approval or completion.
New completion must bind the linked engine's own successful terminal outcome. Preserve existing
feature plans and code; this maintenance flow does not implement a feature.

When a maintainer has already prepared and validated the exact recovery review,
`resume --run-id <original-id> --reuse-prepared-recovery` creates the continuation
without repeating its correction-authoring agent. Admission verifies the preserved
authority, current review packet, architecture checks and every planned passing proof.
Stale preparation fails before dispatch; the flag cannot supply verdicts. Native proof
checks, synchronization, packet preparation, human approval, readiness and completion
still run. Use plain resume for subsequent continuation attempts.

Continuation readiness first generates a fresh compact stage brief and hash-bound
evidence index in the continuation run, using the original confirmed intake through
verified lineage. It supplies current ADR supersession, permitted source paths,
output budgets and the single structured validation command. Historical correction
handoffs are not readiness inputs. Published recovery directories inherit workspace
permissions; private temporary-directory ACLs must not be retained after publication.

The known 0.12.0/0.12.1 continuation readiness suffixes migrate to internal revision
0.13.0 and use the same deterministic readiness renderer as fresh bootstrap, after preserving
its failed state and workflow in resumption history. A failure whose sole blocker is
`READINESS-CURRENT-EVIDENCE` retries context generation and readiness after validating
the unchanged approved authority. It does not repeat closure, proof execution or
approval. Recorded unresolved questions or invalid authority retain correction/review
routing; an old report's independently authored status does not itself require
re-authoring valid accepted decisions. Changed
authority, unknown suffixes and invalid lineage stop before agent dispatch. The
original lineage definition remains historical; the child's saved migrated workflow
and final completion hash identify the actual executed suffix.

Corrective handoffs include current authored-byte targets and hard limits. The producer uses
`bootstrap_recovery.py inspect-output --run-id <source-run-id>` after its final writes, including
for older handoffs. Native sizing validation runs before provisioning/runtime proofs and counts
only verified canonical generated views separately. Malformed output reports
`RECOVERY_PRODUCER_OUTPUT` with paths, authored/generated/total bytes and hard limits.
Use the supported lifecycle resume for bounded correction; failed output and diagnostics are
archived before retry. Older saved definitions enforce the same guard at proof-helper entry
without changing their workflow snapshot. Protected authority failures retain governance diagnostics.
Sizing supplies no structural acceptance or approval; synchronization, semantic validators,
proof checks, the human review gate and engine completion remain authoritative.

Repeated resume follows the same linked run. An OS execution lock prevents concurrent
resumption and releases on process death. Interrupted state and invalidated step history stay
inspectable. Unknown saved structures require maintenance rather than guessed jumps.

Completion is valid only when its record binds the exact saved workflow and a native engine
run with terminal completed status and a successful final step. `workflow_lifecycle.py
validate-completion` checks project authority and engine outcome. A pending final-step record
cannot authorize feature work before the engine finishes. Historical independent completion
records remain artifact evidence but do not satisfy this engine-completion contract.

Report fresh and resumed completion separately, including source/continuation run IDs and
statuses. Mocked-dispatch deterministic tests prove mechanics; they do not prove paid real-agent
execution. Preserve that distinction in every report.
