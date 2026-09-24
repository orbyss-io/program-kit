# Intake and first-slice closure handoff repair

## Observed failure

Consumer run `a103c7f2` reached `require-first-feature-handoff` with SPEC-001 Blocked.
Its three planned runtime probes passed, but `readyWhenProven` was empty. The ledger
retained four architecture blockers: composition compatibility, provider compatibility,
local access, and device fit. No planned probe covered those four. Structural validation
of the ledger and recipes therefore passed without establishing a path to the first handoff.

The evidence also mixed distinct obligations. The approved intake deferred consumer
persistence details to feature planning, access setup to before implementation, and device
preference to synthesis review or frontend planning. Proposed ADRs combined external
compatibility with tests of future consumer behavior. Device intent and actual device
verification became one blocking condition. Generic runtime receipts cannot close those
conditions, and relabeling a real provider dependency would not be an acceptable repair.

The trial's closure output reported a 6,669-byte roadmap, over its existing 6,144-byte hard
limit. Closure could edit that document but its output contract did not check its size.

The user explicitly chose a fresh consumer for the next trial. No repair, answer,
approval, status change or evidence rewrite was applied to the failed consumer. A
Program Kit maintainer's hypothetical device preference is not consumer authority.

## Source changes

- The existing intake method now separates intended access surface from later empirical
  device/accessibility verification. Consequential choices are answered or the disclosed
  proposal is confirmed during intake, preserving default provenance. The validator rejects
  confirmed human-decision/human-answer-required records and contradictory blocking deferrals.
  Semantic honesty still matters: validators cannot infer every dependency from free text.
- The existing lifecycle reference owns the phase distinction: consumer intent, external
  feasibility and consumer implementation verification. Architecture and closure use that
  authority. Shared provider risks still require real compatibility evidence; detailed
  consumer admission and behavior retain their feature gates.
- Closure validation now requires all open architecture prerequisites of the selected first
  slice to have probes and its complete conditional Ready transition. Incomplete coverage
  fails before probes run, with the missing IDs, owners and tasks. Future slices may remain
  blocked. Legacy consumers without a selected first-slice contract retain existing behavior.
- First-feature handoff recovery returns to closure, not roadmap redrafting. Closure also
  enforces the roadmap's existing byte budget.
- Feature intake exposes only the selected slice's inherited feature-plan obligations.
  Each must link to a reviewed decision; deferrals retain the existing planning gate.
  Unknown, duplicate or excluded links fail. Scope changes invalidate confirmation without
  invalidating it for unrelated slices or routine lifecycle status changes.

## Verification and limits

Targeted tests cover incomplete proof coverage without execution, complete execution and
receipt reuse, unresolved intake answers versus legitimate later verification, closure
roadmap budgets, and inherited obligations reaching the existing planning gate. Existing
intake/strategic-map regression checks also run. A standalone test import-path defect was
corrected so those tests use the same sibling imports as the installed CLI.

Passed: 23 intake-authoring tests, 14 proof-plan tests, 14 feature-intake tests, stage-context
checks, existing bootstrap-intake and strategic-semantic checks, and the bounded Development
suite. A separate `Start-IntakeSession.ps1 -PrepareOnly` setup check also passed. Seven installed
source hashes and the generated architecture skill were checked against the repaired source.
The logs are preserved under
`artifacts/intake-closure-*-2026-09-16.log`. The initial setup attempt exposed an inaccessible
inherited `UV_CACHE_DIR=C:\ProgramData\uv\cache`; the follow-up uses the per-user local-app-data
cache for that process. No machine-wide setting or existing consumer was changed.
Successful setup evidence: `artifacts/intake-sessions/bc7921fb49ee4a3fabed500dcc4751cc/`.

These checks do not establish live interview quality or a completed bootstrap. The next
human-owned trial starts from the unchanged household-shopping vision only, with no
acceptance contracts or prewritten consumer answers. Its actual questions, phase assignment,
first-slice proof coverage, token use and final roadmap remain live evaluation criteria.
