# Governed workflow resumption

Program Kit owns stage selection and invalidation; Spec Kit's workflow engine owns execution,
human gates, dispatch and the terminal outcome. Use the installed `scripts/workflow_lifecycle.py
run` or `resume --run-id <existing-id>` from the human-owned terminal. Agents derive run IDs
and all mechanical paths. Do not start an outer worker workflow inside an ordinary agent stage.

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
