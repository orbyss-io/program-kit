# Proposed N20: Build must use maintained test orchestration and preserve pack identity

Prepared 16 October 2026 for the consolidated additions queue. Consumer continuation D55 reports a supported Build-entrypoint orchestration failure and a related version-propagation problem exposed by its repair. They are tracked as one coordinated finding with two explicit regression obligations: managed test dispatch and exact build/test/pack version identity. This is separate from N1's child-interpreter readiness and N16's late reference-metadata diagnostics.

No product/consumer code, original approval/audit or active implementation ledger was changed by this collection task. Current consumer code and canonical source were inspected read-only. Reported dispatch greens are not independently executed end-to-end qualification here.

## Source findings and observed failure

The report attributes a user's failed supported build to raw solution tests after successful restore and Release compilation: 67 cases, 49 setup failures comprising nine interpreter-selection, 35 disposable-provider-admission and five missing native-run-directory failures, with 18 passes. This is a reported classification of missing orchestration, not 49 independently established product regressions.

Current canonical `eng/Build.ps1` counts solution test projects and invokes `dotnet test --solution ... -c Release --no-build -p:Version=...` directly. It therefore does not enter the maintained `Invoke-RepositoryVerification.ps1` scoped path or selected consumer runner adapter for those tests. Current wrapper source also has an Acceptance fallback into Build, so blindly calling its default scope from Build risks recursion.

The consumer repair discovers actual IsTestProject projects and invokes the existing wrapper with named Focused projects, Release configuration, forced fresh coverage and a concrete reason. It temporarily supplies the already selected Python and restores the prior value in finally. That is a plausible way to preserve the managed isolation, runner, logs and failure ledger while avoiding the Acceptance fallback. Its actual wrapper/complete build qualification was still underway in D55; no full green build is established by collection.

## Related exact-version gap

The maintained scoped verifier rebuilds selected projects. Current canonical single-project build has no `-p:Version`, and its traversal project sets Configuration but no Version. Passing a global version only to the earlier solution build and later no-build pack cannot establish that the intervening tests used those same versioned outputs. The consumer adds a validated `BuildVersion`/`--build-version` value to both build modes and binds it into planning and before/after coverage fingerprints; it refuses that narrowing parameter in Acceptance.

Treat version identity as a separate required subcase, not as solved merely by routing tests through the wrapper. Reuse the repository's supported version contract, pass it as a literal property/argument without shell/property injection, and retain project/SDK version semantics. Avoid introducing an untracked environment override or a parallel version source. Actual compiled assembly/package metadata and bound evidence are stronger proof than a command string or package filename alone.

## Critical assessment and planned upstream work

**Owners:** Program Kit installed Build, verification wrapper/native runner adapters, build identity/freshness and central installed build qualification. Preserve all existing setup/provider/test guards.

1. Trace the supported Build, explicit skip and Acceptance fallback flows and implement one maintained dispatch route. Scope must be bounded by the actual complete solution test set, not a handpicked subset or currently affected files. Preserve explicit skips as skips without claiming new test execution. Handle genuinely empty solutions honestly.
2. Evaluate IsTestProject against the actual requested configuration/version and supported project formats. Preserve graph ownership and fail actionably for unsupported/external/dynamic cases; do not silently omit tests or rely only on filename suffixes or a stale count. Tests required outside that solution remain their separately declared obligations.
3. Use the selected interpreter, wrapper-managed isolation and declared runner adapter. Keep the disposable provider/environment and run-directory lifecycle owned by their existing adapters; never substitute live database credentials, weaken admission or bypass guards to reproduce a direct raw-test command. Child runtime overrides must restore on every outcome without exposing secrets.
4. Make orchestration nonrecursive. An internal Focused dispatch over every discovered solution test is a development/build execution mechanism, not permission to relabel that result full Acceptance or narrow a separately requested Acceptance gate. Preserve existing wrapper validation and recorded scope/reason.
5. Propagate the exact intended version through selected single/traversal builds, architecture where applicable, test execution and subsequent no-build pack. Bind configuration/version/toolchain/source/build outputs to planning and reuse admission before and after execution. Different versions must not reuse each other's coverage even when source files are unchanged.
6. Preserve failure tracking, output/drain/isolation cleanup and nonzero behavior. If dispatch, preparation or tests fail, packing/publication cannot proceed as if tests passed. Retain earlier failed evidence and never manually clear it. Update installed ownership/managed-file records through maintained generation.

## Required central evidence

| Obligation | Proof |
| --- | --- |
| Default actual Build dispatch | Installed representative solution with multiple test projects uses the maintained wrapper and selected adapter; all expected projects and genuine results are observed. |
| Preparation ownership | Fresh-shell selected Python, disposable PostgreSQL admission, run directories and offline/isolation policy work; missing prerequisites remain actionable failures. |
| Discovery and configuration | Evaluated IsTestProject/configuration/version and supported project formats are covered; empty and explicit-skip cases do not fabricate tests. |
| No recursion/narrowing | Acceptance fallback terminates through the intended path; unsupported Acceptance narrowing remains rejected; Build's reason and complete solution test set are recorded. |
| Failure and environment restoration | Failed wrapper/adapter/test prevents pack, retains evidence and restores prior child-selection state; caller/operator interruption and cleanup remain honest. |
| Single/traversal version identity | Both paths compile/test with the intended version and configuration; inspect actual assembly/package metadata and no-build pack behavior. Wrong/missing/malicious version inputs fail within the documented contract. |
| Freshness and reuse | Version-only changes invalidate relevant prior coverage; planning, execution, post-run fingerprints and any reusable successful records agree. Unspecified normal development retains its defined default behavior. |
| Complete integration | Actual installed wrapper and end-to-end build/pack work in relevant Windows/CI environments, with current affected tests and exact-candidate qualification later. Extracted-block or mocked dispatch tests alone are insufficient. |

The consumer reports regression-first extracted dispatch coverage and five passing dispatch/version/failure/restoration/empty-skip cases. An initial dynamic-scriptblock PSScriptRoot problem was a test-harness mistake, not a production defect. Its sandbox-restricted `dotnet --info` attempt remains an environment failure, not a waived plan result. Preserve these distinctions until the actual full route passes.

## Collection disposition

Queue N20 with N16–N19 for one later consolidated handoff. The latest inspected maintenance ledger still has 47 findings and has not adopted these five additions; the combined inventory would be 52 if all are adopted. Do not increase the count for the reported individual setup failures or silently count version propagation as closed without its own proof. No new paid calls, stories, device preparation, destructive data operations, human acceptance or publication authority is granted by this diagnosis.
