# Bootstrap system critical review

Scope: Household Shopping consumer `program-kit-intake-z2dtgmtu`, workflow `7e59d3e1`,
failed at `execute-compatibility-proofs`. This is an investigation, not an implementation or
authorization to resume. The original consumer, receipts and approved documents were not edited.

## Assessment

The repeated failures expose structural weaknesses in the orchestration and acceptance model.
Knowledge volume contributes to effort, but the stronger evidence is that routine execution
mechanics are still reconstructed by agents, semantic handoffs are incomplete, and failed-run
diagnostics are discarded. Adding more prose alone would not resolve these weaknesses.

Useful safeguards are working: selected profiles now reach architecture, managed dependency
restores succeed, failures do not become passing evidence, and approvals remain hash-bound.
Those safeguards establish honesty and traceability; they do not establish an efficient,
operationally complete path through bootstrap.

## Immediate failure: established facts and limits

The workflow's saved state and
`.specify/governance/compatibility/toolchain-setup/attempt-nj0hntuy/proof.json` show:

- The .NET toolchain probe passed and its prerequisite is closed.
- Browser provisioning resolved Node 24.20.0 and npm 11.19.0 and completed a locked npm restore.
- The authored `browser_toolchain.py` exited 1. Its only retained error is
  `toolchain-setup: required check failed`.
- `test_result` is null. The attempt retains only proof.json, stdout.txt and stderr.txt.

The consumer's `recipe_support.py` sends child output to temporary files and discards it on
failure. Both the Python recipe and its `check.mjs` catch exceptions without reporting a cause.
The installed `bootstrap_lifecycle.py:run_proof` copies JUnit only inside `if exit_code == 0`,
then exits the scratch-directory context. Consequently even a produced failing JUnit file is
not retained. The consumer-generated reporting code writes that file, but its failing cases
are no longer available for this attempt.

It is not possible to identify the original failing assertion from this retained evidence.
Do not describe it as a proven browser-installation, package-license, TypeScript, or npm launcher
failure. A diagnostic version-only check using the installed bounded process runner successfully
executed both node.exe and npm.cmd; that narrow hypothesis did not reproduce. No package restore,
full probe rerun or paid agent was launched during this investigation.

## Structural findings

### Routine platform work is generated anew

The closure skill tells an agent to author Python recipes, adjacent contracts, JUnit case names,
fixture maps, package inputs, process cleanup and compatibility criteria. This consumer produced
custom tool checking, Python reporting, a Node check program, and generic SDK/browser tests.
Those mechanics are platform infrastructure suitable for maintained, tested implementations.
Custom recipes remain appropriate for new consumer-specific integrations, but should not be the
default way to revalidate an unchanged managed platform for every small product.

### Producers can finish without supplying the decisions their consumers need

Intake assigns provider selection to architecture. Research and architecture each asked for
existing-service/hard-constraint information. The respective transcripts record accepted
asynchronous question requests but no answer messages. This is not evidence of permission to
assume there are no constraints. The workflow nonetheless continued through tooling and roadmap
to closure with provider, runtime, storage and identity dependencies open.

The final proof plan contains only two toolchain probes and `readyWhenProven: []`. Even if both
pass, it intentionally permits no roadmap promotion. The closure README explicitly lists the
unselected provider and incomplete host/state/identity work. Partial progress can be legitimate;
the problem is presenting this as ordinary forward execution without a first-class pending-input
or pending-design state and an actionable next step.

### The bounded-context design misses the expensive closure stage

The workflow prepares briefs for assessment, research, architecture, tooling, roadmap and
readiness. It dispatches compatibility closure with generic prose instead of its own generated
stage brief. The closure transcript shows broad reads of all ADRs, the decision register,
prerequisites, roadmap, selection, architecture documents and executor implementation, including
repeat reads. The model has to reconstruct the operating contract at the handoff most dependent
on executable details.

Actual generated brief sizes in this consumer:

| Stage | Bytes |
| --- | ---: |
| Assessment | 60,216 |
| Research | 46,870 |
| Architecture | 63,100 |
| Tooling | 41,761 |
| Roadmap | 84,703 |

The assessment intake projection alone is approximately 41 KB when reserialized; the roadmap
architecture projection is approximately 52 KB. These are byte counts, not token counts or proof
that all content is unnecessary. They do show that the smaller fixture's compactness checks do
not bound a realistic consumer. Project-model expansion and repeated authority material are part
of the burden, not just the size of the static knowledge library.

The closure transcript's final cumulative token event reports 1,385,045 input tokens, of which
1,298,432 are cached, plus 16,177 output tokens. Uncached input plus output is 102,790, matching
the user's CLI summary. Cached tokens are a subset, not an additional input total. No monetary
cost or avoidable-token percentage is inferred from these counters.

### Failure handling preserves the verdict but loses the explanation

The runner correctly refuses success on nonzero exit. However, a failing JUnit result and the
useful child error can both disappear. Credential protection should be implemented by a shared
bounded redaction/reporting mechanism, not delegated to an agent that suppresses every exception.
A failure must preserve its stage, case, reason, exit code and sanitized diagnostic evidence.

### Validator passes are weaker than consumer-flow acceptance

Existing tests exercise real execution as well as mocks and structural fixtures; they are not
worthless. But their passing status did not cover this generated probe's failure diagnostics,
the unresolved-decision handoff, or closure's discovery burden. We need assertions about the
composition of stages and the user's next action, not only the validity of each file or receipt.

The roadmap also groups RM-01 through RM-04 into one joint first specification. This follows an
intake choice for a useful add/read/bought/undo loop; it is not evidence that the fixture secretly
mandated those four entries. It nevertheless needs review against the intended smallest useful
slice, so that journey labels do not conceal a larger implementation batch.

## Recommended direction before another paid run

1. Make failed proof diagnostics reliable first. Retain bounded/redacted failing test artifacts
   and exact failure categories. Recovery must identify whether this is missing input, missing
   provisioning, a probe defect or actual compatibility failure.
2. Put managed toolchain/browser/host checks and their process/reporting mechanics in maintained
   executable recipes. Derive inputs from existing profile/catalog/sync authorities. Do not create
   a second baseline or a separate restore authority. Parameterize consumer-specific proofs.
3. Add semantic exit contracts between stages. Resolve or explicitly pause on first-slice design
   inputs before downstream dispatch; distinguish project architecture approval from a purchase
   or deployment commitment. Pending human answers must survive process boundaries visibly.
4. Give closure a generated minimal brief: selected first slice, exact open dependencies, authority
   pointers, supported recipe choices, available provisioning and one terminal contract. Keep full
   evidence queryable. Measure repeated reads and size growth on realistic inputs.
5. Test the assembled pipeline with deterministic stage outputs and maintained real executors,
   including missing constraints, failed probes, absent browsers, stale pins and targeted recovery.
   Require correct diagnostics, preserved approvals and no unrelated stage reruns. Then use one
   fresh live intake/bootstrap/first-slice run for model-quality and efficiency evidence.

This is a redesign proposal for execution boundaries and validation coverage, not a recommendation
to discard proven domain/.NET knowledge or weaken acceptance gates. Further paid reruns should
wait for those failure paths and the complete route to a Ready first slice to be demonstrable.

## Evidence locations

Consumer root: `C:\Users\Joeyb\AppData\Local\Temp\program-kit-intake-z2dtgmtu`.
Saved workflow state: `.specify/workflows/runs/7e59d3e1/state.json`.
Plan, ledger and roadmap: `docs/architecture/bootstrap-proof-plan.json`,
`bootstrap-prerequisites.json`, `specification-roadmap.md`.
Recipes: `docs/architecture/compatibility/`.
Local transcript directory: `C:\Users\Joeyb\.codex\sessions\2026\09\14`.
Research: session `01a09fb9-6a39-70c3-9246-3b0f7197247c`;
architecture: `01a09fc2-1f6e-7091-a2cf-9c80602aafb9`;
closure: `01a09fd5-62db-7910-a042-89c541e535db`.
