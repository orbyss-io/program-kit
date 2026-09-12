# Repository sync candidate and live review

Branch: `codex/repository-sync-coordinator`, based on `33b69e5` (0.11.0).
Candidate: 0.12.0. No publication or live soundness claim is made here.

## Implemented behavior

- `speckit.program-kit-governance.sync` coordinates generated setup context, ordered offline
  adapters, reviewed plan digests, phase readiness and interrupted-operation recovery. Bootstrap
  completion records requirements; before-plan establishes setup; after-plan and implementation
  preflight require current package evidence. Implementation setup materializes existing owned
  subjects and requires renewed/locked restore before application coding.
- The public .NET sync command is retired without an alias. Its guarded internal adapter remains.
  Upgrade uses the same coordinator, preserves accepted existing profiles and future targets, and
  reports pending package verification separately from offline convergence. Retirement preflight
  compares original registrar output and refuses to discard consumer edits or extra skill files.
- Exact npm metadata, isolated strict graph resolution and npm restore share runtime commands,
  catalog registry routes, credential references and CA trust. Missing access, denied access,
  unavailable packages, trust failures and incompatible graphs have distinct diagnostics.
- Graph, restore and readiness evidence bind current inputs. Unchanged graph proofs avoid network
  execution; interrupted restore resumes unchanged completed subjects. Cache relocation alone does
  not invalidate a dependency graph. Changed native locks, manifests, runtime or CA inputs do.
- Accepted composition materialization defers instances until their physical package/project targets
  exist. The full selection remains validated, and managed-file transaction/ownership checks remain.

## Deterministic evidence

Targeted tests cover registry first lookup, credential redaction, strict-policy enforcement,
JavaScript-only planning, bootstrap deferrals, invalidation, interrupted restoration, scoped targets,
actual Spec Kit registration/removal, consumer-edit conflicts and sequential disposable upgrades.
The bounded Development suite and targeted packaging/installation checks are development evidence;
they do not start paid coding agents or substitute for the user-owned Release gate.

Development validation on 2026-09-12 passed: the bounded suite, sequential local upgrades, rebuilt
0.12.0 component/bundle installation, governance authority transitions, exact JavaScript toolchain,
and live v2 contract checks. The final targeted stage checks also cover parent stores in separate
release checkouts, authenticated baseline graph-path relocation, and locked cache rehydration after
upgrade. Logs and the generated fixture inventory are retained under this worktree's ignored
`artifacts/sync-*` paths. CI includes the new deterministic sync checks; CI execution and the full
user-owned Release gate remain outstanding.

## Live review

[Case definitions](../tests/live/scenarios/repository-sync/v1/cases.json) and the
[review contract](../tests/live/scenarios/repository-sync/v1/REVIEW.md) cover matched baseline/candidate
feature flows and upgrade continuation. `prepare_sync_live_review.py` emits the reproducible fixture
inventory. The v2 stage runner binds exact source receipts, phase, case, checkpoint, harness and model
profile to one-use authorizations. Human feature confirmation is a distinct checkpoint boundary.

Stage checkpoints are not full-flow acceptance. Actual functional/browser checks and classified
worker/supervisor evidence must substantiate every assertion and metric before comparison. Unknown
measurements remain null. A failed run is preserved; a rerun requires new authorization.

Before the first paid session, the human-owned Release gate must produce valid receipts for the exact
clean candidates, equivalent bootstrap checkpoints must be available, and model/effort must be fixed.
Then confirm each exact manifest through `New-LiveAcceptanceAuthorization.ps1`. Publication remains
a separate decision and the other release session retains its publication responsibility.

The prepared model assumption is the user's saved `gpt-6-astra` / `high` profile for both comparison
arms; this is not authorization and remains reviewable in every manifest. Use the fixed
`tests/live/scenarios/repository-sync/v1/bootstrap-seed` for both bootstrap runs. Its review explains
the stock Dockerfile precondition and retained original consumer-conflict test.
