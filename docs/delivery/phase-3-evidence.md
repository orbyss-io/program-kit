# Phase 3 reconciliation evidence

Date: 2026-09-13. Status: Phase 3 complete. Implementation, independent acceptance and the real
human portal edit/reconciliation journey passed. The user approved the exact impact review;
application preserved native content and left the required technical revision pending.
The two interview rounds in [Phase 3 decisions](../backlog-delivery-phase-3-decisions.md) were
explicitly accepted. Work remains on `codex/backlog-delivery`, following Phase 2 commit
`a4590fdf535a8f5f27f2e3a1fe8f959984b8de1a`. No version change or publication is authorized.

## Implemented behavior

Complete item/update/comment observations are distinct from reviewed classifications and accepted
business/technical bases. Edited, reverted and deleted comments remain visible in their history.
Role decisions bind an exact report; fresh reads reject intervening changes. Unknown coverage
cannot become readiness. Impact can be narrowed with an explanation, leaving unrelated siblings
eligible. Technical obligations accumulate until a separately reviewed revision verifies actual
Git commit, path and current file bytes.

Planning now captures native history, including updates that share a revision. Unfinished legacy
proposals need a new history-aware proposal before further dispatch. Reviewed uncertain-write
recovery retains human edits and original dispatch evidence; remaining work needs a fresh plan.
Shared-profile migration and disconnection use role approvals, provider registration and resumable
local history handoffs. The installed core admits local governance only after a verified completed
disconnect. The [installed reference](../../extensions/program-kit-delivery/references/azure-reconciliation.md)
documents commands, contracts and limitations.

## Independent checks

Evidence is preserved under the development worktree's ignored `artifacts/delivery-phase3/`.
These tests start no coding-agent sessions. Native test actions are confined to the approved
private `Unfussiness/ProgramKit.Delivery.Phase2` project; synthetic items use a separate delivery
space and coordinator. Epic 82's native content has not been changed by the tests.

- Reconciliation tests cover history pagination, comment versions, observation versus approval,
  mixed roles, scoped impact, stale proposals, incomplete observations, reviewed recovery,
  technical Git evidence, migration and interrupted disconnect. Final count: 21.
- Existing Azure adapter tests: 36; offline delivery tests: 25. Final bounded Development and
  targeted governance validation passed; results are preserved in `development-verified.log` and
  `governance-state.log`.
- Local package build and installed component/bundle validation passed, including the new
  reconciliation command, runtime, schema and reference. Logs: `package-build.log` and
  `package-install.log`. This is package validation, not publication or a complete Release run.
- Review caught an offset-pagination defect before completion: a provider-capped page must advance
  by the returned row count. The regression now serves multiple one-row pages despite a larger
  requested size. Missing named coverage streams also cannot claim completeness.

Native probes use Python 3.12 because this host's Spec Kit Python 3.13 encounters the known
`OPENSSL_Applink` TLS failure. Deterministic Development/package validators use the installed Spec
Kit runtime. Production TLS validation is unchanged.

## Native provider acceptance

Isolated space: `b78fae06-e671-41c6-ba14-0ad6cd923074`; coordinator repository
`phase3-coordination-ce86695d` / `c380d13f-d798-483e-bffc-a33764f19a5c`, branch `coordination`.
Synthetic Epic 88, Feature 89 and Requirements 90/91 were created through reviewed planning.
Editing then reverting Requirement 90's description was still detected; its sibling remained
eligible. Business approval retained an explicit technical revision obligation.
Evidence: `live-initial/results.json` and `live-resumed.log`.

The initial protection check stopped before graph creation while native branch permissions were
still propagating. The original setup was reused only after a read confirmed effective protection;
the guard was not bypassed. Preserve `live-initial.log` and `protection-observed.log`.

Extended acceptance preserved edited/deleted versions of synthetic comment `34483117`, verified
technical revision against a real Git artifact, and migrated two actual registered consumer
repositories together:

- `phase3-consumer-ce86695d-a`: `a5afb9a4-1243-4346-adef-0e87c544d7a6`.
- `phase3-consumer-ce86695d-b`: `d00349f1-22a5-4d96-88e6-e99627accda1`.

Migration `c40f47da-c975-41df-baa7-964424d7b4df` retained prior policy/history and required an
explicit new baseline. Disconnect `e5751d4e-ad53-4765-9bcb-984caa8f2d6d` accounted for the second
consumer's obligation, then survived an injected failure between binding and history writes.
Resuming the same transition completed it; repeating did not append another history event.
Installed consumer A returned platform refinement admission with no pending technical revisions;
consumer B returned verified disconnected local governance. Evidence: `live-extended/results.json`,
its journal, proposals and `live-extended.log`.

Reviewed recovery used synthetic Epic 92. Its current description was independently edited and its
creation marker removed after an injected response loss. Initial native history positively proved
identity. Review `c577d734-bc8d-4a0f-931b-5f4a0a67b5ff` retained the changed text, superseded the old
remaining proposal, and created no duplicate. Fresh proposal `4cfd8ebd-4a46-4117-b914-855b1a2c4b76`
completed the remaining Feature. A provider read failed during fresh approval; the run resumed
from its saved proposal, preserving the original failure log. Disposable Epic 94 was soft-deleted
and positive recycle-bin evidence supported explicit retirement. Final unresolved operations: zero.
Evidence: `live-recovery/results.json`, saved proposals, `live-recovery.log` and
`live-recovery-resumed.log`. These artifacts preserve source hashes at execution time; later
pagination hardening is covered separately by final deterministic checks and the human baseline read.

## Completed human portal acceptance

The product captured Epic 82 and children 83–87 without changing them. Report
`82e16518-05d5-4148-8bf5-daa0ba2ac371`, digest
`e2bdfe6b41fcd89362755e49a105965e47ccd8a787087cb62889129e2b21a69c`, is preserved in
`human-82-before.json` and its rendered report. All six observations have complete coverage and
no comments. At that observation Epic 82 was revision 2 with the original user description; child revisions were 1.
This is an observation, not an implicit new approval of unseen history.

The user personally appended the requested customer/partner-origin scope and added the unknown
destination triage question in [Epic 82](https://dev.azure.com/Unfussiness/ProgramKit.Delivery.Phase2/_workitems/edit/82),
then confirmed completion. Product sync captured report `8ed31e6c-1173-40b5-b26c-abc86305846b`.
Epic 82 advanced from revision 2 to 4; human comment `34483156` is version 1, attributed to the
verified user identity. All six observations have complete history/comment coverage; the five
children exactly match the saved before snapshots. No native field/comment was written by sync.
Evidence: `human-82-after.json`, `human-82-comparison.json` and their logs.

The prepared `human-82-review.json` classifies the Epic change as business scope with technical
revision required for the six-item pilot branch. Child snapshots are initial unchanged baselines:
the adapter had no previously accepted Phase 3 history basis for this Phase 2 graph. The proposal
explicitly distinguishes these initial observations from the new Epic impact, and does not claim
that the old baseline was retroactively approved before the edit. Requirement 85 already retains
unmatched/ambiguous requests for review; the concrete human triage owner and handoff remain open.
Intake, origin persistence and integration-test coverage need refinement. A fresh history check
passed when preparing the proposal. The user then explicitly approved the presented impact review.

Review `c7577e29-9b32-404d-976b-208bef0bcd8a`, digest
`3f4a80ab36c77a7ebe0281cfcdc0cb73ab8e229b1c4469427e7a892dd7fc7f48`, was applied with both
business and technical approvals attributed to the verified user. Final verification compared
complete native snapshots for all six items against the post-edit observation: every snapshot,
including the user's exact description and comment, was preserved. All six logical work items
retain this review as a pending technical revision; no technical completion evidence was created.
There are zero unresolved operations. Repeating the apply left coordinator commit
`df2faafd29c43caa8bb1e795cc4287fd9bee7728` unchanged. Evidence: the business/technical approval
logs, `human-82-review-applied.log`, and `human-82-verification.json`/`.log`.

This completes Phase 3 product acceptance. The Customer Service Pilot itself still needs its
recorded refinement; the test did not implement it or manufacture architecture evidence. Commit
and push the completed phase on the existing integration branch, then conduct the Phase 4 interview.

## Bounded limitations

Full history reads favor complete evidence over large-backlog performance; scopes bound work and
pagination has a finite limit. No background monitoring is installed. Technical artifact checks
require the relevant local repositories; unavailable remote artifacts block explicitly. Migration
keeps organization, project and coordinator fixed and needs all active consumer checkouts.
Disconnection conservatively requires all uncertain space operations resolved and no active claims;
future claims need their later supported handoff contract. Verified disconnect still needs provider
read access. These constraints are explicit and are not silent local fallbacks. Tags, dependencies,
execution claims, dates and delivery/acceptance gates remain Phase 4 work.

Primary API evidence is linked in the accepted [decision record](../backlog-delivery-phase-3-decisions.md):
Azure update IDs and comment versions are separate from work-item revision numbers, comment
pagination uses its response-body token, and deletion requires positive recycle-bin provenance.
