# 0.12.2 handoff after concurrent-source validation failure

The user authorized publication and now wants the other agent's newly found
bootstrap-continuation fix included. They explicitly declined another local Release
run and asked this session to fix the validation issue, commit and hand off. Do not
ask them to repeat the same run. Publication has not occurred; no v0.12.2 tag was
pushed or release created by this session.

The permission fix is committed at `39ca114d838a0988e0ae3bdd5ec80afb0dcc706e`.
The Windows mixed-Python test-only correction is committed at
`a2476df0fe91d9d21215e0e7da416811c003fa21`. PR
[25](https://github.com/orbyss-io/program-kit/pull/25) contains these and the earlier
governance config / stale ADR fixes. CI run
[37048735131](https://github.com/orbyss-io/program-kit/actions/runs/37048735131)
passed Windows bootstrap and the complete Linux inventory, including Firefox.

The third human-owned local Release run executed all 87 checks successfully:
`artifacts/validation-runs/20261002T193102Z-0791b75b/journal.json`.
It began at commit `a2476df` / tree `ef785af37447cb929399139cda095db7208203a6`.
At receipt creation the working tree contained the other agent's unfinished
bootstrap-continuation changes, and `write_release_receipt.py` correctly rejected
the dirty source. The transcript is `artifacts/release-validation-0.12.2.log`.
This is not a failed product check and not a successful Release receipt. The
87 passes cannot establish that every check tested the same source revision or
validate the later combined candidate. Preserve the journal/transcript unchanged.
Do not invoke the receipt writer alone, rewrite historical hashes, or manufacture
a clean-source receipt from this run.

The first two human runs and their failures are preserved at
`artifacts/validation-runs/20261002T184442Z-643a0cee/` and
`artifacts/validation-runs/20261002T185846Z-50bb920d/`. The first selected unpinned
global runtimes and had one temporary-file sharing error. The second passed 86/87
checks but the local helper incorrectly passed an npm JavaScript entry point to
the native availability launcher (WinError 193). The corrected helper is now
tracked as `scripts/Invoke-LocalRelease.ps1`; it uses cached native npm.cmd and
Windows system certificate trust, a bounded PATH and environment restoration.
`-PrepareOnly` passed and starts no suite or coding agent. Catalog verification
passed in `artifacts/building-block-public-availability-system-ca.json`.

This handoff adds a source-integrity guard before and after each Release check.
It stops early with `PROGRAM_KIT_RELEASE_SOURCE_CHANGED`, names observed changes
and preserves the current journal without producing a receipt. Seven deterministic
runner regression tests pass, including an edit during a fixture check which
prevents the next check and receipt invocation. The existing receipt gate is intact.
The helper, runner checks and this documentation are contributor validation files,
outside shipped bundle inputs; the new continuation fix changes shipped inputs.

Finish and commit the other agent's changes separately, update PR 25 around the
combined scope and validate the combined candidate. Keep release source frozen or
develop in a separate checkout. Publication still requires the repository's valid
Release evidence and complete tagged Release workflow. The user's refusal to rerun
does not turn the dirty-source run into a receipt. Resolve the remaining evidence
requirement under their direction; this session has not bypassed it, started an
agent-owned Windows Release run or asked for another human run.

Other agent edits observed before this handoff were limited to bootstrap recovery,
continuation/lifecycle guidance and scripts, `bootstrap_context.py`,
`bootstrap_proof_plan.py`, `workflow_lifecycle.py`, its proof-plan test, the validation
inventory and new `tests/validate_post_bootstrap_continuation.py`. This session
did not stage, discard or alter those edits.
