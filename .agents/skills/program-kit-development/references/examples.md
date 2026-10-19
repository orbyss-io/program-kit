# Proportional contributor examples

These are representative requests and expected working approaches, not fabricated
execution results. The [creation review](../../../../docs/reviews/program-kit-development-skill-review-2026-10-19.md)
records the bounded exercises actually performed and their limits.

## Small documentation edit

Request: “Add an Affected preview example beside the existing validation guidance.”

Inspect [docs/validation.md](../../../../docs/validation.md) and the actual
`--list` branch in [run_validation.py](../../../../scripts/run_validation.py).
Add the example in the existing procedure, preserving its semantics:

```powershell
python scripts/run_validation.py --suite Affected --changed-from <base-commit> --list
```

Inspect the Markdown diff, check the command against the actual CLI, and select
repository checks under actual AGENTS.md. Explain what changed and what ran in
chat. No new test for the wording, mandatory interview, disposable consumer or
retained review index is necessary. A correct example is not fresh runtime proof
of every check it might select.

## Bug fix with an independently specified rejection

Request: “Affected selection unexpectedly includes a broad manual-only check.”

Trace `select_affected()` and its callers before assuming the inventory is wrong.
The [existing selection tests](../../../../tests/validate_validation_runner.py)
contain an independent miniature producer/consumer/unrelated/manual-only graph.
Reproduce the extra selection with that oracle, repair the owning selection
mechanism and rerun meaningful selection cases, including unknown-input behavior.
Do not suppress the broad check by weakening its inventory registration.

For a disposable exercise, a deliberate removal of the manual-only filter can
produce this illustrative repair:

```diff
-    checks = [c for c in definition['checks'] if
+    checks = [c for c in definition['checks'] if not c.get('manualOnly') and
```

The rest of the comprehension is omitted here. Review the complete actual diff
and test output. The initial red must show unwanted selection; an import failure
would establish only broken setup. Show the preserved independent test, actual
red/green, unaffected selection and remaining limits. Label seeded defects as
fictional; they are not findings against the approved source.

## Substantial feature with an unsettled contract

Hypothetical request: “Add machine-readable JSON to the existing validation preview,
including selected checks, reasons, gaps, manual decisions and bounds.”

Investigate `select_affected()`, `deferred_checks()`, `closure()` and `main()` in the
existing runner, the inventory, selection tests and maintained validation guide.
Check current text output, list-only side effects and exit semantics. Reuse those
owners. JSON rendering does not justify another runner or evidence lifecycle.

A consequential open choice is whether callers may depend on a stable public
integration contract or whether this is a developer diagnostic view. Explain the
compatibility consequences and recommend a scoped answer. Do not silently invent
versioning promises or change failure exits while calling it presentation work.
Agree observable outcomes and review boundaries after that decision. Possible
sections are:

| Section | Inspectable outcome |
| --- | --- |
| Read-only preview | Actual JSON for representative selections; existing selection ownership and text behavior preserved; listing executes no checks. |
| Failure/compatibility behavior | Independent unknown-input/manual-decision cases retain the agreed diagnostics/exits; documented interface and relevant regressions. |

The human may authorize both sections together. Otherwise, finish and walk through
the first before starting the second. At each boundary explain actual output and
important source changes, with links to complete material and honest omissions.
A plan or a paused interview proves neither implementation nor feature delivery.

## Review and continuation language

Scale this to the change; these are useful contents, not a required form:

- Start with the request and the delivered behavior, then show its normal entry
  path and the important actual file/diff/output excerpts.
- For each relevant control, connect input, expected result, actual result and
  retained evidence. State if source review supplies a judgment tools cannot make.
- Name the source and environment each execution binds. Preserve failures, budget
  overruns and unsupported hosts separately from functional outcomes.
- Give the next person the exact checkout, current section, settled choices,
  unresolved findings, evidence location and next action. Identify real human
  decisions separately from fixture authoring or an agent's recommendation.

An inline explanation could say: “This fixture deliberately removes the filter.
The unchanged selection oracle reports an extra manual-only check. Restoring the
filter makes the same case pass; unknown inputs still remain gaps.” Attach that
wording to actual inspected results before presenting it as an observation.
