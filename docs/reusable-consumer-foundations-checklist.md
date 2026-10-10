# Reusable consumer foundations implementation

Single compact checklist for the [accepted plan](reusable-consumer-foundations-plan-2026-10-10.md).
The orchestrator reviews code, installed artifacts and actual evidence; implementation owners and
independent reviewers cover bounded tranches. Normal evidence remains under `artifacts/`.

Foundation **0.3.2 is published**. Program Kit **0.12.11 is a candidate and is not yet available**.
The user authorized publication in that order and the dedicated local Release override.
Notes and De Sportomgeving remain read-only; no live services or data were changed.

| Obligation | Owner and dependencies | Delivered / acceptance | Remaining |
| --- | --- | --- | --- |
| 1. Lifecycle baseline | Orchestrator; lifecycle and packaging owners | Reused feature-owned Prepare/startup/workers, selected-root staging, scoped verification and durability repairs; pure-library RootPackage retained. Targeted lifecycle, packaging, task and catalog checks pass. | Final integrated gates. |
| 2. Foundation contracts | Foundation owners; independent runtime/release reviewers | Typed crawler policy, mandatory private floor, response-local admitted nonce, denial/isolation and late-denial cache correction; maintained provider/deadline contracts. [Release 38067350551](https://github.com/orbyss-io/dotnet-foundation/actions/runs/38067350551) succeeded; root verified 30 public runtime packages and immutable dual-platform Host, both scans zero High/Critical. | None for Foundation publication. |
| 3. Compositions/configuration | Composition and identity owners; contract reviewers | BFF/Keycloak and EF/PostgreSQL descriptors, authoritative defaults, relational validation, precedence/lifecycle and theme envelope. Public issuer remains distinct from private transport/administration. Sixty-two sync checks include 48 invalid-alias rejections without writes. Actual discovery passes both disposable shapes. | Final-source qualification. Production TLS/proxy/provisioning needs deployment-specific checks. |
| 4. Materialization | Sync and retirement owners; reviewers | Existing preview/digest/apply mechanism; minimal feature-owned API/provider seams, root/nested runtime paths, safe rerun/customization/conflict/removal. Customized independent Sport Feed survives and builds outside selected runtime roots; test probes stay outside production selection. | Final archive/install checks. |
| 5. Maintained verification | Setup/readiness and native-runner owners | Shared authentication/provider fixtures, bounded supervised processes and input-sensitive reuse. **22 setup tests and 43 qualifier contracts pass**. Actual Notes HTTP ownership/conflict/restart checks and Sport xUnit/MTP 4.0.2 pass; skipped native case is rejected. Application transaction, replay and recovery contracts remain application-owned. | Actual Firefox candidate and full gates. |
| 6. Architectural views | Configuration/view owners; orchestrator | Templates, source reference/Mermaid, validated browser allowlist, redacted configured attribution and actual owner-options/DLL provenance. Flattened shell-provider observations and unobserved owners are labeled accurately. | Inspect final generated views. |
| 7. Readiness/product workflow | Readiness, installed-workflow and upgrade owners | Generation, platform readiness and product acceptance remain separate. No implicit services during drafting/hooks. Native tasks/implement replacement plus analyzer append remove the upstream blanket barrier while retaining due security/provider/authority obligations. Nineteen task checks, 29 upgrade contracts, actual 512-entry installation and failed-activation/recovery/retry pass. | Rebuild and inspect final Release archives. |
| 8. Migration/performance | Disposable qualification owners; fresh reviewers | Notes and nested Sport migrations preserve synthetic data, locks, accepted history/custom settings and independent features. Both author zero generic harness lines and retain zero generic setup tasks. | Final-source cold/prepared measurements and publication. Live adoption remains a separate consumer action. |

Public Foundation Host is
`ghcr.io/orbyss-io/foundation-host@sha256:d4d74db6c56ef335fe44dc69a2b13b003718d847e9aa61849cdd587d4867306c`.
The selecting profile and 415-source/447-range knowledge were regenerated and qualified together.
Independent Build 0.3.1/exporter 0.2.5 remain pinned; Spec Kit 1.1.3, xUnit/MTP 4.0.2 and Analyzer 0.3.2
are selected. Historical profiles/evidence, native locks and personal skills are preserved.

Current evidence and gates:

- Foundation publication: [public 0.3.2](https://github.com/orbyss-io/dotnet-foundation/releases/tag/v0.3.2).
- Bounded Development: clean `09f3a1d`, tree `6ed02eec9caaeb47fc1bb312e98faebba1509fb3`,
  [journal](../artifacts/validation-runs/20261010T210254Z-153eb7a9/journal.json) passed **87/87** in **656s**;
  root verified all 87 log hashes and clean source before/after. This precedes the final signed-out
  assertion correction. Earlier `7f98b21` remains 86/87 on its obsolete component assertion; the
  repaired full component validator and 20 native/mutation controls pass. Failed evidence is preserved.
- Latest completed targeted [CI 38084938760](https://github.com/orbyss-io/program-kit/actions/runs/38084938760)
  at `862c747`: Linux 2/3, Windows 5/5. All 21 authentication cases were observed with no skips;
  Firefox cross-site denial alone failed after exact POST/Origin/HTTP400 verification because the
  selected driver had no captured response body. Original failures and all eight log hashes are preserved.
- The maintained Firefox renderer correction at `c509c2c` handles `application/problem+json`.
  [Targeted CI 38085908238](https://github.com/orbyss-io/program-kit/actions/runs/38085908238) confirms
  cross-site denial passed; session logout and provider-navigation-failure still failed assertions.
  All 21 cases were observed without skips; Linux 2/3, Windows 5/5. Root verified all eight hashes.
  The next bounded correction verifies the actual signed-out navigation URL, HTTP200, JSON content
  type and typed `{signedOut:true}` response rather than literal display formatting. Session/provider
  assertions remain intact. Source-extracted negative controls and genuine locked-type compilation
  pass fresh review. The actual disposable Notes integration at `296d7c5` passed all 14 Chromium/WebKit
  cases and all five platform checks; owned create/read/isolation/conflict and the same retained resource
  after restart passed. Root verified 104 physical runtime-copy hashes, 44 supervised processes/88 streams
  and 17 unchanged consumer inputs. This functional run establishes no new cold timing or readiness receipt.
  [Targeted CI 38087148676](https://github.com/orbyss-io/program-kit/actions/runs/38087148676) advanced
  to Notes cold readiness but failed before the issuer check; authentication evidence was absent.
  Linux 2/3 and Windows 3/5 remain failures, with all eight journal hashes verified. Initial failures are preserved.
- Local Release preflight PATH repair preserves original command precedence and exact executable
  selection, plus absent/empty/populated environment restoration. Actual PrepareOnly and negative
  controls pass independently. The latest Windows fixture exposed a source-spelling defect: canonicalizing
  relative/8.3 PATH entries changed PowerShell Get-Command Source. The correction emits original spelling
  while normalizing only matching/deduplication; exact executable guards remain. Root and fresh review
  verified canonical/forward-slash/relative/distinct-8.3 cases, actual old-helper failure and fresh PrepareOnly
  with 12 identical executable sources, exact environment restoration and 15 retained Codex metadata entries.
  Remote acceptance remains pending. PrepareOnly starts no Release suite.
- Mandatory complete dependency maintenance (including Firefox and both image scans), full CI,
  final local Release through `Invoke-LocalRelease.ps1 -AuthorizedCodexTask`, and tagged Release/public
  install/upgrade remain required. Earlier full maintenance/CI failures remain failures.
  **The complete plan is not yet achieved.**

Pre-final public 0.3.2 timing observations below precede the final cache/toolchain corrections.
Cold used fresh consumer NuGet/npm/browser acquisition paths; SDK, Docker and immutable images were
preinstalled. Prepared reused the same consumer. These are single observations, not factory-cold
provisioning or statistical speedup claims. Final-source measurements must replace this assessment.

| Shape | Cold / prepared first-product-operation conservative bound | Cold / prepared full workflow |
| --- | ---: | ---: |
| [Base](../artifacts/tests/reusable-foundations/2d18bdbac9fd4971/qualification.json) | No product operation | 129.190 / 79.116s |
| [Notes](../artifacts/tests/reusable-foundations/727cbb21ee984382/qualification.json) | 136.729 / 95.279s | 165.697 / 124.450s |
| [Nested Sport](../artifacts/tests/reusable-foundations/7f6f445253164228/qualification.json) | 149.910 / 107.388s | 189.433 / 148.419s |

The conservative first-operation bound retains wrapper overhead:
`generation + readiness wall clock - (integration elapsed - integration time to first operation)`.
The prototype-derived target is 180s cold / 120s prepared under the stated preinstalled conditions;
final measurements are assessed independently, not as a CI wall-clock gate.

Reviewed functional evidence: [Notes](../artifacts/tests/reusable-foundations/functional-9006e07f9cc74504/qualification.json),
[Sport/MTP](../artifacts/tests/reusable-foundations/functional-9fb120eb71754b9e/qualification.json).
These reruns establish no new cold timing/readiness receipt.
Reviewed migrations: [Notes](../artifacts/tests/reusable-foundations/727cbb21ee984382/notes/migration/result.json),
[Sport](../artifacts/tests/reusable-foundations/7f6f445253164228/sport/migration/result.json).
Installed-workflow evidence: [actual frozen 3d57b30 archives/upgrade/recovery](../artifacts/program-kit-publication/analyzer-alignment-20261010/result-final-native-append.json);
these archives precede later corrections and cannot substitute for final Release assets.

Configuration and adoption:
[templates/envelope](../extensions/program-kit-dotnet/references/foundation-compositions.md),
[generated source reference/Mermaid](../artifacts/tests/reusable-foundations/727cbb21ee984382/notes/consumer/docs/architecture/foundation-configuration.md),
[configured-source view](../artifacts/tests/reusable-foundations/7f6f445253164228/sport/consumer/artifacts/tests/runs/functional-c1a37efadbfe4bef9026492f3653db41/effective-settings.configured.json),
[actual owner-options/provenance view](../artifacts/tests/reusable-foundations/7f6f445253164228/sport/consumer/artifacts/tests/runs/functional-c1a37efadbfe4bef9026492f3653db41/effective-settings.runtime.json),
[adoption](maintenance/reusable-foundation-adoption.md), [0.12.11 migration](../releases/migration-0.12.11.md).

Final qualification uses `python tests/qualify_reusable_foundations.py --shape all --prepared --engines=chromium,webkit`
through the maintained inventory; bounded `--contract-tests` starts no services. Local Firefox remains
the documented Windows-host limitation and CI retains Firefox. No paid coding-agent phase was requested.