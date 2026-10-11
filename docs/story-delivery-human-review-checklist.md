# Story delivery and human review implementation

Accepted requirements: [plan](story-delivery-and-human-review-plan-2026-10-11.md).

- [x] Published baseline: v0.12.11, `99f2f6f8639588f4966f99515ebc9b1165f49ff0`; [complete Release](https://github.com/orbyss-io/program-kit/actions/runs/38128815951), tagged checkout, full deterministic inventory, attestation, public publication and install/upgrade all succeeded. Public archives/receipt/checksums uploaded 2026-10-11. Implementation starts at `834a9f2478fb270e883532d62c56c4ad5444567d`, with only publication README/checklist changes since tag.
- [x] Dedicated `codex/story-delivery-human-review` branch/worktree; primary changes retained.
- [x] Align constitution, specification, planning, tasks, analysis, implementation and projected/installed guidance.
- [x] Extend compact tasks checkpoint: story decisions, roles, freshness, progression/resume/closure/handoff and active clocks.
- [x] Validate optional GitHub identity and explicitly supplied scoped decisions using authenticated reads; deterministic simulations only.
- [x] Fresh-feature adoption guidance and one reset exercise in the existing installed-consumer fixture.
- [x] Targeted checks, review/repairs and bounded Development qualification; record actual results.

Verification: source/template changes use coherent edits and maintained resolution checks. Authority/state changes receive focused behavioral and negative controls, including deterministic clocks and authenticated-response shapes. No dependency, publisher, real-consumer or live-worker changes are planned. Release dependency maintenance, fresh local Release evidence, CI and complete tagged/public qualification remain future publication gates.

Implementation review: state/reset support is consolidated into `task_draft.py` and the existing
`phase-evidence.md` reference, retaining the 512-entry packaging limit and one canonical tasks state.
No new library/package pins; optional authenticated `gh api` access is recorded in maintenance policy.
Source registration covers every new canonical section and the story rule. Normal engineering runs
remain independent. Simulated fixture reviewers establish no actual human acceptance or speed claim.

Requirement results:

| Accepted requirement | Implemented result |
|---|---|
| Small runnable stories | Spec/plan sizing, actor intent/non-goals/walkthrough/effects; validated Story delivery map and exact operation/task dependencies. Larger stories disclose effort/rationale. |
| Per-story review/default pause | Separate engineering/human states; ordinary operations progress; completed stories/agreed early gates pause, with scoped repair/diagnosis and explicit acceptance/deferral. |
| Scaffold-first/balanced checks | Canonical and projected risk-selected sequence; maintained scaffold checks precede dependent behavior, missing consumer tests remain mandatory. No universal TDD or duplicate publisher suite. |
| Persistent roles/provenance/freshness | Compact checkpoint replacement retains all reviews, original baseline, failures, assignments/decision sources; scoped material changes reopen affected story/early reviews, unrelated commits/tests preserve acceptance. |
| Optional GitHub | Verified stable ID/host/login and confirmed assignment; exact supplied authenticated decision scope includes user meaning and implementation basis. Wrong/unavailable/ambiguous responses stay pending; no posting/polling. |
| Advisory time/resume | 60/120 active-minute defaults; elapsed accumulation, wait/suspend/resume, repairs, once-only warnings and explicit owner budget revisions. Time alone never blocks. |
| Maintained progression/closure | Start/preflight/progress/finish/formal handoff consume the same state; no-hook paths use these validators. Deferred reviews remain due before acceptance; engineering checks cannot manufacture human decisions. |
| Fresh-feature adoption | Owned file inventory preview/explicit selection/archive; constitution amendment and normal ratification; old partial work cannot authorize continuation; all fresh phase contracts consume installed policy. Bootstrap/shared/delivered/lock inputs preserved. |
| Concise qualification | 22 focused story controls, existing task/normal-development validators and one reset exercise in the existing packaged consumer. Existing installation, source protection and activation/recovery checks retained. |

Qualification source: `18835fb3cd25ab4a38acb4ac7e06ed25dc034f84`, clean and frozen during both final runs.
`./scripts/Test-ProgramKit.ps1 -Suite Development -BrowserEngines 'chromium,webkit'`
passed **88/88 checks** on 2026-10-11, 11:10:38–11:22:14 UTC. Evidence:
[Development journal](../artifacts/validation-runs/20261011T111038Z-40586ae3/journal.json).
This includes story controls 22/22, task generation 19/19, normal development 24/24,
intake 15/15, knowledge inventory 7/7, dependency audit 10/10 and phase readiness 18/18.
The final targeted `validate_consumer_upgrade_install` run passed with all five prerequisites:
[package journal](../artifacts/validation-runs/20261011T111308Z-b69580a4/journal.json),
[installed reset/recovery log](../artifacts/validation-runs/20261011T111308Z-b69580a4/validate_consumer_upgrade_install.log),
[consumer summary](../artifacts/consumer-upgrade-install.json). Both journals' exit codes and every log hash
were verified: zero errors. The bundle contains 512 entries; local development archive SHA256 is
`c90a73fcdfb770c399d4cc4bd8a884cb1eb5edb0e80f5d82bd490f3666d2b3a9`
([retained development archive](../artifacts/program-kit-0.12.11.zip)). Archives retain the predecessor build label 0.12.11 only for local
development qualification; they are not its published assets or a newly published version.
The first Development journal `artifacts/validation-runs/20261011T105444Z-e1589ca1/journal.json`
is retained as failed: concurrent shipped-source edits tripped exact updater freshness; new rule
ordering/registrations and fresh-state fixtures exposed four repairable validator failures.
All identified repairs passed the final frozen-source Development run. Only this non-shipped checklist
is updated after qualification; shipped payload/build inputs remain at the qualified implementation commit.
The primary checkout's unrelated skill files and uncommitted handoff documents remain untouched.

Adoption after publication: archive the unfinished attempt; update via the normal installer;
amend/review/ratify the constitution; review/select its exclusively owned reset inventory;
abandon old spec/plan/tasks/code/tests as active progress; rerun specify, clarification, plan,
tasks, analysis and implement. Reuse unchanged confirmed intent/bootstrap, architecture,
foundations/tooling, locks and delivered features. Real resets need their own consumer-session authority.

Release preparation: the user authorized publication as **0.13.0** on 2026-10-11.

- [x] Register version, initializer/catalog pins, versioned adoption guide and structured consumer change.
- [x] Retain every indexed guide and its checksums within the 512-file bundle limit: omit only duplicate
  aggregate summaries from the composite bundle; governance/public assets retain them. Bundle: 511 entries.
- [x] Release guidance: 8/8; shared-device Release preparation passed; native locks remain unchanged.
- [x] Bounded maintenance Development: 88/88 on clean `3a1e817b5680b3a45141fb713d720b26a7516e1e`,
  11:48:34–12:00:14 UTC; [journal](../artifacts/validation-runs/20261011T114834Z-61c1e810/journal.json).
  Every exit code/log hash verified. This is Development evidence, not a Release receipt.
- [x] Complete repaired dependency maintenance and candidate CI, then freeze the candidate.
- [x] Obtain fresh successful local Release evidence under explicit Codex-task authorization;
  inspect the complete journal, receipt, asset sizes and hashes.
- [x] Merge/tag and complete tagged Release, public installation/upgrade and publication verification.

Failed [candidate CI](https://github.com/orbyss-io/program-kit/actions/runs/38136895716) and
[maintenance](https://github.com/orbyss-io/program-kit/actions/runs/38136883783) evidence is preserved.
CI passed 119/121 checks, including installed reset/recovery, packaging and all three browser engines.
Two test-only repairs retain the same rejection/preservation controls: avoid shadowing the updater
command with the implementation-entry probe, and normalize terminal whitespace before checking the
unsafe-order diagnostic. Pin/profile/knowledge lookup succeeded; those failures prevented security scanning
and completion. No release tag or assets were published from either failed preparation run.
Both repaired targeted upgrade checks passed with their maintained prerequisites:
[local upgrade, 5/5](../artifacts/validation-runs/20261011T121424Z-7db4453a/journal.json) and
[candidate upgrade, 6/6](../artifacts/validation-runs/20261011T121453Z-915c8db6/journal.json).
Maintenance discovered CShells 0.0.30; normal publisher-engineering synchronization then retained
the selected published Foundation's exact preview ABI pins. Profile and versioned knowledge are
already current, so the maintained updater creates no duplicate qualification or lasting pin/lock diff.
Publication completed: [v0.13.0](https://github.com/orbyss-io/program-kit/releases/tag/v0.13.0),
source `ebe04405d3f6a85af90ca60fc223084d1df605c2`, tree `beeff319a524cdbd60237b85912a602cdcebe32e`.

- [Maintenance](https://github.com/orbyss-io/program-kit/actions/runs/38138778648) and
  [candidate CI](https://github.com/orbyss-io/program-kit/actions/runs/38138781071): **121/121 Linux checks**
  each; every preserved log hash verified. Windows CI passed. Actual Host AMD64/ARM64 scans passed.
- Fresh local Release: **122/122 Windows checks**, 12:52:18–13:38:55 UTC. The user explicitly authorized
  `Invoke-LocalRelease.ps1 -AuthorizedCodexTask`; the journal records it. Preserved under
  `C:\Users\tech_\Code\program-kit\artifacts\r13\artifacts\validation-runs\20261011T125218Z-7b3508a8`.
  All logs, 32 assets and receipt fields verified; local receipt SHA256
  `3f50919cf2a15d809bb5f670cf2a02c7cba2a1e9874788ea239c325a0a413a4f`.
- The first local run is retained as failed: **121/122**, journal `20261011T122225Z-07eb9609` in the
  original implementation checkout. Its sole failure was a 264-character Chromium executable path:
  normal Node launch returned ENOENT; extended-path launch succeeded. An identical clean short checkout
  reduces that path to 240 characters; complete composition and Release qualification then passed.
  Product code and browser coverage were unchanged. The failed run created no receipt.
- [Complete tagged Release](https://github.com/orbyss-io/program-kit/actions/runs/38144160052):
  **121/121 Linux checks**, Chromium/Firefox/WebKit, exact-source receipt, attestation, publication and
  public installation/upgrade all passed. Published at 13:58:49 UTC. All public receipt/asset checksums
  verified and the bundle's signed GitHub attestation verified. Public bundle SHA256
  `6fa44e894007109fc700586aa7e5285e8a5da295ad0aa967f739691815d06dd1`;
  [public receipt](https://github.com/orbyss-io/program-kit/releases/download/v0.13.0/release-receipt-0.13.0.json)
  SHA256 `b2ab7bc725265b5fbb18d812ef4eac650dfba7c5b87940d1fd3ac6982dda5710`.
- PR #39 merged at `9e3c94272804bf7089cfbdd32ae27f706649262a`, with the same source tree. Merged-main CI
  and the publication-owned README update passed. The tag remains at the exact qualified commit.

No publication gates remain. Published assets and original receipts remain unchanged; this reporting
update does not relabel evidence to a later source commit. Follow the [0.13.0 adoption guide](../releases/migration-0.13.0.md).
Paid workers and real consumer resets retain their separate authorization gates. Primary unrelated
skill files and uncommitted handoff documents remain untouched.
