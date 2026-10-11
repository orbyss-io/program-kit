# Story delivery and human review implementation

Accepted requirements: [plan](story-delivery-and-human-review-plan-2026-10-11.md).

- [x] Published baseline: v0.12.11, `99f2f6f8639588f4966f99515ebc9b1165f49ff0`; [complete Release](https://github.com/orbyss-io/program-kit/actions/runs/38128815951), tagged checkout, full deterministic inventory, attestation, public publication and install/upgrade all succeeded. Public archives/receipt/checksums uploaded 2026-10-11. Implementation starts at `834a9f2478fb270e883532d62c56c4ad5444567d`, with only publication README/checklist changes since tag.
- [x] Dedicated `codex/story-delivery-human-review` branch/worktree; primary changes retained.
- [x] Align constitution, specification, planning, tasks, analysis, implementation and projected/installed guidance.
- [x] Extend compact tasks checkpoint: story decisions, roles, freshness, progression/resume/closure/handoff and active clocks.
- [x] Validate optional GitHub identity and explicitly supplied scoped decisions using authenticated reads; deterministic simulations only.
- [x] Fresh-feature adoption guidance and one reset exercise in the existing installed-consumer fixture.
- [ ] Targeted checks, review/repairs and bounded Development qualification; record actual results.

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

Evidence so far: story controls 22/22, task generation 19/19, normal development 24/24,
intake 15/15, knowledge inventory 7/7, dependency audit 10/10, phase readiness 18/18;
component registration and local 512-entry packaging pass. The existing packaged consumer
exercise passed with its reset/installation/recovery summary in `artifacts/consumer-upgrade-install.json`.
The first Development journal `artifacts/validation-runs/20261011T105444Z-e1589ca1/journal.json`
is retained as failed: concurrent shipped-source edits tripped exact updater freshness; new rule
ordering/registrations and fresh-state fixtures exposed four repairable validator failures.
All identified targeted repairs pass. Final frozen-source Development qualification remains pending.

Adoption after publication: archive the unfinished attempt; update via the normal installer;
amend/review/ratify the constitution; review/select its exclusively owned reset inventory;
abandon old spec/plan/tasks/code/tests as active progress; rerun specify, clarification, plan,
tasks, analysis and implement. Reuse unchanged confirmed intent/bootstrap, architecture,
foundations/tooling, locks and delivered features. Real resets need their own consumer-session authority.

Publication gates: version selection and versioned consumer-change/release registration; dependency
update with active pins/locks and profile/knowledge qualification together; frozen clean candidate,
fresh successful local Release evidence, green CI (including Firefox), complete tagged Release and
public install/upgrade. This changes shipped content: predecessor evidence cannot replace these gates.
Local complete Release remains human-terminal work unless separately authorized through the existing
opt-in. No publication, paid workers or real consumer reset is authorized by this implementation.
