# Program Kit release validation follow up implementation plan

Date: 15 October 2026. Audit baseline: `2b21be892719cac1fdcaeb1a9ea1746a1d56c29d`.

Post-release handoff verified on 15 October 2026: local main was fast-forwarded to origin/main at `9274d4b4462ef1b1ca70488a7c1d93242cbf3bbc`. Stable v0.13.2 points to `fff643af3a12b6f7f975106992a792aab2df7cf3`; its [complete Release workflow succeeded](https://github.com/orbyss-io/program-kit/actions/runs/38757467458). The only tracked file changed between the audit baseline and synchronized main is README.md. The earlier active-release hold is satisfied; protect the published release and proceed with an isolated follow-up. Refresh main again when implementation starts.

This follow-up moves deterministic release qualification entirely into CI and makes tagged Release promote the already-qualified artifact set. Local release work consists only of applicable human/device checks and optional, separately authorized AI trials. The follow-up will be pushed directly to main after the separately coordinated release is complete; it will not create a version, tag or publication.

All fifteen interview decisions are settled. This is an implementation plan, not a change to the running release. The supporting [audit](local-release-ci-ownership-audit-2026-10-15.md) and [inventory snapshot](local-release-ci-ownership-checks-2026-10-15.json) preserve the source findings.

## Agreed execution model

| Stage | Responsibility | Evidence |
| --- | --- | --- |
| Ordinary development | Focused local validators and bounded Development; main CI runs Development plus affected expensive checks | Development/affected journals, without a complete qualification claim |
| Candidate qualification | One untagged CI workflow runs the full Linux inventory, required browser engines, focused Windows compatibility and security scan | Complete candidate manifest, original journals/logs, provenance and immutable publication bundle |
| Local readiness | Inspect candidate evidence and change-based trial recommendations; perform only applicable human/device checks | Readiness assessment; a candidate can require no local execution |
| Optional AI trials | Download qualified packages, verify identity, prepare a disposable local consumer and run only individually authorized phases | Local host/preparation record and existing redacted trial evidence, bound to candidate identity |
| Tagged publication | Verify exact-candidate qualification, artifact integrity, readiness disposition and security freshness; attest/publish; check the newly public installation/upgrade | Publication record and public smoke results |

If a complete matching qualification already exists, reuse it. Partial CI runs are not combined into complete acceptance in this patch. A new complete qualification can repeat checks from earlier affected-only CI. Neither the mandatory local gate nor tagged publication repeats the deterministic suite.

## Protect the published release and workspace

1. Preserve the published v0.13.2 source, receipts, tag, assets and run evidence. Do not edit the release chat's worktrees.
2. Planning and handoff preparation change only the audit, inventory snapshot, this plan and the next-session implementation prompt. The initial active-release snapshot has been superseded by the successful workflow verification above.
3. Begin implementation from refreshed post-release main in a separate checkout. Use a named `codex/` development branch for isolation if needed, then deliver the reviewed commits directly to main. Do not switch branches in another active checkout.
4. Reconcile the final release changes before editing workflows or policy. The present branch is codex/diagnostics-repair-batch; it must not be pushed wholesale as this follow-up. Stage only the follow-up's files, including only the new maintenance skill under .agents.
5. The separately coordinated v0.13.2 publication is complete. Before pushing, reconcile any new main commits and verify that the follow-up still preserves the published tag/assets and unrelated work. Do not message or steer the other chat without user authorization.

## 1 Define qualification and ownership contracts

Update `tests/validation-inventory.json` and add a schema-validated `release-policy.json`. Keep one check inventory; execution responsibility and required platform/browser variants become explicit rather than being inferred from the current cost groups.

The policy will identify required Linux checks, Windows compatibility checks, Chromium/Firefox/WebKit coverage, the trusted qualification/security/assessment workflow identities, artifact requirements, and the approved 24-hour default security freshness. Artifact retention is a separate configurable storage setting; retain the current 14-day default initially and reject unavailable/expired handoffs with a clear recovery instruction. Retention never extends security freshness.

Add a versioned portable candidate-qualification schema under `tests/schemas/`. It must bind:

- Exact source commit and tree, VERSION, inventory/policy hashes and schema version.
- Producer repository, workflow identity/revision, run ID and attempt, plus the required successful job variants.
- Actual platform/toolchain/browser observations and required check coverage.
- Original journals and log digests, without rewriting command paths or claiming another host executed them.
- Every publication asset's basename, size and digest; immutable uploaded artifact IDs/digests and build provenance.
- Security observations, scanned immutable image identities, scanner/database details where available, timestamp and linked candidate identity.

Use an acyclic evidence graph. Upload the release payload and its file manifest first; upload the original validation evidence separately. The final qualification manifest then binds those immutable artifact IDs/digests, observed job results and original security evidence. Authenticate and upload that final manifest as separate qualification evidence; it does not contain its own enclosing upload digest. Later security refreshes and readiness assessments reference its stable manifest digest. The original qualification scan binds the already-known source/payload identity, which the final manifest incorporates.

Keep legacy receipts and historical evidence read-only. New portable CI qualification and local execution evidence have distinct schemas and claims. Do not mint a legacy full-local-Release receipt from a reduced run.

Implement the shared contract/verifier in `scripts/release_candidate.py`, using existing dependencies or the standard library. Add any genuinely new external input to maintenance-policy.json; do not trigger unrelated dependency upgrades for this maintenance patch.

## 2 Make ordinary main CI select affected checks

Change `.github/workflows/ci.yml` and the relevant selection helpers in `scripts/run_validation.py`:

- Preserve bounded local Development and existing PR behavior.
- On main pushes, compare the entire push's before/after range, select Development plus affected non-maintenance checks, and expand prerequisites.
- Treat missing/invalid bases, unknown inputs and unsupported diff situations conservatively as full selection. Do not treat a selection failure as successful validation.
- Preserve all three Linux browser engines whenever selected checks require browsers.
- Keep ordinary CI evidence clearly distinct from complete candidate qualification. A targeted or affected run cannot emit a complete qualification assertion.

The completion/receipt changes below must not permit manual targeted jobs to advertise full coverage.

## 3 Add complete untagged candidate qualification

Add `.github/workflows/qualify-candidate.yml`, manually invoked by release preparation. It will qualify a trusted main candidate with an expected-commit assertion. The selected checkout, workflow run source and expected candidate must agree; if main advances before dispatch, stop rather than qualifying a different commit silently.

Within one workflow execution:

1. Provision pinned CI tools and schema runtime.
2. Build one authoritative publication artifact set using the existing builder.
3. Run complete Linux deterministic qualification, including packaged installation, upgrades, runtime/service checks and Chromium/Firefox/WebKit. Preserve failures and original logs.
4. Run the focused Windows compatibility lane against the same prepared package bytes.
5. Run the security scan against the immutable published Host identities selected by that candidate.
6. Finalize complete qualification only after every required job succeeds; verify that tested package bytes still match the final asset manifest.
7. Generate build provenance in the producing CI workflow and upload the complete immutable payload, including release/migration Markdown and every asset referenced by indexes/checksums. Publish the separate authenticated qualification evidence only after its payload/validation artifact identities are known, following the acyclic graph above.

Update runner/build orchestration so downstream package checks consume the designated artifact set instead of rebuilding it. Preserve an initial post-build digest inventory and verify it after package checks; a final hash only cannot establish that earlier checks tested unchanged bytes. Changes to build output invalidate qualification.

Adjust `scripts/write_release_receipt.py` and its callers so portable qualification is created during the actual qualifying execution. Preserve the original logs and original per-platform journals; aggregate required jobs from this one workflow, not unrelated partial runs. No receipt-writer-only shortcut.

The qualification workflow produces no public release and invokes no coding agent. A successful Linux job alone cannot finalize qualification while Windows is missing or failed.

## 4 Extend focused Windows compatibility

Declare the agreed Windows contracts explicitly. Start from the existing validators:

| Contract | Candidate validators |
| --- | --- |
| Source/bootstrap installation | source-install; validate_codex_bootstrap |
| CMD, Node/npm, Python/uv and PATH | test_workflow_shell_preflight; validate_js_toolchain; Windows launcher cases in validate_local_upgrade |
| Packaged consumer install and upgrade | validate_release_install; validate_consumer_upgrade_install; candidate-upgrade |
| Native workflow start/resume | validate_workflow_resumption; validate_workflow_runtimes with distinct engine/shell Python |
| Worker permissions and process cleanup | validate_codex_worker_policy; real fixture-child supervision cases in validate_live_bootstrap_acceptance |

Inspect and test prerequisite closure for this lane. Factor a narrowly scoped native fixture out of a larger validator when necessary to keep Linux service/browser acceptance out of Windows compatibility. Do not replace behavioral coverage with phrase checks.

Windows package checks must import and verify the Linux-produced candidate package set. Replace the implicit build-release prerequisite with an explicit verified-artifact preparation dependency for that execution mode. Record it as preparation, not as a Windows build test that did not run. Ensure the test internals also use those artifacts rather than rebuilding independently.

Keep Windows execution sequential where required by the current runner. Paid trials remain outside this lane; fixture subprocesses are deterministic tests. Hosted Windows execution is acceptance evidence only after those jobs actually pass.

## 5 Make tagged Release verify and publish

Replace the full-suite/build invocation in `.github/workflows/release.yml` with the shared candidate verifier and artifact download. Remove qualification-only SDK/Node/Spec Kit/browser setup from this workflow when no remaining publication step requires it.

Resolve a qualifying run for the exact tag commit, from the allowed repository/workflow and event. Reject PR/fork artifacts and name-only or latest-main selection. Verify the run attempt and all mandatory jobs against GitHub metadata as well as authenticated qualification evidence. Attestations must be verified against the expected producer; an arbitrary downloaded JSON success field or checksum file is insufficient.

Before any publication:

- Check tag/VERSION, source commit/tree, inventory/policy compatibility and required variants.
- Verify provenance, the immutable artifact object and the complete extracted file inventory, sizes and hashes. Require hard failure on digest mismatches with the actual pinned download implementation.
- Reject missing, expired, tampered, incomplete or incompatible qualification with a specific pre-tag CI recovery instruction.
- Require fresh security evidence and a candidate-bound readiness disposition that contains no unresolved confirmed product defect.

Publish exactly the qualified assets. Retain existing build provenance and add appropriate publication attestation without claiming tagged Release built the packages. Reverify uploaded/downloaded public asset hashes during public smoke testing.

Retain public installation and upgrade smoke tests: newly published URLs and delivery are a separate boundary. Preserve partial-publication diagnostics and failed-tag recovery safeguards. A same-payload retry may be idempotent; existing assets with different hashes must fail rather than being silently clobbered.

An older qualified candidate remains valid when main advances, provided the tag still points to that exact qualified commit. The historical local-evidence reuse exception does not authorize a source mismatch in this new promotion contract.

## 6 Add scan-only freshness refresh

Add `.github/workflows/refresh-candidate-security.yml`. It takes a verified candidate identity, derives immutable scan targets from that candidate and produces a new authenticated security evidence artifact linked to its manifest digest. It neither rebuilds packages nor runs product tests.

Publication accepts the original qualification scan or a trusted matching refresh if it is within the configured maximum age and remains authoritative. Enumerate applicable trusted candidate-bound scan attempts; a later failed scan cannot be hidden by explicitly choosing an earlier passing artifact. A recorded repair and successful applicable refresh must supersede the failure. Reject future/invalid timestamps, failed scans, wrong targets, wrong candidate bindings and stale evidence. A failed scan identifies the repair and blocks publication. Do not mutate the original qualification bundle to refresh its timestamp.

## 7 Prepare local trials from CI artifacts

Add a release-oriented preparation command to `scripts/release_candidate.py` and adapt `tests/live/v2/candidate.py`, `cli.py`, `trial_candidate.py`, the necessary schemas and PowerShell wrappers.

Preparation downloads/verifies the selected CI candidate, checks the local toolchains and host prerequisites, then installs those exact archives into the disposable trial consumer. It does not run build_release, the complete deterministic suite or a separate deterministic installation acceptance validator. Installing the consumer is necessary trial setup and is recorded as such.

Create a separate local preparation record that references the portable CI qualification digest and records the actual device/toolchains, source identity, package hashes and preparation operations. Do not rewrite an Ubuntu receipt to make it appear to qualify Windows, and do not weaken host binding by deleting the current checks without a replacement.

Preserve one-use authorization, checkpoint identity, worker workspace-write isolation, Windows Job Object cleanup, stream redaction and credentials isolation. Authorization issuance binds both candidate identity and local preparation. No AI phase starts because readiness was requested. Existing development-learning trials remain separately labeled and do not become publication qualification.

## 8 Add predictable repository maintenance readiness

Create `.agents/skills/program-kit-release-readiness/SKILL.md`, scoped to maintaining Program Kit itself. It is not packaged into consumer skills. Use skill-creator validation for the completed skill.

The skill calls deterministic helpers and policy instead of carrying an independent checklist. It will:

1. Establish the candidate and changes since the previous successful release; confirm dependency-maintenance evidence under the existing maintenance workflow.
2. Locate and verify a complete qualifying run. Reuse it when valid; otherwise request one complete CI qualification as part of the authorized readiness task.
3. Check freshness and request only a security refresh when that is the missing condition.
4. Produce a change-based optional trial recommendation with reasons, prerequisites and coverage gaps.
5. Prepare selected release-oriented trials from CI artifacts while leaving paid dispatch to its existing explicit phase authorization.
6. Produce a concrete readiness assessment for review and preserve the exact candidate identity for any later publication authorization.

Use a configurable recommendation map with these initial families:

| Changed behavior | Relevant optional trials |
| --- | --- |
| Intake/bootstrap instructions or workflow handoffs | Bootstrap checkpoint and applicable fresh/failure/resume workflow cases |
| Building-block selection or application instructions | Building-block consumer phase |
| Feature/lifecycle instructions | Applicable intake, planning, plan/tasks, setup or delivery phases |
| Consumer upgrade/migration or continuation instructions | upgrade-consumer, actual governance handoff, then separately authorized upgrade-continuation |
| CI-only qualification/publication plumbing | Deterministic CI and promotion checks; do not recommend an unrelated paid trial automatically |

Do not label an unimplemented scenario as covered. The existing upgrade phases use the active knowledge-application/v3 fixture and have parent-checkpoint/human-governance requirements; recommendation does not bypass those requirements.

Store full trial evidence internally. A versioned readiness assessment records recommendations, the user's selection, actual trial scope/outcomes and unresolved findings. Confirmed product defects block readiness until repaired; harness/inconclusive outcomes receive an explicit disposition without fabricated acceptance. No paid run is required merely because the candidate is being published.

To make the concise assessment available to tagged publication, add a narrow trusted `record-release-assessment.yml` workflow that validates the supplied minimal assessment against the candidate and stores a separate authenticated artifact. Require an attributable human review, exact candidate binding, references/digests for internally retained trial manifests, and explicit provenance of each reported outcome. Authentication proves who recorded the statement; it does not prove an uninspected trial ran or passed. Distinguish verified trial evidence from human-attested findings and do not upgrade submitted JSON into an independently verified acceptance claim.

The assessment workflow performs no tests, package build or paid dispatch. The release body includes the reviewed summary; complete logs/workspaces are not uploaded automatically. Recording assessment information must not create a new candidate commit or alter the qualified asset set. Select the authoritative assessment history for the candidate: a later unresolved confirmed defect invalidates an older readiness pass until an explicit recorded resolution supersedes it. Publication cannot select a favorable older assessment to conceal a newer applicable finding.

## 9 Align commands and documentation

Update AGENTS.md, README, `scripts/Test-ProgramKit.ps1`, `scripts/Invoke-LocalRelease.ps1`, live acceptance/authorization guidance, dependency-maintenance guidance and validation-runner/test-suite contracts together.

- Keep local Development and focused debugging commands available.
- Replace the old mandatory local Release instructions with the CI qualification and local-readiness workflow.
- Make deprecated full-local-Release entry points return actionable guidance rather than silently executing another suite or producing a misleading receipt.
- Describe the new exact-candidate CI receipt and local preparation record separately; retain honest legacy parsing or explicit migration diagnostics for historical formats.
- Preserve Firefox in CI, optional paid-phase authorization, historical evidence and consumer locks.
- Update failed-tag recovery to require valid complete candidate qualification and publication verification, rather than a repeated local suite. Preserve exact corrected-commit/tag approval and partial-publication disclosure.

README and any shipped references changed by the patch are product inputs. This follow-up cannot be treated as a non-shipping correction covered by the ongoing release's receipt. It gets its own commit and CI evidence, without publishing a new version now.

## Validation and completion criteria

Use meaningful fixture-based contract tests for the new boundaries, not assertions that merely repeat implementation text:

1. Main push selection includes the whole push range, affected prerequisites and conservative fallback; targeted runs cannot qualify publication.
2. Required Linux, Windows and browser variants must all be present; no Windows fixture launches a paid agent.
3. Qualification preserves original logs, checks source stability and proves the tested packages remained unchanged.
4. Reject wrong source/tag, wrong repository/workflow/run attempt, failed or incomplete jobs, changed logs/manifests/files, missing assets and expired artifacts.
5. A replaced package plus a replaced checksum file does not bypass producer-provenance verification.
6. Security freshness covers the 24-hour boundary, clock errors, target identity and scan-only refresh without build/test dispatch. Reject selection of an older pass after a newer applicable failure.
7. Tagged publication dispatches no deterministic inventory or builder. Safe fixtures verify the planned publication arguments and reject differing existing public assets; do not create a real tag to test this patch.
8. Release-oriented local preparation uses downloaded hashes, records actual host identity, never dispatches paid work and leaves per-phase authorization enforcement intact.
9. Readiness assessment preserves trial scope, attributable review and outcome provenance; a confirmed product defect prevents readiness; absent or unchecked trial claims never become verified AI acceptance. Reject an older passing assessment after a newer unresolved defect.
10. Missing/invalid legacy evidence produces an honest migration diagnostic, without modifying historical receipts.
11. Validate workflow/schema syntax, the repository-only skill and the affected existing runner, installation, live-harness and suite-policy contracts.
12. Evidence graph tests establish that payload/validation uploads precede final qualification and that authenticated qualification never depends on its own enclosing artifact digest.

During implementation, run focused affected validators and bounded Development locally. Use CI for the full untagged qualification and real Windows/browser coverage. Exercise handoff/verification with that qualification bundle in a non-publishing mode; no tag or public release is necessary to verify promotion decisions. A real publication smoke remains a future release boundary and must not be claimed from the dry verification.

## Delivery order

1. Refresh post-release main, reconcile changes after the handoff baseline and isolate the follow-up checkout.
2. Implement policy/schemas and pure verification contracts first.
3. Implement main selection, complete qualification and Windows artifact consumption.
4. Implement scan refresh, publication verification and assessment handoff.
5. Implement local preparation, maintenance skill and aligned documentation.
6. Complete focused checks and Development; review the diff for accidental version/pin/consumer changes.
7. Push only the follow-up commits directly to main. Inspect exact-commit main CI, then invoke one untagged complete qualification for the new mechanism and exercise its non-publishing verifier.
8. Repair any failures and obtain evidence for the corrected commit. Do not tag, publish, move an existing tag or advertise a new available version as part of this follow-up.

Deferred scope: reuse of individual checks across separate CI runs, AI/API execution in Actions, mandatory paid acceptance, automatic publication of detailed trial evidence, and unrelated dependency/product changes.
