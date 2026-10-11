# Story delivery and human review implementation plan

Date: 2026-10-11. Status: accepted design, prepared for implementation in a fresh session after the current official Program Kit release completes. Implementation and publication are separate actions.

Program Kit will help implementation agents deliver small, runnable user stories promptly, verify changes according to risk, and obtain human feedback before moving to another story. Known scaffolds should be materialized coherently instead of reconstructed through artificial failing-test cycles. Human review and time-drift reporting must survive interruptions and resumes without adding repeated acceptance suites or approval dossiers.

## Starting point and scope

Begin from the successfully published predecessor and its committed source, after verifying that the complete tagged Release workflow and public assets succeeded. Do not start this work inside the current publishing agent's frozen checkout. Inspect current instructions, Git state and installed mechanisms again; paths below identify inspected responsibilities, not a requirement to reset to an earlier commit. Read this plan and its [fresh session prompt](story-delivery-and-human-review-implementation-prompt-2026-10-11.md).

The implementation belongs to Program Kit's maintained commands, templates, compact feature state, validators and release guidance. Reuse existing scaffolds, verification runners, governance decisions, installation fixtures and GitHub access mechanisms where suitable. Foundation changes, upstream component publication, a new agent supervisor, automatic GitHub monitoring/posting, and migration of partially implemented features are outside scope unless a concrete prerequisite is discovered and separately agreed.

Claim Evaluator motivates the change but remains untouched. Its stopped session reported 31 of 115 tasks completed without a delivered end-to-end slice. Its older task graph made all stories depend on 22 foundational tasks. This is evidence of the delivery problem, not a specification to reproduce or permission to restart that consumer.

## Story boundaries and delivery order

A user story is the default unit of human acceptance. An operation is an internal unit of implementation, integration and technical verification. Completing every useful operation does not require a human review or pause.

For a UI product, each story must produce a runnable journey through its relevant UI, backend and persistent or external effects. Backend-only products use their actual supported interface. A route, component, handler or database migration alone does not establish a delivered story. Known enabling work stays beside the first operation needing it; future infrastructure does not become a blanket prerequisite.

Assess story boundaries during specification and planning, then confirm them during task generation:

- One coherent actor intent and observable useful outcome, with explicit non-goals.
- A concrete independent walkthrough and required success/material failure outcomes.
- Connected integration, including the necessary authorization, ownership, persistence and recovery behavior.
- Only the enabling dependencies actually needed for that outcome; preserve real provider, security and authority gates.
- An estimate to human-reviewable behavior that includes preparation, integration and verification, not only writing source files.

Reconsider oversized stories before generating their implementation tasks. Split along useful journeys, not backend/frontend/test layers or arbitrary endpoint counts. A larger story needs an explicit rationale and disclosed expected effort. The two-hour story target is a sizing aid and drift warning, not a guarantee or an automatic rejection of a valid story.

Earlier human checkpoints are optional. Agree them explicitly during planning when significant product uncertainty or a consequential assumption warrants early feedback. If new uncertainty appears during implementation, propose a checkpoint and obtain the human's decision before making it a progression gate. Do not silently schedule one for every operation. Reuse a review that already covers the unchanged complete story outcome rather than requesting duplicate acceptance.

## Verification selected by risk

Require appropriate verification for meaningful changes. Choose sequencing from the changed responsibilities, uncertainty and available maintained proof. Labels such as small, UI, adapter or scaffold do not by themselves establish low risk.

| Work | Default method |
| --- | --- |
| Known scaffold, deterministic templates, generated structure, unchanged qualified components | Materialize a coherent batch first; run maintained generation/configuration/build/integration checks; add missing consumer-specific tests afterwards. |
| New critical authorization, ownership, transaction, concurrency, replay, destructive-action or recovery behavior | Prefer meaningful test-first development with focused behavioral/boundary checks. |
| Reproducible bug | Prefer a regression that demonstrates the defect before fixing it. |
| Straightforward wiring or presentation | Implement a small increment and verify immediately through appropriate tests, inspection and existing regressions. |
| Refactoring | Use existing behavioral regressions and add coverage where missing; do not manufacture a new failing behavior merely to justify the refactor. |

Knowing a pattern does not establish correct configuration or customization. Scaffold qualification and inherited component proof cover their actual scope; application policies and changed integrations retain their own checks. Run the relevant scaffold checks before dependent product behavior relies on readiness. Use existing maintained authentication/provider fixtures rather than authoring another generic harness.

Record risk, verification method and any reason for an alternative sequence briefly in existing plan/tasks. Routine choices require neither a new ADR nor human approval. Observe intended missing behavior when test-first is selected; a compile error, missing tool or unrelated environment failure is not a valid red result. Group coherent behavior checks instead of requiring a shell invocation for every assertion.

Run focused checks for changed behavior and expand through affected contracts and reverse dependencies. Reuse passing evidence only for unchanged relevant inputs/environment; retain unresolved failures. Progress saves, resumes and human story checkpoints do not trigger full application acceptance. Story closure uses its relevant regression coverage. Complete feature acceptance and publication retain their existing gates.

## Human review and progression

Before presenting a story, the agent exercises its integrated journey and passes the relevant automated checks. Present the actual runnable entry point, necessary prepared test data/account instructions, a short walkthrough, expected results and material limitations. Disclose simulated external responses and limit acceptance claims to what was demonstrated. A mockup may inform design but cannot establish implemented-story acceptance.

Human review assesses usefulness, clarity and faithfulness to the intended journey. It does not require the reviewer to repeat the automated technical suite. A simple story can have a brief review but still needs explicit acceptance or deferral.

Persist separate engineering and human dispositions for each story and any explicitly agreed earlier checkpoint. The minimum human states are pending, ready for review, changes requested, accepted and deferred. Engineering tasks can remain checked when genuinely complete while human review remains pending. Such a story is not fully accepted.

At a required checkpoint, pause by default before starting another product operation or story. The agent may repair or diagnose the presented outcome and improve its review instructions. Acceptance permits the authorized progression. Deferral permits only the explicitly named checkpoint or bounded listed batch; it leaves review outstanding. All required deferred reviews must be resolved before overall feature acceptance. Silence, elapsed time, screenshots and an agent's own test results never grant acceptance or continuation authority.

Corrections to already agreed requirements remain within the current story. A genuine new requirement or product decision needs a scope decision and an update to the affected existing artifacts. Required technical failures cannot be waived by a human product approval. Optional improvements can be placed in the backlog explicitly without relabeling required defects as enhancements.

Record the presented checkpoint, covered outcome, relevant implementation/configuration basis, reviewer and actual decision source. Material changes to the reviewed behavior reopen affected review, including changed user meaning, workflow, authorization or persistence outcomes. An unrelated test correction or a new commit alone does not invalidate every accepted story. Preserve valid prior acceptance through unrelated changes and GitHub outages.

## Review roles and GitHub identity

Default the feature owner and reviewer to the requesting human. Let the owner explicitly assign different people and reassign review roles. The reviewer can accept, request corrections or defer assigned checkpoints. The owner controls scope changes, reviewer reassignment, broader deferrals and effort-budget revisions. Review delegation grants no additional spending, release or unrelated implementation authority.

GitHub linkage is optional. When selected, bind a role to a nominated account, verify the actual account through maintained read access, and obtain human confirmation of the assignment. Retain the provider/host, stable account identity and readable login/reference. A repository owner, commit author or connected tool account is not automatically the requesting human or reviewer.

The requesting reviewer can decide in the implementation conversation when identity is established. A delegated reviewer can supply an authenticated GitHub decision reference tied to the exact checkpoint. Retrieve an explicitly supplied reference, verify its author against the authorized assignment and verify its checkpoint scope. Ambiguous responses remain pending. A generic PR approval does not accept every story checkpoint.

If author/scope cannot be verified or GitHub is unavailable, the new decision remains pending. Preserve established decisions; allow an explicit owner reassignment to the conversation reviewer. Do not fabricate an approval or use an automatic fallback. Posting review requests, polling GitHub and automatic monitoring are separate work requiring explicit authorization.

## Time drift and resume

Use adjustable defaults of 60 active elapsed minutes per implementation operation and two active elapsed hours per human-reviewable story. Include preparation, planning, builds, integration, tests and repairs. Exclude explicit human waiting. Measure elapsed time rather than summing parallel command durations, and preserve accumulated effort through interruptions, resumes and reassignment of the same work.

Both thresholds warn the user and agent that the work is drifting. Neither is an automatic implementation block or a promise of delivery. On crossing a threshold, report what works, what remains, the observed or suspected cause, and the smallest corrective next action. Reassess scope or story boundaries and continue bounded authorized work when appropriate. A real technical/authority blocker or a pending required human review still blocks its dependent work.

Do not reset accounting by renaming work, saving progress or requesting review. Human waiting suspends accounting; repairs consume active effort. The feature owner can revise the declared budget explicitly. Report once at a threshold and update when the diagnosis, scope or remaining effort materially changes; avoid repeated warnings for every command. Use a controllable clock in deterministic tests rather than waiting for thresholds to elapse.

## Fresh start for existing consumers

Adoption of this improvement requires a fresh affected-feature specification and implementation. There is no continuation or migration of an in-progress specification, plan, task graph or partial implementation under the new workflow.

1. Checkpoint/archive the abandoned attempt and retain its history and failed evidence.
2. Install the released toolkit through its normal supported update route.
3. Preserve unchanged confirmed bootstrap/feature-intake decisions, accepted architecture, installed foundations/tooling, consumer locks and previously delivered features.
4. Amend and ratify the constitution through its existing reviewed mechanism to adopt balanced verification, story review and the new progression policy.
5. Review an explicit reset inventory for the affected unfinished feature. Shared source, generated outputs, migrations and database data need clear ownership before any reset. Resetting a feature does not authorize deleting unrelated code or live data.
6. Abandon its old specification/plan/tasks/implementation/tests as active work; keep them in history rather than reuse partial feature code or checkmarks as new progress.
7. Rerun specify, clarification, plan, tasks, analysis and implement. Use the maintained configured hooks once at their owning boundaries rather than duplicate their checks. Unchanged confirmed intent can inform the fresh specification without restarting the whole product interview.

The fresh session implementing Program Kit qualifies this route only with disposable fixtures. It does not reset Claim Evaluator or another actual consumer. A live consumer reset requires its concrete inventory and explicit selection in that consumer's session. Existing service/data adoption is outside this feature reset policy.

## Maintained implementation responsibilities

Reinspect these owners on the published baseline and change their canonical policy together. Update source registration/descriptions when required; changing only implement would leave conflicting upstream rules.

| Owner | Required change |
| --- | --- |
| `presets/program-kit-governance-preset/templates/constitution-governance.md` | Replace universal test-first sequencing; establish human story review, authority and advisory drift policy through existing constitution ratification. |
| `templates/spec-governance.md` and governance `commands/speckit.program-kit-governance.specification-intake.md` | Carry balanced verification and coherent independently testable story outcomes. Preserve settled intake and existing confirmation mechanisms. |
| `templates/plan-governance.md`, `templates/tasks-governance.md`, preset tasks/analyze/implement commands | Define story/operation boundaries, risk-based test methods, required story reviews, optional agreed early checkpoints and bounded deferrals. Remove conflicting mandatory per-operation human review or universal test-before-code ordering. |
| Governance phase-context/implementation-check commands; `references/vertical-slicing.md`, `phase-evidence.md`, `ui-feedback-and-recovery.md` | Align projected guidance, scoped checks, readiness and early human review. Keep routine coding free of extra approval ceremony. |
| Governance `scripts/task_draft.py`, `phase_obligations.py`, `implementation_preflight.py`, and existing state helpers | Persist and validate story/checkpoint dispositions, assignment/decision provenance, review freshness and cumulative elapsed accounting. Cover progression, resume, ordinary closure, formal handoff and the no-hook path. |
| Existing consumer upgrade guidance/recipes and `releases/` assets | Publish the explicit fresh-feature reset requirement and constitution amendment. Preserve toolkit installation/recovery and historical guidance; do not offer partial-feature continuation for this improvement. |
| Existing task/governance/installation validators and `tests/validation-inventory.json` | Add focused behavioral/failure controls and reuse the installed consumer fixture. Keep added qualification bounded and registered with accurate ownership. |

Paths in the first three rows are under the governance preset unless otherwise stated; governance commands/references/scripts are under `extensions/program-kit-governance/`.

Use one canonical compact feature state, with readable status in ordinary tasks/progress output. Extend existing persistence and validation rather than add parallel review ledgers or a framework. Preserve the implementation baseline and unresolved failure references. Select the smallest storage shape that can retain all required story decisions without losing them when the current checkpoint is replaced.

The maintained workflow must reject invalid progression and acceptance claims. Instructions alone are insufficient: installed entry/transition/finish paths must consume the validated state, including when optional hooks are absent. The tool is not an agent supervisor and cannot physically prevent arbitrary edits outside its workflow; do not claim such control. Engineering commands remain independently runnable without human approval records, and their successful execution never establishes human acceptance by itself.

## Implementation sequence and acceptance

1. Verify the predecessor publication, inspect the current baseline and create a dedicated implementation branch/worktree as needed. Copy only these handoff documents if they remain uncommitted; preserve unrelated work.
2. Map canonical policy sources and existing state/validator entry points. Create one compact checklist in this plan or normal existing implementation output.
3. Implement aligned constitution/spec/plan/task/analysis/implementation guidance and the story-sizing criteria. Verify the resolved installed instructions, not only repository source text.
4. Implement minimal persistent review/assignment/freshness/progression and clock support, reusing existing helpers. Add GitHub reference validation with fixture responses and no automatic posting/monitoring.
5. Add fresh-feature reset guidance and one concise installed reset fixture. Verify the revised constitution route and regenerated fresh-spec workflow.
6. Run appropriate targeted checks, then the bounded Development suite for the integrated change. Review actual code, generated artifacts and failure cases; repair only identified defects.
7. Prepare release/migration guidance and publication evidence under the existing maintenance and Release policy, keeping the exact candidate frozen during final validation.

The acceptance checks must establish:

- Ordinary operations can progress within a story without human review; required story or explicitly agreed early checkpoints pause progression.
- Engineering completion cannot manufacture human acceptance; pending, changes-requested, stale, wrong-reviewer, unverifiable and out-of-scope decisions cannot close the required review.
- Explicit acceptance and bounded deferral permit their actual scope; required deferred reviews remain due at feature acceptance. Resume, ordinary closure, formal handoff and absent hooks cannot bypass the state.
- Reviewed unchanged behavior remains accepted; material affected changes reopen the corresponding checkpoint without resetting unrelated accepted stories.
- Known scaffold generation can precede tests and reuse maintained proof; new critical/customized behavior receives its appropriate checks without duplicate publisher suites or full acceptance at every checkpoint.
- Time warnings survive resume, exclude human waiting, include repairs, and never block solely because elapsed time exceeded a threshold.
- GitHub identity/decision checks use authenticated source attribution and exact checkpoint scope, with offline/unavailable outcomes handled truthfully. Fixture identities/decisions are explicitly simulated and establish no human acceptance.

## Concise reset qualification and prompt publication

Add one deterministic installed fresh-start fixture to the existing installed-workflow exercise, rather than create another package-installation loop. Seed representative old partial spec/plan/tasks/code and a strict ratified constitution. Prove the revised constitution needs normal ratification, old progress cannot authorize continuation, the selected reset preserves designated bootstrap/toolkit/shared inputs, and fresh specification through subsequent phase contracts consumes the new policies. Use simulated human decisions only within the disposable fixture.

No historical feature-migration matrix, real consumer/data migration, live coding-agent trial or new service cohort is required for this change. Existing installation, source-protection, updater retry/recovery and packaging checks remain because they protect toolkit behavior. The fresh fixture proves workflow contracts and installed guidance, not coding-agent delivery speed.

Keep added checks small and reuse existing test setup. Use deterministic clocks, local fixtures and recorded GitHub response shapes. Expand coverage only for changed responsibilities, identified failures or an unresolved concern. Do not add redundant audits, repeat full suites after ordinary edits, redesign release infrastructure or introduce dependencies without a concrete need.

Publication still follows [AGENTS.md](../AGENTS.md), [dependency maintenance](maintenance/dependency-review.md) and [releasing guidance](releasing.md): maintain active pins/locks and regenerate profile/knowledge together, freeze the candidate, obtain successful local Release evidence and green CI, then require the complete tagged Release and public install/upgrade checks. This patch changes shipped content, so the predecessor's receipt is not fresh evidence for it. Apply the existing non-shipping evidence-reuse exception only where its actual conditions hold for later corrections.

Local Windows checks use Chromium/WebKit; Firefox remains in CI. Local complete Release remains human-terminal work unless the user explicitly authorizes that future Codex task's existing opt-in. Implementation of this plan does not by itself authorize publication, live workers or real consumer deletion. Report actual validation outcomes and outstanding gates without claiming availability before publication succeeds.
