# Post-bootstrap compatibility admission release handoff

The dezaaglijst RM-01 implementation source gate exposed two supported-path defects:
the aggregate proof executor rejected an Active roadmap entry, and readiness recovery
could not continue a completed bootstrap. The consumer also has an over-budget roadmap
proposal requiring review. This correction is in Program Kit source; consumer recovery
has not been performed and implementation eligibility is not claimed for dezaaglijst.

## Candidate behavior

- The aggregate executor attaches the latest matching standalone native compatibility
  receipt, validating the planned recipe/contract, fixtures, selected design, toolkit,
  named runtime cases, results and streams. Active/Delivered status is preserved.
- Explicit `resume --post-bootstrap` creates a linked continuation from an intact,
  engine-bound completed bootstrap. Original run, approval, completion and current
  artifacts are archived; intake, assessment, ratification and Accepted ADRs remain
  protected. Review compares every changed artifact against the archived approval,
  including changes predating recovery preparation.
- Authored roadmap sizing is repaired through correction, structural/budget checks,
  a fresh human review, renewed approval and engine-bound completion. Approval is
  never inferred from previous completion.
- Stale executable inputs can renew only in the matching running native continuation
  proof step. Historical receipts remain intact. Chained continuations validate the
  entire recorded lineage to the original confirmed intake.

The pending changes also include release-runner source guards and
`scripts/Invoke-LocalRelease.ps1`. The runner preserves a `source-changed` diagnostic
and stops if HEAD, working-tree cleanliness or validation inventory changes during
Release validation. The Windows helper uses cached pinned toolchains, bounds its
process PATH, restores the caller's environment, and invokes the user-owned Release
suite. Its default execution belongs in the user's terminal; it must not be launched
from a Codex Desktop task.

## Validation evidence

- Bounded Development suite: 58 checks passed; log:
  `artifacts/post-bootstrap-development.log`.
- Proof-plan regression validator: 18 tests passed, including standalone admission,
  Active preservation and rejection of changed/latest-incomplete evidence.
- Final post-bootstrap continuation validator: 2 tests passed, including native
  review pause, implementation phase eligibility after admission, preserved history,
  and a second continuation renewing changed inputs. Log:
  `artifacts/post-bootstrap-targeted.log`.
- Existing bootstrap lifecycle regressions passed after the final review-packet
  adjustment; log: `artifacts/post-bootstrap-lifecycle.log`.
- Release validation runner's 7 unit tests and local release helper's
  PowerShell syntax check passed. These checks do not constitute a Release run.

These are deterministic tests. Coding-agent dispatch is mocked in continuation
tests; no live agent acceptance is asserted. Local artifact logs are ignored files
and are not included in the source commit. Firefox remains in CI; the known local
Windows Firefox launch limitation still applies.

## Release preparation

The user requested committing all pending work so another agent can start release
preparation. VERSION remains 0.12.2; no new release version or tag has been selected
by this handoff. Follow the repository's release process for version selection and
packaging. This change modifies shipped scripts/references/commands, so old local
Release evidence cannot be reused under the non-shipping exception.

After preparing and committing the exact publication candidate, have the user run
the mandatory full local gate in their normal terminal:

```powershell
./scripts/Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Keep that checkout committed and clean throughout validation. Inspect the preserved
`artifacts/release-validation-<version>.log`, journal, receipt and generated artifacts.
CI is authoritative for Firefox. Stable publication stays downstream of the complete
Release workflow; do not announce availability before that workflow succeeds.

## Consumer continuation after the maintained update

After installing the corrected toolkit, the human-owned terminal in dezaaglijst can run:

```powershell
python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id dae559cf --post-bootstrap
```

The source run is `dae559cf`; planning commit is
`decb8bf77b01e8acdcb31c0d6758e15286d0775a`. The retained roadmap compact proposal is
`.program-kit/proposals/roadmap-size-repair/specification-roadmap.md`. It must be
validated and reviewed, not copied into approval authority without review. Toolkit
changes may require renewed native proofs because the receipts bind toolkit sources.
Preserve architecture disposition, all later consumer/device/delivery obligations,
and the existing plans/code. After successful continuation, rerun source preflight
before continuing T006/T007 and the RM-01 implementation tasks. Keep T002/T006
unchecked until the consumer gate actually passes.
