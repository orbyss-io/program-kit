# Bootstrap epics, feature seeds and consumer comparison

The accepted redesign is implemented on `codex/bootstrap-intake-analysis`, based on main commit `969ccf04d90e9a539df402836c810dc54349bd7b`. Bootstrap now models the supplied vision, preserves rich feature proposals and recommends a starting outcome. Roadmap epics can contain independently scoped feature specifications. Feature intake reuses the supplied seed and settles the exact delivery boundary.

Fresh implementation agents covered feature identity, canonical seeds and bootstrap/roadmap behavior. A fresh reviewer inspected the integrated result, and a separate fresh agent exercised the installed CLI. The coordinating agent reviewed the changes, ran maintained validation and compared the original disposable consumer with a fresh installation. No material correctness blocker remained in the independent review. One malformed-sibling robustness edge and one Windows validation limitation are disclosed below.

The original main checkout and its unrelated dirty work remain intact. Implementation lives in `artifacts/worktrees/bootstrap-intake-analysis`. After the original implementation review, the user authorized committing and pushing this branch. No publication is included.

## What changed

| Owner | Delivered behavior |
| --- | --- |
| Bootstrap guidance and assessment | Discover identity, ownership, lifecycle meaning and consequential relationships across the supplied vision. Preserve detailed proposals and boundary reasoning. Investigate architecture-changing uncertainty now; deepen feature behavior at its specification intake. |
| Canonical architecture map and authoring | Optional epic membership, intended/exploratory commitment, rich structured seeds and feature dependencies. Validate references, evidence, duplicate/self/cyclic dependencies and preserve outputs on rejected authoring. |
| Bootstrap handoff and stages | New `recommended_start` names exact candidate IDs and remains nonbinding. Retain the full future portfolio and architecture. Legacy `first_slice` remains readable for existing accepted consumers. |
| Roadmap parsing and generated view | Epic type, completion criteria, exact feature-seed membership and intent. Show membership separately from feature dependencies. Completion follows agreed outcomes, with human-owned delivery status. |
| Specification intake | V2 briefs have independent `featureId` and parent `roadmapEntry`. Two features of one epic have separate draft/review/confirmation scopes. Seed content and partial brief answers initialize the draft; resume preserves existing answers. |
| Receiving consumers | Feature context, knowledge, phase obligations, retained decisions, capability deferral and upgrade resolution use the actual selected feature. Relevant incoming future consumers remain visible without importing their complete detailed seeds. |
| Compatibility | Existing entry-only v1 briefs and confirmed references remain usable. No mandatory global rebootstrap, extra approval ledger or speculative feature branches. |

The primary contributor entrypoints are [specification intake](../../extensions/program-kit-governance/scripts/specification_intake.py), [bootstrap context](../../extensions/program-kit-governance/scripts/bootstrap_context.py), [roadmap governance](../../extensions/program-kit-governance/scripts/governance_state.py) and the [canonical map schema](../../extensions/program-kit-governance/references/architecture-map.schema.json). The [consumer intake guide](../../extensions/program-kit-governance/references/specification-intake.md) documents the installed CLI and durable references.

For new work, `--entry EPIC-001 --feature admit-service-job` identifies one child intake. Its brief lives at `.program-kit/specification-intake/features/admit-service-job/brief.json`. Another feature under `EPIC-001` gets a separate directory and confirmation. A specification records its parent epic, feature ID, exact brief reference and confirmation hash. Cross-feature, wrong-parent and escaping references reject without replacing valid evidence. Optional `affected_features` narrows an existing prerequisite to its actual child features; omitted scope retains historical parent-wide behavior.

Detailed exploratory input stays exploratory. Creating a seed or draft does not confirm or commission it. The actual feature-intake review and confirmation establish selected scope through the existing mechanism.

## Matched disposable-consumer comparison

The original fictional WorkshopFlow scenario is [retained here](bootstrap-intake-analysis-2026-10-23/scenario.md), with its [original simulated interview](bootstrap-intake-analysis-2026-10-23/transcript.md). The comparison used exactly the same 2,001-word input and reused the same thirteen simulated answers. The input SHA-256 is `cedf61242318159eb598a1062ebc5a183808073975d6563b1fa88d13cc450cb8`. The original nine-file evidence snapshot was verified unchanged after the replay.

Both consumers were prepared through the shipped `Start-IntakeSession.ps1 -PrepareOnly` path. The fresh consumer used the implemented source and installed proxy-intake surface. Real installed builders and validators ran. Answers, proposed boundaries and epic grouping were authored in this session and are explicitly simulated. No independent interview, bootstrap workflow, approved roadmap or fictional application implementation is claimed.

### Control: unchanged candidate model, changed handoff

This is the clearest causal result. The original and new installed stage-plan functions received the same original seven-journey, nineteen-candidate model. The original legacy selection named the repair source journey. The new recommended start named `perform-repair` explicitly. The complete outputs are in [same-model-control.json](bootstrap-intake-comparison-2026-10-23/same-model-control.json).

| Output | Original installed behavior | New installed behavior |
| --- | --- | --- |
| Selection representation | `first_entry` bound to source journey `vision-repair` | Nonbinding `recommended_start` names exact feature candidate |
| Selected candidates | `schedule-job`, `perform-repair`, `issue-report` | `perform-repair` |
| Commission rule | Exactly one roadmap entry must cover the selected journey's candidates | `first_entry: null`; feature intake settles exact useful scope |
| Remaining vision | Other candidates available as future portfolio | All nineteen retained as feature-seed inputs |

The new behavior removes the demonstrated forced bundle. It does not claim that repair without scheduling or an issued report is always a good feature boundary. Those supporting capabilities can be prerequisites or part of one coherent selected outcome when actual intake establishes that need.

### Rich-output demonstration

A second replay authored coherent feature proposals using the preserved scenario and answers. It demonstrates the new representation and receiving intake; the grouping/count reduction is an authored boundary review, not an automatic decomposition result.

| Output | Original draft | New authored draft |
| --- | --- | --- |
| Broad source journeys | 7 | 7 |
| Architecture contexts | 4 | 4 |
| Candidate outcomes/features | 19 operation-oriented candidates | 16 proposed features |
| Explicit epic grouping | No canonical epic links | 7 groups: 6 intended, 1 exploratory |
| Structured feature seeds | 0 | 16, including preserved page detail and boundary rationale |
| Commitment distinction | Future ideas described in source prose | 15 intended features and 1 explicit exploratory franchise option |
| Child intake demonstration | Entry-keyed intake contract | Two distinct V2 drafts under `EPIC-001` |

The founding decisions, subdomains, bounded contexts, modules, contracts, context relationships and journeys were compared for exact JSON equality and remained unchanged. This isolates richer delivery organization from an invented architectural rewrite. Full [before](bootstrap-intake-comparison-2026-10-23/before-architecture-map.json) and [after](bootstrap-intake-comparison-2026-10-23/after-architecture-map.json) maps and the [comparison summary](bootstrap-intake-comparison-2026-10-23/comparison.json) are retained with the branch.

The installed roadmap renderer produced this [diagnostic graph and membership table](bootstrap-intake-comparison-2026-10-23/roadmap-projection.md) from authored epic records. It shows, for example, two features in Reception and repair agreements and three in Parts supply. Directed prerequisites cross epic boundaries where appropriate; membership does not require waiting for every sibling. The graph was written outside the consumer. No authoritative consumer roadmap was generated or approved in this proxy exercise.

Two actual installed feature-intake drafts demonstrate the receiving boundary:

| Feature | Parent | Reused seed | Draft result |
| --- | --- | --- | --- |
| [Admit service job](bootstrap-intake-comparison-2026-10-23/draft-admit-service-job.json) | `EPIC-001` | 1,759 characters of detailed source | Users, outcome and scope prefilled; unconfirmed |
| [Manage repair agreement](bootstrap-intake-comparison-2026-10-23/draft-manage-repair-agreement.json) | `EPIC-001` | 3,852 characters of detailed source | Separate users, outcome and scope; unconfirmed |

Both retain their boundary rationale and unresolved questions. The rich input is available to deepen the selected specification rather than being lost in a broad epic summary. Independent installed regression tests additionally exercise review, confirmation, checking, resume and sibling-edit isolation; this fictional proxy comparison deliberately stops at draft intake.

The same thirteen answers were reused to hold input constant. Therefore this comparison proves no reduction in question count and no measured improvement in interview judgment. The guidance changes target question relevance; a future authorized independent interview would be needed to observe that behavior.

## Review findings and dispositions

The independent review found adjacent assumptions that a specification-intake-only change would have missed. Those were repaired before final validation:

- A future capability could not defer to another feature in the same epic. It now accepts an exact child identity with proved parent membership, while retaining true self-deferral and unknown/wrong-parent rejection.
- Parent-wide eligibility could obscure child scope. Explicit feature selection is validated before filtering; feature-scoped before-specification conditions do not blanket-block unrelated siblings.
- Feature knowledge omitted direct incoming future consumers. Their boundaries, relevant dependency rationale and contracts are now projected, while their detailed seeds remain outside the selected feature's context.
- Arbitrary seed metadata could be mistaken for canonical decision references. Seed content remains lossless without gaining architecture-decision authority.

The separate installed-flow agent exercised actual installed subprocess commands, not just imported source functions. All 26 specification-intake tests passed in the final maintained affected run. Positive flows and rejected cross-feature/parent/path references check that existing bytes survive rejection.

One minor robustness edge remains: `feature_plan_decisions.satisfied` resolves same-epic sibling brief references before selecting the requested child. A malformed unrelated sibling reference can interrupt eligibility inspection with a diagnostic. Ordinary sibling scope edits preserve independence. This is a narrow invalid-input handling limitation, not evidence that a valid sibling confirmation becomes stale; it is retained here for follow-up rather than hidden by the passing normal-path tests.

## Validation and retained evidence

Product source remained fixed during final input-bound runs. The maintained inventory selected 45 affected checks with no coverage gaps; its prepared-run selection additionally included the required shared archive build. Documentation and comparison snapshots were written after those runs. A final Integrity run covers this reporting update separately.

| Run | Actual result | Retained local record |
| --- | --- | --- |
| Integrity before Affected | 7 checks passed; 7.325s | `artifacts/validation-runs/20261023T194927Z-46635046/results.json` |
| Final Integrity after review material | 7 checks passed; 7.377s; `git diff --check` also clean | `artifacts/validation-runs/20261023T200142Z-6b9a2c95/results.json` |
| Affected against `969ccf04...` | 42 passed, 3 failed; 498.919s; no source mutation or coverage gaps | `artifacts/validation-runs/20261023T194946Z-39ecea35/results.json` |
| Explicit bootstrap handoff, governance and context checks | All 3 passed; 55.630s | `artifacts/validation-runs/20261023T195212Z-1fe38b1b/results.json` |
| Focused scaffolding and evaluation-journey reproduction with native process access | Both passed; 55.336s | `artifacts/validation-runs/20261023T195820Z-7b2debd4/results.json` |
| Focused adverse-boundary reproduction with native process access | Still blocked before behavioral control; failed; 6.416s | `artifacts/validation-runs/20261023T195859Z-31b56360/results.json` |
| Fresh installed proxy draft and matched control | Draft builder and proxy verification passed; original snapshot unchanged | `artifacts/epic-comparison/comparison-attempt-01.txt`, `before/baseline-manifest.json`, `after/` |

The original affected failures were independently inspected. Windows blocked a generated readability assembly, denied the native evaluation adapter's Service Control Manager query, and blocked the adverse test executable. The first two passed unchanged on focused native-process reruns. The adverse executable remained blocked by Application Control even there; its compiled valid/adverse markers were never reached. That check remains a local coverage limitation, never a passing negative test. Both original and later failed logs remain retained.

An earlier whole consumer-upgrade test run occurred while implementation files were changing: 31 tests produced one source-freshness failure and one Windows junction error. On frozen source, the exact source-freshness test passed. The junction test passed with native process access in 1.432s. Those focused reproductions are retained at `artifacts/epic-comparison/upgrade-focused-reproduction.txt` and `upgrade-junction-external-reproduction.txt`; the original run survives in the agent tool transcript. The affected representative upgrade mechanism also passed in 88.086s.

For reproducibility, use the existing prepared Python and a writable TMP/TEMP. The principal commands were:

```powershell
./scripts/Test-ProgramKit.ps1 -Python <prepared-python>
<prepared-python> scripts/run_validation.py --suite Affected --changed-from 969ccf04d90e9a539df402836c810dc54349bd7b --engines=chromium,webkit
<prepared-python> scripts/run_validation.py --check validate_bootstrap_handoffs --check validate_governance_state --check validate_bootstrap_context --reason "Changed epic roadmap, recommended-start handoff, scoped feature prerequisites and installed feature identity contracts"
```

This change does not require browser scenarios; no Firefox result is claimed. Exact-source package CI and Linux execution were not run locally. No release, paid-worker or independent-agent acceptance claim follows from these development checks.

The original consumer is retained at `artifacts/intake-analysis/temp/program-kit-intake-ekhf_bb8`, session `2c3d70267d9f44058ab4e92b93f84dcb`. The new consumer is `artifacts/intake-analysis/temp/program-kit-intake-_34oeqsi`, session `8b4e5548e5464735873cf826e4714ba1`. Both retain simulated provenance, zero bootstrap workflow runs and no product confirmation. The local comparison driver is `artifacts/epic-comparison/compare.py`; the original immutable-snapshot verifier is `snapshot_before.py` alongside it.

## Suggested human walkthrough

Start with the unchanged-model handoff comparison, then inspect the epic graph and the two feature drafts. These show the intended separation: whole-vision architecture and grouped outcomes at bootstrap, independent detailed commissioning at feature intake. Review the installed intake guide and new schema fields against the accepted [design](bootstrap-intake-epics-design-2026-10-23.md). The exact remaining execution gap is the Windows-blocked adverse check; independent interview quality remains unmeasured. The next decision is human review of this implementation and its demonstrated boundaries.
