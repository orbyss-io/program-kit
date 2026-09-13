# Phase 4 execution acceptance evidence

Date: 2026-09-13. Status: independent acceptance, the approved board-state amendment and the real
human portal exercise passed. All [Phase 4 decisions](../backlog-delivery-phase-4-decisions.md) were
accepted. This phase lands on `codex/backlog-delivery`; no version change, main-branch merge or
publication is authorized.

## Isolated native resources

The private `Unfussiness/ProgramKit.Delivery.Phase4` project is
`91611982-1c26-48b8-a9f7-c77c2f41f821`; delivery space
`160c923d-5ac4-4d88-be1a-6a2130168962` has coordinator repository
`69c9a727-e1c4-4441-9955-e027e28aa5f3`. The code repositories are API
`9f667150-b85a-4296-8509-f5e33f09b31b` and client
`25592c38-0750-4cd4-8c7d-552d47ec9aa1`. Work items are Epic 95, Feature 96,
API Requirement 97, client Requirement 98, receiving-integration Task 99 and human-exercise
Requirement 100. Existing Customer Service Pilot Epic 82 and its children remain outside this scope.

Pipeline 56 verifies the API; pipeline 55 verifies the receiving client and actual consumed API.
Required main-branch build policies are IDs 1 and 2. They are blocking, cover the whole branch,
expire when the target changes and queue only through explicit manual acceptance actions. Jobs
have ten-minute timeouts. The shared journal enforces the accepted limit of twelve runs; no capacity
purchase, production deployment, organization-wide process change or coding-agent session occurs.

## Observed coordination behavior

The two consumers have actual Azure Git histories, pinned profiles, installed extension runtimes,
accepted architecture/contract documents and separately verified repository activations. Two competing
processes claiming Requirement 97 produced exactly one success. Requirement 98 was then claimed by
a separate session of the same person. A parent-wide client claim blocked Task 99. Explicit takeover
advanced the API generation to 2 and rejected the previous receipt. A deliberately out-of-scope file
blocked its checkpoint. Both installed core implementation gates subsequently passed.

Native tags, planned starts, predecessor/successor links and readable work views were published.
The milestone has explicit membership, outcome, accountable owner and forecast dates; no committed
deadline was invented. Its readable view distinguishes implementation, delivery and acceptance.
Views preserve human descriptions/comments and unrelated tags. Exact projection intents and raw
before/after histories remain in the coordinator and local evidence.

Observed Azure behavior required narrowly scoped projection handling: a new work-item revision
expires the previous terminal revision's audit timestamp, even when mirrored-link updates follow
that revision; a first tag assignment can backfill an empty tag in revision one. Tests reject
nonempty historical tag changes and unrelated audit timestamp changes. Recovery resumes the exact
intent rather than replaying its native PATCH. Intervening human edits require reconciliation; an
obsolete dispatched operation can be abandoned only after a newer accepted revision fences it.

## CI authority and initial runs

Initial synthetic runs 1385 and 1386 succeeded. Run 1386 verified the actual project-scoped job
identity `76c747b8-6399-4024-8156-c934718257e6`. The coordinator grants that identity read access
and explicitly denies contribution, force push, branch/tag creation and protection changes.
The initial checker is pinned at tooling commit `e2399d7fd0c036f26fad682c574a11a966a79464`;
it is a separate immutable producer input, not a delivery-subject revision.

[API PR 9](https://dev.azure.com/Unfussiness/ProgramKit.Delivery.Phase4/_git/phase4-api/pullrequest/9)
passed required build 1387.
[Client PR 10](https://dev.azure.com/Unfussiness/ProgramKit.Delivery.Phase4/_git/phase4-client/pullrequest/10)
passed required build 1388. Each actual job verified current work history, execution scope, claim
generation and configured branch policy. The job's own permission checks returned read=true and
contribute/force-push/manage-permissions/edit-policies=false at both repository and coordination
branch. Both emitted `completionRecorded: false`. Passing CI did not grant business authority.

Both initial PRs integrated with required policies and released only their implementation claims.
Integrated API run 1389 passed. Client run 1390 correctly withheld evidence after exposing a checker
defect: it assessed the already released parent as a proposed live claim while its receiving Task
was active. The repair checks conflicts only for live claims, while still verifying released
implementation proof. A regression reproduces the exact parent/Task combination.

The receiving claim was explicitly withdrawn. A complete business/coordinator/technical migration
then pinned corrected checker `164699f7a94c71af43a178ca0db27d53efec3aac` and profile digest
`502c675d899699e4e0ab66fed55a6e63f7460ad80c493588cb5c351cb6ae12d5`. Both consumers preserve their
old profile and history and use the new immutable snapshot through their binding. CI's `--binding`
mode verifies this current snapshot and provider registration. Fresh `phase4/verified` test targets
were seeded from the integrated contributions and protected by policies 3 and 4 before claims
resumed. Existing main policies were not changed. New baseline reviews and execution plans preserve
the prior decisions in history.

Repair PRs 11 (API) and 12 (client) passed required policy builds 1391 and 1392 and integrated
without bypassing policy. The integrated API commit is
`39a50a5f19c2182f478b5468799a229e3fbce785`; the integrated client commit is
`4866e9ff92db1dc7c32149a0e87731feb717de95`. Their claims released implementation without recording
delivery. The receiving Task refreshed its approved base, acquired generation 2 and started; client
delivery was explicitly rejected while its required receiving evidence was absent.

Integrated builds 1393 (API) and 1394 (client) both succeeded. Actual client CI verified the released
parent at generation 2 together with its active receiving Task at generation 2. Both jobs verified
read-only coordinator permissions and emitted `completionRecorded: false`. The shared journal
records ten of the twelve authorized runs, including the preserved failed run 1390. Implementation,
delivery and acceptance were separately recorded for the API, receiving Task and client. The shared
pilot milestone received its own explicit synthetic outcome decision against current member evidence.
All three final work views and the milestone view were published. The final milestone snapshot has
no blockers and `outcomeAccepted: true`. The real human portal exercise remains before phase completion.

The verified receiving artifact is native artifact 849 from build 1394. Its manifest identifies
both integrated commits above and successful `origin-routing` and `receiving-integration` checks.
The downloaded content digest is
`485d7faa82ab9825378c46ff70db147442ef5bbe74ea41c43a51fd2639efdc8a`; the manifest digest is
`07b088c697ce44205faba2f5e41500775aa92e4e90b110e2088700da1a2ec487`. Actual payload hashes were
verified before recording evidence for the client and its receiving Task.

A fresh process using the client's installed extension passed explicit `SPC-001` delivery and
acceptance admission while its local receipt still identified `P4-INTEGRATION`. Both selected
`P4-CLIENT` and returned `completionRecorded: false`; checking admission did not create another
completion decision. The native results are preserved in `installed-completion.json`.

Observed performance limitation: native progression and verified view publication repeat provider
history, integration and artifact reads. The sequential acceptance driver takes minutes after CI
finishes. This run establishes functional guarantees, not a latency or scale target. Any read
deduplication or caching must preserve freshness at approval and commit boundaries; validation at
larger delivery-space sizes remains follow-up work.

## Native board-state completion amendment

The approved per-type policy is `724495d0-13e7-4753-986f-810b6bd599a2`. It binds the existing
delivery profile and actual Stories/Features/Epics board mappings. Tasks use New/Active/Closed;
their implementation cannot be mapped to Completed prematurely. The extension exposes mapping
review, synchronization, resumable publication and explicit parent-outcome commands.

The real implementation checkpoint queued the native updates atomically with its activity record.
Requirement 100 and its Epic/Feature parents became Active. Previously verified API/client/Task
progression was then projected without changing the consumer Git inputs, execution approvals,
pipeline definitions or existing evidence. No additional pipeline run was queued.

At coordinator commit `7fd436e2ec795d9d845568f7e3b1b6d3bc5fa2a7`, observed native states are:

| Item | Native lifecycle | Native board column |
|---|---|---|
| Epic 95 | Active | Active |
| Feature 96 | Active | Active |
| API User Story 97 | Closed | Closed |
| Client User Story 98 | Closed | Closed |
| Receiving Task 99 | Closed | Task workflow; no Stories column |
| Human-test User Story 100 | Active | Active |

There are no pending board operations. Requirement 100 retains its active generation-1 claim,
original actual-start timestamp, uncommitted file and absent implementation/delivery/acceptance.
Parent completion was not inferred from child completion; deterministic coverage proves that an
explicit parent outcome can close a Feature only after its scoped Requirements have current
acceptance, while the enclosing Epic remains Active without its own outcome decision.

Native inspection exposed Azure's initial board-field materialization. Only the observed workflow
service identity, previously absent configured board fields, unchanged lifecycle and unchanged
human fields/comments are accepted by the explicit initialization observer. Raw before/after
snapshots and original business review identities are preserved. Actual state writes separately
validate the actor, conditional revision, known workflow audit effects and board columns. Human
state/tag/text/comment changes remain reviewable conflicts.

Validation: the bounded Development suite passed with 45 execution cases, including seven board
regressions. Two additional targeted cases passed for the subsequently observed initialization and
hidden audit-field behavior. Current execution coverage totals 47 cases. The local package build
and targeted packaged-install check passed with the new board runtime and default mapping. Earlier
test-fixture and schema-selection failures are preserved alongside their fixes. Pipeline runs remain
10 of 12. The original pipeline checker pin was not replaced by this board-only change; native board
acceptance and deterministic/installed checks establish the new behavior, rather than attributing
it to the earlier pipeline runs.

Evidence is under `artifacts/delivery-phase4/board-states/`, including the exact mapping proposal,
initialization observations, native before/after histories and `final-state.json`. Board-specific
logs, `development-board.log`, `board-native-history-tests.log`, `package-build-board.log` and
`package-install-board.log` preserve validation outcomes. The repeatable native driver is
`scripts/delivery_phase4/board_states.py`.

## Completed real human acceptance

The user personally edited
[Requirement 100](https://dev.azure.com/Unfussiness/ProgramKit.Delivery.Phase4/_workitems/edit/100)
at `2026-09-13T16:28:02.97Z`, creating revision 5: State **Closed**, board column **Closed**, and
ordinary tag **Human portal check**. Native history identifies Joey Barten
(`1905259c-b49e-6ebc-8210-ad4f56b44823`). The user confirmed completion; this action was not simulated.
The amended Active baseline is `board-states/human-before.json`; the earlier New baseline under
`finish-repair/` remains historical evidence.

Sync report `3d358427-0566-442a-a3cc-5c94aef5a3bc` discovered exactly the changed item. Five negative
checks rejected board synchronization, the implementation checkpoint and implementation/delivery/
acceptance completion proposals because the native history was unreviewed. The original active
generation-1 claim, actual start, plan and absent completion records remained unchanged. Azure's
automatic Reason of "Acceptance tests pass" also granted no technical or business acceptance.

The exercise exposed a recovery defect: every history review previously replaced the execution
basis, even when an explicit feedback decision required no technical revision. The correction
records the new history review separately from the retained business basis. Only reviewed cosmetic
or feedback decisions explicitly requiring no revision retain that basis. Material decisions still
advance it; later cosmetic reviews cannot clear pending revisions or restore an older basis, and
concurrent reviews cannot supersede a newer accepted decision.

Review `66db0299-8ec3-455b-ba51-ac86038b76c7` records the approved synthetic false-closure correction:
no requirement, architecture, assignment, dependency, text or comment change; preserve the ordinary
tag and restore the verified activity. Conditional board publication produced revision **6, Active**.
The original claim and complete progress record compare equal to the baseline, including actual
start `2026-09-13T15:09:36.512227+00:00`. The unfinished `portal-exercise.md` remains uncommitted.
At coordinator commit `682cefeb76fc06fa2f46bfd8766eb8a6dc8df9fc`, the readable view is refreshed and
there are no pending board operations. Epics/Features remain Active; accepted items 97–99 remain Closed.

Preserved evidence: `human-after-observed.json`, `human-sync.json`, `human-negative-gates.json`,
`human-review.json`, `human-board-correction.json`, `human-recovered.json` and `human-complete.json`
under `board-states/`. The guarded driver is `scripts/delivery_phase4/human_board_acceptance.py`.
This completes the real human acceptance requirement for Phase 4 without treating the deliberately
unfinished test item as delivered.

A fresh installed-consumer check (`board-states/installed-human-final.json`) admitted continued
implementation at generation 1 with exactly the uncommitted `portal-exercise.md` footprint. Explicit
`SPC-002` delivery and acceptance both failed because no integrated implementation exists.

Final recovery review also found that board projection could prevent an explicit pause/withdrawal
when native history or the execution basis was stale. Claim control now records the stop and an
attributable deferred-board reason without writing over human changes; readiness exposes that
deferred publication. Reviewed synchronization clears it. An already-dispatched native operation
still requires its recorded recovery path first. The targeted stop/reconciliation regression passed;
this additional failure case was exercised deterministically, without changing the real human test's
retained claim or consuming another native pipeline run.

The final local delivery archive has SHA-256
`e6a5e38f285a75b4abca465b5ad55eb97742fa2fef0379d8e750bfabc4e454bc`.
All 40 archive entries match the final extension source bytes, recorded in
`board-states/phase4-final-package-source-check.json`. The local build and packaged-install check
passed (`package-build-phase4-final.log`, `package-install-phase4-final.log`); no package was published.

The final bounded Development suite passed in `development-phase4-final.log`, including all **48
execution** and **23 reconciliation** regressions. The complete real human recovery, retained
business basis, substantive-change invalidation, concurrent-review rejection and explicit stopping
cases are covered. `git diff --check` passed. Synthetic consumer Git status remains only the
deliberate uncommitted API test file; the client is clean. The shared native run budget remains
10 of 12. The deferred Spec Kit/module integration is recorded as Phase 7, with implementation
postponed until the current capabilities are developed and tested through Phase 6.

## Validation and preserved evidence

Existing targeted validators passed: 36 Azure planning tests, 21 reconciliation tests and 25 offline
delivery tests. The bounded Development suite passed, including 36 execution/evidence regressions.
Local package build and targeted packaged installation passed, including the execution command and
runtime. After the CI repair, the Development suite and packaged installation passed again with
38 execution regressions. These include explicit completion selection after another Task occupied
the checkout, bounded outage/reconnect behavior, migrated-binding identity and the released-parent
receiving-task combination. The preserved successful initial build 1385 was also rejected against
current targets using its original producer configuration; this negative read changed no active
policy and recorded no evidence.

Evidence is preserved under `artifacts/delivery-phase4/`: setup and mutation journals, complete
proposals, native observations, pipeline timelines, exact artifact verification, projection recovery,
installed-gate outputs and validation logs. Reproducible synthetic drivers are in
`scripts/delivery_phase4/`. Local consumers are under `C:/Code/Orbyss/_ProgramKit/artifacts/p4`.
No complete Release suite has been requested; publication remains a separate user decision.

Provider references: [policy evaluation identity](https://learn.microsoft.com/en-us/rest/api/azure/devops/policy/evaluations/list?view=azure-devops-rest-7.1),
[explicit policy build queueing](https://learn.microsoft.com/en-us/rest/api/azure/devops/policy/evaluations/requeue-policy-evaluation?view=azure-devops-rest-7.1),
[actual caller permissions](https://learn.microsoft.com/en-us/rest/api/azure/devops/security/permissions/has-permissions?view=azure-devops-rest-7.1),
and [Git ancestry](https://learn.microsoft.com/en-us/rest/api/azure/devops/git/diffs/get?view=azure-devops-rest-7.1).
