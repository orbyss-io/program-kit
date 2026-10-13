# Program Kit 0.13.1 release handoff — stopped at the user's request

Release preparation is stopped. The user is obtaining another consumer diagnostic and wants a fresh session to fix that newly discovered bug before release work resumes. Its details have not been supplied to this session. Do not infer the bug or resume publication from this document.

## Checkout and publication state

- Primary checkout: `C:/Users/tech_/Code/program-kit`, branch `codex/program-kit-maintenance`.
- Latest pushed code candidate: `fcb1c84fe9344e35fc988228cfb1f120e8399877`, version 0.13.1. This handoff is a subsequent local documentation-only commit; it is deliberately not pushed because that would restart candidate CI during the requested stop.
- Draft PR: https://github.com/orbyss-io/program-kit/pull/40. It remains open and draft. Candidate CI run `38306473796` is completed/cancelled; the superseded `38305252750` is also cancelled. There is no green complete candidate CI acceptance.
- Remote `main` remains published 0.13.0 at `60e875799e1aa7ae408ca5b660fcd278d9f6abea`. No `v0.13.1` tag exists, nothing was merged, and this session published no release assets. Keep version 0.13.1 for the pending release.
- Tracked files are clean after the handoff commit. Pre-existing untracked `.agents/` skills remain intentionally untouched. Preserve existing stashes and consumer evidence; do not delete or hide these files to manufacture a clean Release checkout.
- Historical managed worktree `C:/Users/tech_/.codex/worktrees/release-0131/program-kit` is clean, inactive and still at **older** `b650fdbe9904d0996d65bf3b43844dbd1396587d`. It retains ignored diagnostic artifacts. Do not treat it as the current bug-fix checkout, delete its artifacts, or start another Release run there unchanged.

## Completed implementation and source context

The nine-step approved maintenance plan is saved in [the durable plan](program-kit-maintenance-plan-2026-10-12.md); [the execution record](program-kit-maintenance-execution-2026-10-12.md) contains all 14 observation dispositions and exact evidence. The earlier stale checkout was corrected and independently audited against published 0.13.0 in [the context audit](program-kit-maintenance-0130-context-audit.md). Do not restart from remote main and lose the maintenance repairs.

Maintenance implementation `2a90b90a168d5bde72bfd31edd1773de82a8dc8a` passed all 88 Development checks. Public Foundation 0.3.3 was qualified/promoted together with its exact publisher knowledge while preserving historical profiles and existing consumer locks. Its immutable Host passed both amd64/arm64 HIGH/CRITICAL vulnerability gates. Those records are maintenance evidence, not a successful Program Kit Release receipt. This session made no real consumer edits; the consumer's concurrent authorized adoption is documented separately.

Release preparation added consistent 0.13.1 metadata and migration guidance, retaining fresh 0.13.0 story/review/clock semantics. README installation/upgrade/verification examples still point to successfully published 0.13.0; the published-readme workflow advances them only after publication succeeds. The bundle limit remains 512 entries; only an unregistered updater working recipe was excluded, and registered historical qualification inputs remain shipped.

The first full Release run exposed three causes, all corrected before handoff:

1. `foundation_setup.py` now fingerprints and launches generic Python commands through the same validated shared device selection. An unreadable Windows alias is rejected by the original-source regression, and invalid selection launches no child. All 27 readiness tests pass.
2. `bootstrap_compatibility.py` rejects missing fixture bindings before authority lookup or scratch materialization. Valid contracts retain stale-authority checks. All eight actual compatibility checks pass.
3. Every README install/upgrade/verification example retains the available release. All 13 dependency-workflow tests and initializer validation pass.

These shipping corrections are in `b650fdbe9904d0996d65bf3b43844dbd1396587d`. The subsequent `fcb1c84` changes only test scaffolding and contributor documentation: disposable composition qualification chooses available application/identity public ports, preserving private transport and real authentication checks. An existing consumer legitimately owns 5000/8080; neither of its containers was stopped or modified. Occupied-listener contract checks and actual cold/prepared base qualification pass (`artifacts/tests/reusable-foundations/f73e395ed6cf4b96/qualification.json`). Remaining all-shape/full acceptance is not established by that targeted result.

## Preserved validation and verified stop

- First complete local Release: commit `0a90945842247564ab3fa8b1965e436a1df131bc`, 122 checks, 118 passed/four failed. All failures are diagnosed in the execution record. Preserved transcript/journal/streams: `artifacts/maintenance-2026-10-12/release-0131-first-run/`. Journal SHA256: `1e4d72c7f7f10c6b6bc70c7fc63d682db07ac4b6a3b6d4ef096e4b71a8a06258`.
- Second local Release: commit `b650fdbe9904d0996d65bf3b43844dbd1396587d`, journal `20261012T203607Z-4600b7e9`. At the user-requested stop, 96 checks had completed: 94 passed; disposable qualification failed on the already-owned port, and public availability failed on local registry credentials. `validate_dotnet_scaffold` was interrupted and has no completed result. Preserved transcript/journal/streams/native failure: `artifacts/maintenance-2026-10-12/release-0131-stopped-run/`. Journal SHA256: `99676390a722acb5afb444c43a35cb4f25232097ae9610159ab2369cb966b5cb`.
- Stop provenance: `artifacts/maintenance-2026-10-12/release-0131-user-stop.json`. Only the verified task-owned validation runner was terminated; its Windows kill-on-close Job ended supervised descendants. The surrounding PowerShell cleanup finished. Recorded task processes remaining: zero. CI cancellation is verified completed. Existing `rm01-ds01-entry` and `program-kit-identity-keycloak-1` continued unchanged.
- No successful `release-receipt-0.13.1.json` exists. Original journals/receipts were not rewritten. Interrupted, failed or cancelled checks are not passes, and prior evidence does not authorize a paid phase.

GitHub CLI login works for repository/PR/CI operations. Its observed OAuth token lacked package-read scope and the package endpoint returned HTTP 403. The user explicitly instructed **“Skip that check. CI will prove it too.”** Additional OAuth checks stopped; use CI for package-access acceptance. Retain local failures honestly; do not weaken the deterministic inventory or fabricate a local receipt. Tokens must remain out of logs/files and coding-worker environments. No Git credential-helper secret was extracted.

## Fresh-session order

1. Start in the primary candidate branch, read `AGENTS.md`, the plan/execution/context audit and this handoff, and obtain the actual new consumer diagnostic from the user.
2. Fix that bug with meaningful targeted coverage and the bounded Development suite. Keep actual consumer edits, interactive intake and paid live phases outside this release-maintenance scope unless separately authorized.
3. Keep the release stopped while fixing the bug. When the user explicitly resumes release work, freeze the corrected committed candidate. For a clean managed checkout, specify the **exact corrected ref**; the worktree tool's default remote-main baseline would discard these changes. Follow the local terminal/explicit-task opt-in rules in `AGENTS.md`.
4. Run/review the required local and latest-source CI validation, retain actual local credential failures under the user's CI instruction, and require all authoritative gates before publication. No old failed/interrupted journal can produce a successful new receipt. Non-shipping evidence reuse requires every condition in `AGENTS.md`; no successful local receipt exists here to reuse.
5. Obtain/confirm authority for the exact final commit and stable tag before merge/tag publication. The complete tagged Release workflow, including security, public component gates and its exact-source receipt, remains mandatory. Do not claim 0.13.1 is available until that workflow succeeds.

No future automation or background monitor was created. No release process remains running from this session.
