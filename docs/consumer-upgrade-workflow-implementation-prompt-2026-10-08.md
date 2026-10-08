# Fresh session prompt for the consumer upgrade workflow

Paste the following prompt into a new Program Kit session. The approved plan is stored in this repository; this prompt authorizes branch creation and implementation there. It does not create a new session by itself.

---

Implement the approved consumer upgrade workflow for Program Kit.

Read `C:\Users\tech_\Code\program-kit\AGENTS.md` and `C:\Users\tech_\Code\program-kit\docs\consumer-upgrade-workflow-plan-2026-10-08.md` in full. The plan was fully approved by the user on 2026-10-08 after a detailed design interview. Treat its settled decisions as requirements; do not restart that interview. Resolve ordinary implementation choices yourself. Investigate new facts and ask only for consequential decisions that the approved plan cannot resolve, while continuing independent work.

## Branch and source preparation

Create a `codex/consumer-upgrade-workflow` implementation branch, using an isolated managed worktree when needed. If that name already exists, inspect its purpose and use a safe unique suffix rather than resetting unrelated work. Follow applicable worktree/tool instructions, inspect attached worktrees and avoid taking a checkout owned by another chat.

The handoff checkout was observed on `main`, at commit `42ea361e54b341caa922f76b3d62bd42faf54b67`, with VERSION 0.12.9. These are observations, not a requirement to reset or freeze source at that commit. Reinspect current HEAD, status and instructions. The checkout contained unrelated modifications, including the updater, building-block/dependency code, bootstrap/runtime/probe code and tests. Preserve them. Do not stash, overwrite, delete, commit or silently import unrelated changes.

If the primary checkout is dirty, implement from a suitable committed baseline in a separate worktree. Inspect any overlapping changes read-only to understand concurrent work. Integrate needed predecessor work only when its ownership and committed source are established; record genuine dependencies instead of losing or copying unreviewed work. The two handoff documents may still be uncommitted in the primary checkout: read them there and copy only those approved documents into the implementation worktree if needed. Do not lose them when changing directories.

## Required product behavior

Deliver a resumable consumer upgrade workflow with a conversational command or skill as the entry point, integrating the existing release-owned updater and normal Spec Kit hooks.

- Compare cumulative source-to-target semantic changes against actual consumer adoption, customization, current code, architecture and exact dependencies. A new default offers optional adoption; supported retained choices remain valid.
- Maintain structured reviewed metadata for substantive release changes, their applicability, alternatives, verification and supersession. Inspect the whole consumer for impacts while editing only affected areas.
- Ask grouped consequential questions, preserve unchanged intent/confirmation and existing authority, and use existing substantive architecture/dependency review routes. Preserve founding bootstrap history; do not restart it merely because a toolkit version changes.
- Refresh affected architecture/spec/plan/tasks and resume from the earliest affected phase. Preserve valid requirements, saved task IDs, completed work and consumer edits. A feature already at tasks does not automatically return to specify.
- Keep one minimal coordination record. During upgrade, create bounded planned migration briefs with reason/evidence, scope, outcome/invariants, trigger/due phase, dependencies, maintained method and uncertainties. Avoid eager generation of all detailed migration plans.
- At migration pickup, inspect current inputs, perform focused analysis, create normal detailed plans/tasks/tests, resolve material choices, then implement and verify. Publish reusable planning methods/recipes; allow bounded reviewed consumer-specific plans when no recipe fits.
- Scope blockers to actual affected work and due phases. Permit deferred migrations when retained compatibility is established. Complete migrations required for the upgrade itself before declaring success; an unresolved shared incompatibility cannot be hidden as deferred work.
- Integrate a lightweight compatibility scan into ordinary feature intake before a feature directory exists, and refine it as planning reveals scope. Match planned migrations against owners and touched contracts; keep output regenerable and decisions/dependencies in existing documents. Do not introduce per-feature approval packets, generic bootstrap gates or application build dependencies on the coordination record.
- A newly discovered migration enters the same local recovery path immediately. Distinguish detectable omissions, activated conditions, changed inputs/new scope and unresolved causes. Convert demonstrated omissions into regressions; unaffected work remains available.
- Provide a minimal sanitized local evidence report for maintenance with relevant versions, findings, reproduction/results and recovery outcome. Preserve original local evidence; never export raw logs/architecture wholesale or send a report automatically.
- Support honest actual-layout assessment where structured historical guidance is incomplete. Resolve consequential gaps without fabricated history or blockers based only on age.

## Isolation and destination activation

Consumer upgrade preparation uses an isolated branch/worktree from a known commit and installation state. Inventory tracked files, owned untracked/ignored setup, authority and customization. A plain worktree may lack `.specify` and the bundle/registry state required by the updater. Establish a supported exact baseline reproduction route; do not copy arbitrary caches, invent installation history or overwrite consumer edits.

Validate effective project roots and all mutation destinations. Installed Specify can honor inherited `SPECIFY_INIT_DIR` instead of `cwd`; establish that every primitive targets the intended disposable worktree. Handle any scoped environment adjustment explicitly and do not borrow paid-worker sanitization or bypass sandbox restrictions.

Preserve the original setup through failed/interrupted preparation and abandonment. Allow concurrent development on the old version; reassess intervening changes and validate the combined result before merge. Activation must reconcile/reproduce toolkit installation and required readiness in the destination, including assets that Git merge cannot carry. Test restoration of the original setup on failed activation. Source branches/worktrees do not undo database/cloud/deployed state; use disposable resources for qualification and leave external rollout separately scoped.

## Implementation and validation

Follow the full plan's implementation sequence and acceptance scenarios. Re-read current implementation seams listed there; historical documents and research observations may differ from current code. Reuse the updater, release guidance, dependency transitions, managed reconciliation, feature scope readers and current engineering flow rather than introducing duplicate lifecycle authority.

Add meaningful regression and installed/package consumer checks using isolated fixtures. Cover optional defaults versus mandatory conflicts, multi-version comparison, shared migration scope, tasks-phase repair, migration pickup/staleness, pre-spec scans, newly discovered migration recovery, report redaction, ignored installation state, project-root overrides, interruption, conflicting edits, destination activation recovery, concurrent development, legacy history and baseline versus introduced failures. Verify actual outcomes and preserve evidence; structural or installer success is not semantic/application acceptance.

Use targeted validators during development and finish with:

```powershell
./scripts/Test-ProgramKit.ps1 -Suite Development -BrowserEngines 'chromium,webkit'
```

Firefox cannot launch on this local Windows host. Keep Firefox in CI; report the known host limitation. Do not repeatedly retry it or modify production behavior for it.

Do not run the complete Release suite, select/publish a release, move tags, upgrade real consumers, launch interactive intake or paid live-acceptance workers, mutate machine-wide tooling, or send maintenance messages under this request. Follow AGENTS.md if the user later authorizes those separate phases. Dependency review precedes release candidate selection; ordinary implementation stays within the bounded Development workflow.

Keep an implementation journal with the chosen base, work packages, decisions, targeted/Development results and remaining limitations. Update documentation, actual packaged command/skill/workflow registration and validation coverage. Prefer existing dependencies; add any justified new external dependency to maintenance-policy.json. Preserve historical profiles, evidence and consumer locks.

Complete the authorized implementation and deterministic validation. Finish with a reviewable branch/diff, concise behavior summary, verification results, remaining material limitations and next actions. Keep work local unless the user authorizes pushing or creating a PR. Do not claim completion while required product or recovery behavior remains unresolved.

---

The approved plan is the authoritative requirements record. This prompt supplies execution context for a fresh session; no implementation or consumer upgrade was performed while recording it.
