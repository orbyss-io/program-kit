# Live workflow cases

These optional paid runs use committed fixtures from `tests/live/scenarios/`.
They are separate from deterministic Development and Release validation. A
passing deterministic test, copied fixture or artifact-only completion is not a
live workflow acceptance result.

Prepare a clean candidate and its exact complete local Release receipt first.
On this Windows host the user runs Release in their own terminal with
`-BrowserEngines 'chromium,webkit'`; Firefox remains a CI gate. Never create or
rewrite a receipt to make it appear that Release ran against changed product code.

## Choosing and authorizing a case

Use `python -m live.v2.fixture_catalog --list` with `PYTHONPATH` set to `tests` to
list fixture IDs and versions. The maintained PriceCalculator case is
`price-calculator-approved-intake`, version `1`.

The human issues a phase-specific manifest through
`scripts/New-LiveAcceptanceAuthorization.ps1`, choosing:

- `workflow-fresh`: start a new disposable project from the exact confirmed intake.
- `workflow-failure`: start another disposable project and, only after real READY,
  inject a documented NOT READY report immediately before the native readiness guard.
- `workflow-resume`: continue the exact checkpoint written by a prior segment.

The authorization command takes the existing `-ReleaseReceipt`, `-Model` and
`-ReasoningEffort`, plus `-Fixture` and `-FixtureVersion`. Resume takes the previous
segment's `manifest.json` as `-Checkpoint`. At a paused human review it also takes
the user's actual `-Verdict` (`approve`, `ratify`, or `reject`, as offered by that
gate). The command displays the saved packet before its exact typed authorization
confirmation. Agents supply the mechanical paths and show the concrete review to
the human; users do not need to locate run IDs or construct manifest files.

Start the authorized segment with:

```powershell
python tests/live/v2/workflow_acceptance.py run --authorization <issued-manifest>
```

Each segment consumes one manifest and stops at the next real human gate or
terminal engine outcome. It reserves at most eight real command dispatches in
supervisor-owned evidence before dispatch. New segments, retries and interrupted
runs require a new unconsumed authorization bound to the latest checkpoint. A
manifest does not approve unseen architecture, ratify a constitution, or authorize
another segment. Existing paid building-block phases retain their own contracts.

## Evidence and completion

Every segment records its fixture digest, exact candidate receipt, native run and
current step, dispatch reservations, authorization consumption, parent checkpoint,
project inventory, preserved native run files, and supervisor output streams with
raw-stream hashes, redaction, cleanup and drain results. Inspect emitted Codex
usage separately from any monetary charge; no inferred cost is claimed.

A paused gate is pending work. A controlled failure is recorded only if a real
READY report was preserved before injection and the native requirement stopped
the engine. A successful acceptance result requires the supported lifecycle's
governance validation, engine-bound completion and native terminal `completed`.
Report the fresh chain and the failed/resumed chain separately, including all
native source/continuation IDs. Preserve earlier segment manifests unchanged.

Workers stay in their disposable repository with `workspace-write`. Registry
credentials remain with supervised restore operations. Environment or provider
unavailability produces an honest blocker; no fixture, approval or READY record
may be fabricated to make acceptance pass. The original PriceCalculator checkout
is not an execution workspace and must remain unchanged.
