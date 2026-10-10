# Reusable consumer foundations implementation

Single compact checklist for the [accepted plan](reusable-consumer-foundations-plan-2026-10-10.md).
Owners implement bounded tranches; the orchestrator and fresh reviewers inspect actual source,
installed artifacts, package consumption and retained evidence. Normal evidence stays under artifacts/.

Foundation **0.3.2 is published**. Program Kit **0.12.11 remains an unpublished candidate**.
The user authorized publication in that order and local Release through the dedicated override.
Notes and De Sportomgeving remain read-only; their services and live data were untouched.

| Obligation | Owner / dependency | Implementation and acceptance | Remaining |
| --- | --- | --- | --- |
| 1. Lifecycle baseline | Lifecycle/packaging owners; orchestrator | Reused feature-owned Prepare/startup/workers, selected-root staging, scoped verification and browser durability. Pure-library RootPackage retained; no extra Composition library or consumer host. Targeted checks pass. | Final integrated gates. |
| 2. Foundation contracts | Foundation owners; runtime/release reviewers | Typed crawler policy, mandatory private floor, response-local admitted nonce, denial/isolation and late-denial cache repair; provider/deadline contracts. Published runtime packages and immutable dual-platform Host were inspected; scans report zero High/Critical. | Complete for Foundation publication. |
| 3. Compositions/configuration | Composition/identity owners; Foundation contracts | BFF/Keycloak and EF/PostgreSQL descriptors, typed defaults, relational validation, precedence/lifecycle and theme envelope. Public issuer differs from private transport/admin. Sixty-two sync checks include 48 invalid-alias rejections without writes. | Final-source qualification; deployment-specific TLS/proxy/provisioning checks during adoption. |
| 4. Materialization | Sync/retirement owners; composition inputs | Existing preview/digest/apply flow; minimal feature-owned API/provider seams; root and nested runtime layouts; rerun/customization/conflict/removal. Customized Sport Feed survives and builds outside selected runtime roots; probes stay out of production selection. | Final rebuilt archives/install checks. |
| 5. Maintained verification | Setup/readiness/native-runner owners | Shared authentication/provider fixtures and supervised processes; **26 setup / 50 qualification contracts pass**. Actual HTTP ownership/conflict/restart and Sport xUnit/MTP cases pass; skipped native cases reject. Application transaction/replay/recovery semantics remain application-owned. | Final Firefox/complete gates. |
| 6. Architectural views | Configuration/view owners; contracts | Templates, source reference/Mermaid, browser allowlist, redacted configured attribution and actual options/DLL provenance. Shell-provider projection and unobserved owners are labeled accurately. | Inspect final regenerated views. |
| 7. Product workflow | Installed-workflow/upgrade owners; materialization | Generation, readiness and product acceptance stay separate. Native tasks/implement plus analyzer append remove the blanket barrier while retaining named prerequisites. Actual 512-entry archive, installation, interrupted activation/recovery/retry and resolved task-template checks pass. | Rebuild/review after shipping repairs and maintenance. |
| 8. Migration/performance | Disposable qualification owners; fresh reviewers | Both disposable migrations preserve data, accepted history, locks/custom settings and independent features. Zero newly authored generic harness lines and zero remaining generic setup tasks. | Final-source timings and Program Kit publication; live adoption remains explicit consumer work. |

Foundation: [successful Release](https://github.com/orbyss-io/dotnet-foundation/actions/runs/38067350551),
[public 0.3.2](https://github.com/orbyss-io/dotnet-foundation/releases/tag/v0.3.2).
Host: ghcr.io/orbyss-io/foundation-host@sha256:d4d74db6c56ef335fe44dc69a2b13b003718d847e9aa61849cdd587d4867306c.
The selecting profile and 415-source/447-range knowledge were regenerated and qualified together.
Build 0.3.1/exporter 0.2.5 remain independent; Spec Kit 1.1.3, xUnit/MTP 4.0.2 and Analyzer 0.3.2 are selected.
Historical profiles/evidence, existing consumer locks and personal skills remain preserved.

Current checks and repairs:

- Clean bounded Development at f20d7e7, tree cb131bc20a2b84baa0cec497f8915d1d2993a657,
  passed **87/87** in **646.914s**; root verified all hashes and unchanged source before/after:
  [journal](../artifacts/validation-runs/20261010T223738Z-4ee333a6/journal.json). It precedes the final C4 cached-exit correction.
  Earlier 09f3a1d 87/87 in 656s remains historical evidence.
- Authorized local Release at bc322c3, tree e40048cab74fdc1e4a6a6f6a6af5a3d6347c9ff8,
  passed **120/121**; sole failure was Windows C4 cleanup with a locked diagnostic log.
  Root verified all 121 hashes: [journal](../artifacts/validation-runs/20261010T214305Z-7ae14a00/journal.json).
  Original failed transcript is preserved as release-validation-0.12.11-bc322c3-failed.log; no receipt was created.
- All six [cold/prepared cases](../artifacts/tests/reusable-foundations/332dbe71f3f2414c/qualification.json),
  actual product operations/restart checks, native MTP and both migrations passed. Root/fresh review inspected
  runtime package/assembly copies, redacted views and actual HTTP/authentication/native outcomes.
- [Full CI 38088782367](https://github.com/orbyss-io/program-kit/actions/runs/38088782367): Linux 119/120,
  Windows 5/5. [Maintenance 38088785038](https://github.com/orbyss-io/program-kit/actions/runs/38088785038):
  119/120. Both fail during product-schema setup before issuer checking; PostgreSQL exits 2.
  Root verified all 125/120 unique log hashes. Earlier failures remain preserved failures.
- PostgreSQL owner/fresh/root review confirms the temporary image bootstrap accepts sockets before the final
  TCP server. The repair uses TCP without widening budgets. Actual authenticated schema, outage, restart,
  retained data and removal pass; controlled real handoff proves old socket readiness succeeds while new TCP
  readiness rejects bootstrap. [Actual evidence](../artifacts/tests/reusable-foundations/postgres-readiness-draft-20261011/validation-results.json),
  [fresh positive/exact-old-source negatives](../artifacts/tests/reusable-foundations/postgres-readiness-fresh-review-6d7a4710f6f34d49/result.json).
  Root verified 180 process receipts/360 streams and all fresh control streams.
- C4 repair passes root/fresh review: bounded Windows completion wait, closed parent streams and owned
  child cleanup when state writing fails. Three actual repeats and an independent 10.578s validator pass;
  exact old source reproduces open streams/WinError32. Nine handle outcomes, seven invalid PIDs, launch/state
  failure and detached/exited child checks pass. [Fresh evidence](../artifacts/tests/c4-view/fresh-cleanup-review-f4f2a570d93a40ca/review.json).
  A subsequent audit found CPython can cache an exit code and bypass Popen.wait completion. The final
  Windows fallback now always uses the native helper before Popen.wait; controlled success/timeout cases
  reject the exact f20 old source. Two actual repeats and [fresh 10.568s validation](../artifacts/tests/c4-view/fresh-cached-review-641b10434dea4464/review.json)
  pass with unchanged hashes. Root inspected source, actual CPython methods and all six retained control streams.
  Forced-cleanup flags remain recorded; minimal controls show that flag alone cannot prove a viewer leak.
- [Complete CI 38092114773](https://github.com/orbyss-io/program-kit/actions/runs/38092114773) passed Linux 120/120 and Windows 5/5 at f20d7e7; root verified all 125 log hashes. Firefox is covered in CI.
- [Maintenance 38092113058](https://github.com/orbyss-io/program-kit/actions/runs/38092113058) passed 120/120 checks; root verified their hashes. Its final PR step failed because Actions cannot create PRs. The exact pushed commit 6af8773 changes only Python 3.15.0 and was manually reviewed/adopted through [PR 38](https://github.com/orbyss-io/program-kit/pull/38). Published Foundation synchronization restores the initial CShells 0.0.30 proposal to its authoritative preview.174 ABI; locks/profile/knowledge are unchanged.
- Actual scan review rejects that maintenance run's apparent two-platform result: its arm64 report describes amd64 and repeats the amd64 ImageID. Program Kit's repaired remote scanner binds exact immutable child manifests and actual platform/config identities; real platform revalidation remains required. Foundation's published OCI-archive reports independently describe distinct amd64/arm64 images and correct immutable leaves.
- d1e928e integrates final C4 and the tested Python pin. Full CI 38093753423 and maintenance 38093755711 are running; they precede the scanner correction. Python 3.15.0 device update is pending under the [user-terminal policy](../extensions/program-kit-governance/references/device-toolchain-policy.md); dependent local qualification remains paused. Actual PrepareOnly exits 1 with PKT030 (required 3.15.0, detected 3.14.8); [preflight](../artifacts/program-kit-publication/device-preflight-python-3.15.log) starts no Release suite.
- Scanner owner/fresh/root review passes after bounded traversal, strict report schema and timeout corrections. Twenty-seven targeted library-runtime controls pass (not Python 3.15 candidate qualification), including wrong cached architecture/ID, stale/malformed/missing reports, findings despite exit zero and scanner failure. Root inspected code and all 21 retained owner hashes, five process receipts and two fresh streams: [actual controls/manifests](../artifacts/tests/maintenance/platform-scan-contract-1990bcb0d15f4843/validation.json). Actual prior arm64 evidence is rejected; fresh remote scans remain mandatory.
- Fresh bounded Development, exact-source local Release, complete CI/maintenance and tagged Release/public
  install/upgrade remain required. No stable Program Kit tag was pushed. **The complete plan is not yet achieved.**

Measured bc322c3 baseline, preceding the PostgreSQL/C4 repairs and final maintenance:

| Shape | Cold / prepared first-product-operation conservative bound | Cold / prepared full workflow |
| --- | ---: | ---: |
| Base | No product operation | 127.834 / 81.597s |
| Notes | 140.257 / 98.160s | 169.288 / 127.497s |
| Nested Sport | 152.795 / 103.062s | 192.524 / 140.524s |

Cold uses fresh isolated NuGet/npm/browser acquisition; SDK, Docker and immutable images were preinstalled.
Prepared reuses the same consumer. Single observations are not factory-cold provisioning or statistical claims.
The conservative first-operation bound includes wrapper overhead:
generation + readiness wall clock - (integration elapsed - integration time to first operation).
The baseline-derived target is 180s cold / 120s prepared under these conditions, not a CI wall-clock gate.

Configuration/adoption:
[templates/envelope](../extensions/program-kit-dotnet/references/foundation-compositions.md),
[source reference/Mermaid](../artifacts/tests/reusable-foundations/332dbe71f3f2414c/sport/consumer/docs/architecture/foundation-configuration.md),
[configured view](../artifacts/tests/reusable-foundations/332dbe71f3f2414c/sport/consumer/artifacts/tests/runs/foundation-20261010T215627-6702380e4dda47a28852ad815f7d84de/effective-settings.configured.json),
[actual options/provenance](../artifacts/tests/reusable-foundations/332dbe71f3f2414c/sport/consumer/artifacts/tests/runs/foundation-20261010T215627-6702380e4dda47a28852ad815f7d84de/effective-settings.runtime.json),
[adoption](maintenance/reusable-foundation-adoption.md), [0.12.11 migration](../releases/migration-0.12.11.md).
Local browsers are Chromium/WebKit; Firefox remains in CI. No paid coding-agent phase was requested.
