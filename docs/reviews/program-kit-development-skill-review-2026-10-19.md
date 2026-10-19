# Program Kit development skill: review and continuation

Status: implemented and bounded exercises completed; **human review pending**.
No commit, push, PR, cleanup or publication is authorized by this record.

Worktree: `C:/Users/tech_/Code/program-kit/artifacts/program-kit-development-skill`.
Branch: `codex/program-kit-development-skill`.
Approved source base: `4b90dc7ea6458fc2fbd6a5ae7e35c552426ad9e8` (F7).
The shared dirty maintenance checkout and F8 worktree are separate owners.

## Agreed design

The human separately authorized skill creation, superseding its historical deferral.
Read-only investigation covered actual checkout instructions and skills, current
skill-creator guidance, the contributor plan, all F1–F8 checkpoints, retained guided
indices and final handoff, validation/contribution/maintenance/release procedures.
The grilling interview settled these choices before implementation:

- Small changes stay direct. Substantial work agrees useful sections and review
  boundaries; pause after the current section unless several were authorized together.
- Safeguard/rejection/freshness/preservation claims need meaningful independent
  controls where applicable, including intended behavioral markers after compilation.
- Explain actual happy-path source/output and relevant negatives inline, backed by
  retained material for substantial review. Keep results, source review, observed
  agent behavior and human acceptance separate.
- Exercise small-edit completion, a fictional seeded bug fix and substantial-feature
  investigation/decision-boundary behavior. The last is not full feature delivery.
- Implement this skill and its references/metadata as one reviewable change, then
  stop for human review. No additional runner, ledger or approval lifecycle.

## Start the review

Read [SKILL.md](../../.agents/skills/program-kit-development/SKILL.md), then
[examples](../../.agents/skills/program-kit-development/references/examples.md).
Inspect investigation/decision boundaries, proportional sectioning, validation
selection, meaningful negatives and the review/continuation instructions.
The optional [observed lessons](../../.agents/skills/program-kit-development/references/observed-lessons.md)
attributes the reusable guidance without making the whole historical campaign a
routine prerequisite. [UI metadata](../../.agents/skills/program-kit-development/agents/openai.yaml)
uses normal automatic discovery; explicit invocation is `$program-kit-development`.

The maintained inventory already treats `.agents/skills/**` and `docs/**` as
documentation/review-only inputs. No product runner, inventory, dependency,
consumer command or F8 implementation changed. There are four new skill files
and this review document, all uncommitted.

## Actual exercise walkthrough

Three fresh in-session evaluating subagents used separate disposable copies of
approved F7. They received the entrypoint and raw repository material; the skill's
supporting examples/lessons and creation review were held out. These are bounded
forward observations, outside deterministic repository validation and the separate
live-acceptance harness. They establish neither automatic skill discovery nor a
general causal improvement over an agent without the skill.

| Exercise | Actual result and where to inspect |
| --- | --- |
| [Small edit](../../artifacts/skill-review/exercises/small/artifacts/exercise-review.md) | Added seven lines to the disposable validation guide without needing clarification or adding tests for prose. Inspect its actual diff and corrected preview. Integrity and Affected each passed seven checks in 8.270s / 8.468s; the original misleading long-path preview and earlier Integrity remain separate. |
| [Seeded bug fix](../../artifacts/skill-review/exercises/bug/artifacts/exercise-review.md) | The unchanged 14-test suite first produced three intended assertion failures. Restoring the selection filter made all 18 cases pass, including four added manual-selection/unknown-history cases. Existing 14 test bodies remained unchanged. All seven Integrity checks passed individually; full suite orchestration was not run, and source-integrity used a disclosed Git-options adapter. |
| [Substantial investigation](../../artifacts/skill-review/exercises/feature/artifacts/exercise-review.md) | Inspected actual owners and nine preview cases, proposed reviewable sections and stopped with two material questions: JSON compatibility promise and pending versus accepted manual decisions. No tracked source changed or checks executed. This was explicitly plan-only, so the stop cannot be attributed solely to the skill. No JSON feature was implemented. |

Start the small-edit happy path with its actual new command:

```sh
python scripts/run_validation.py --suite Affected --list
```

The corrected output lists seven baseline checks without executing them. Inspect
the bug's [original behavioral red](../../artifacts/skill-review/exercises/bug/artifacts/exercise-output/red-existing.stderr.txt):

```text
AssertionError: Lists differ: ['unit', 'client'] != ['unit', 'client', 'broad']
```

Then compare [actual fix diff](../../artifacts/skill-review/exercises/bug/artifacts/exercise-output/actual-fix.diff)
and [green output](../../artifacts/skill-review/exercises/bug/artifacts/exercise-output/green-focused.stderr.txt):

```diff
-    checks = [c for c in definition['checks'] if
+    checks = [c for c in definition['checks'] if not c.get('manualOnly') and
```

The rest of the comprehension is omitted here; the linked diff is complete. Final
output reports `Ran 18 tests` and `OK`. This was an intentionally seeded disposable
defect, not a newly discovered defect in approved F7. The restored runner matches
pristine F7 bytes, so the specimen's final Git diff contains only new tests; the
before/after snapshots retain the real repair. All exercise changes stay in their
disposable copies and are not part of the proposed skill contribution.

The feature report's proposed JSON envelope is labeled proposed, never emitted
output. Its guarded probes adapt only the Git invocation/fictional changed paths
and retain that limit; unmodified explicit CLI previews remain distinct. Its human
questions are future exercise decisions, not unanswered scope for this skill.

Each report links exact commands, exits, costs, both streams and source identities.
[Parent inspection](../../artifacts/skill-review/exercise-independent-inspection.json)
confirms the three source commits, relevant tracked changes, whitespace checks,
unchanged skill inputs, the bug's restored source and preserved original test bodies.

## Validation, review and retained failures

- Skill-creator `quick_validate.py` passed. The local file-link inspection found
  28 links and zero missing targets; Markdown fragments were not checked by that
  script. UI metadata and routing/proportionality were also read in source.
- [Initial Integrity](../../artifacts/validation-runs/20261019T072329Z-d890013a/results.json)
  passed 7/7 in **8.962s**, within 60s, without source drift or coverage gaps.
  It binds the skill and draft report at that time. Final reporting checks and
  exact final source identities are in the [retained review index](../../artifacts/skill-review/index.md).
- [Affected preview](../../artifacts/skill-review/affected-selection.txt) from exact
  F7 selected the same seven baseline checks, with no gaps/deferred checks. There
  was no extra affected runtime contract or reason to replay broad native/provider/
  browser/package scenarios for this repository-only documentation/skill change.
- Separate [authored semantic review](../../artifacts/skill-review/authored-review.md)
  found no concrete defect in the skill, metadata, examples or lesson attributions.
  This is authored review with stated scope, not authenticated human acceptance.

Retain [setup failures](../../artifacts/skill-review/preparation-failures.json):
local Git cloning first failed on sandbox MSYS process startup, then local clones
hit Windows checkout path length. Only the newly owned copies were completed with
command-scoped `core.longpaths=true`; no global configuration or product guard changed.
Plain nested Git subprocesses also produced a misleading selection until their
child environment received that same scoped setting. The small exercise preserves
both previews. The bug report discloses its syntax-check adapter and an earlier
PowerShell parse error; the feature report preserves failed guessed-path searches.
None supplies behavioral-negative proof or is silently relabeled as success.

## Protected material and provisional F8 evidence

F1–F7 remain approved. F8's implementation is not copied into this branch.
Read its original [checkpoint](<C:/Users/tech_/Code/program-kit/artifacts/coding-system-f1/docs/reviews/coding-system-f8-checkpoint-2026-10-18.md>),
[final handoff](<C:/Users/tech_/Code/program-kit/artifacts/coding-system-f1/docs/reviews/coding-system-final-handoff-2026-10-18.md>) and
[guided index](<C:/Users/tech_/Code/program-kit/artifacts/coding-system-f1/artifacts/f8-review-20261018/index.md>) in place.
Its final fresh journey remains **126.204s against 120s, over-budget**, despite
functional completion. F8 approval, requested human-session analysis and complete
feature acceptance are not established by this task.

The initial protection snapshot covered 1,599 shared-checkout files and 2,614 F8
files, including retained F8 review material and the prepared human consumer.
Before skill implementation, comparison showed unchanged shared checkout and F8
implementation state, but changes within the prepared human consumer since the
earlier snapshot. This task made no writes there. Preserve that discrepancy;
neither its cause nor human-session completion/acceptance follows from file changes.
The [final comparison](../../artifacts/skill-review/preservation-summary.json)
records shared HEAD/branch/status and all 1,599 files unchanged. F8 HEAD/branch/status
and captured files outside the human consumer are unchanged. The same 11 changed
and 169 added consumer files remain visible; counts include Git/generated files,
not a count of implementation findings. Initial and later snapshots are retained
separately under ignored `artifacts/skill-review/`. No cause is inferred and no
consumer analysis or acceptance is performed here.

## Results and next action

The demonstrated scope is the entrypoint's use in one small edit, one seeded bug
repair and one substantial investigation, plus structural checks and authored
review of supporting prose. Automatic invocation, full substantial-feature delivery,
multiple models/sessions, general productivity improvements, human acceptance and
release qualification remain unproven. Local Firefox was not attempted. Existing
F8 runtime, session-analysis and approval findings remain open.

Next action: inspect the skill and the actual excerpts/material above, then provide
human review findings. Continue only in this exact worktree/branch at approved F7
with these five uncommitted additions. Do not switch/reset either protected checkout,
copy provisional F8 code, operate the human specimen, clean retained material or
commit/push/open a PR/publish as an inferred next step. No such action occurred.
