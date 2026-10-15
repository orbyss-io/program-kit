# Local Release and CI validation ownership audit

Date: 15 October 2026. Source reviewed: `2b21be892719cac1fdcaeb1a9ea1746a1d56c29d`.

The requested follow-up is a direct push to main after the separate release effort, with no new tag or publication. This report proposes the validation boundary for that follow-up; it does not change the current release candidate or its acceptance policy.

## Findings

The current local Release gate repeats a complete deterministic inventory that CI can execute. All **141 Windows local Release check IDs** have a CI execution route: **140** in the tagged Ubuntu Release job and the Windows-only **source-install** check in ordinary Windows CI. None of these checks is an actual paid coding-agent trial.

That establishes overlap by check ID, not equivalent coverage on every host. Local Release also exercises Windows variants of checks that mostly run only on Linux in CI. Removing local execution requires an explicit Windows coverage policy. A green main push is also insufficient evidence of the complete deterministic inventory: ordinary main pushes run Development.

The recommended boundary is:

- CI owns deterministic source, migration, package, restore, runtime, browser, security and publication validation, with explicit required operating-system coverage.
- Local acceptance covers human interaction, the user's actual installed environment and explicitly authorized coding-agent trials. It may have no required work for a particular candidate.
- Candidate preparation for a local trial is evidence preparation, with narrowly scoped claims. It should not force a second complete deterministic acceptance run.
- Paid trials remain separately authorized. Making them mandatory for publication would be a separate policy decision.

## Current execution map

The inventory contains 142 entries. Its groups describe cost and execution layers, rather than local versus CI ownership.

| Inventory group | Entries | Windows Release | Linux Release | Present route in CI |
| --- | ---: | ---: | ---: | --- |
| development | 101 | 101 | 101 | Main pushes; PRs; manual full CI; tagged Release |
| release | 26 | 26 | 25 | Tagged Release; eligible PR/manual checks; source-install separately in Windows CI |
| integration | 6 | 6 | 6 | Tagged Release; eligible PR/manual checks |
| package | 7 | 7 | 7 | Tagged Release; eligible PR/manual checks |
| registry | 1 | 1 | 1 | Tagged Release; eligible PR/manual checks |
| maintenance | 1 | 0 | 0 | Separate Maintenance selection; excluded from Release |
| **Total Release** | | **141** | **140** | |

The separate maintenance entry is `legacy-public`, the historical NuGet availability verifier. It is not an extra local Release obligation.

Evidence: [inventory](../../tests/validation-inventory.json), [selection logic](../../scripts/run_validation.py), lines 37–62. The accompanying [check ownership data](local-release-ci-ownership-checks-2026-10-15.json) records every inventory entry, command, prerequisite and platform declaration.

| Entry point | Actual selection | Evidence and limits |
| --- | --- | --- |
| Local Test-ProgramKit Development | 101 Development checks | Bounded development policy; focused validators also remain available |
| Local Test-ProgramKit Release | All 141 non-maintenance Windows checks; normally Chromium and WebKit here | Complete local transcript, per-check journals and Release receipt; requires publication approval |
| Main push CI | 101 Development checks on Ubuntu, plus narrow Windows job | Does not run all expensive checks automatically |
| PR CI | Development plus affected non-maintenance checks and prerequisites on Ubuntu | Unknown changed paths conservatively select full coverage; known inputs can select less |
| Manual CI full | All 140 non-maintenance Linux checks, plus Windows job | Already provides a way to execute the complete Linux inventory before tagging; no Release receipt |
| Tagged Release | All 140 Linux checks with Chromium, Firefox and WebKit | Writes its own exact-source receipt before attestation and GitHub asset publication |
| Dependency update workflow | Full unfiltered PullRequest selection, plus update qualification and security work | Dependency preparation and qualification remain a separate maintenance responsibility |

Evidence: [PowerShell entry point](../../scripts/Test-ProgramKit.ps1), lines 119–124; [CI](../../.github/workflows/ci.yml), lines 73–89 and 117–162; [Release](../../.github/workflows/release.yml), lines 42–75; [dependency updater](../../scripts/update_dependencies.py), lines 45–54.

The tagged workflow has one Ubuntu job. It does not itself wait on an exact-candidate Windows CI job. Existing CI routes demonstrate that tests can run in CI; they do not establish that all required variants passed for a specific candidate. External branch or environment protection settings were not audited.

## Migration and AI are separate test dimensions

Migration involves AI only when the test actually asks an agent to reason about or edit a consumer. Installation, upgrade preservation, schema migration, retained product data and workflow continuation can all be tested with predetermined inputs and real deterministic execution.

| Current coverage | What it actually does | Proposed owner |
| --- | --- | --- |
| validate_consumer_upgrade | Exercises migration state, evidence, condition handling, pending work and preservation in disposable fixtures | CI |
| validate_phase_refresh and validate_native_phase_ownership | Uses native installed skills and fictional retained phase artifacts; checks managed ownership and customization refusal | CI, including selected Windows variants |
| validate_local_upgrade | Exercises the actual local/offline updater and installation metadata, including pending migration verification | CI; “local” describes the installation path |
| validate_consumer_upgrade_install and candidate-upgrade | Tests packaged candidate installation and upgrade from previous releases | CI |
| qualify_reusable_foundations | Creates base, Notes and Sport fixtures; runs real cold/prepared setup and product operations, then retained-data migrations for Notes and Sport | CI |
| validate_installed_bootstrap_flow | Runs all shipped bootstrap steps with real shell validators and fictional authoring/review dispatch | CI; establishes mechanical workflow composition |
| validate_codex_bootstrap and validate_codex_worker_policy | Tests integration boundaries, preflight and guarded worker contracts | CI; does not establish an agent followed the instructions |
| validate_live_bootstrap_acceptance, validate_live_workflow_acceptance and validate_live_trial_candidate | Tests the live harness, authorization, checkpoints and failure behavior with fixtures/mocks | CI; names do not make these paid trials |
| Actual live v2 phases | Starts real Codex sessions under an exact one-use authorization, then preserves and validates their output | Local, explicitly requested |

The expensive reusable-foundation qualifier is particularly relevant: `qualify()` invokes foundation_setup; `migrate()` invokes foundation_qualification with `--migration --product`; `main()` selects the three preauthored shapes. These are real compiler, service, browser and data checks. They do not need a model to author the fixture during the test.

Evidence: [reusable foundations](../../tests/qualify_reusable_foundations.py), lines 1267–1329 and 1523–1537; [installed bootstrap](../../tests/validate_installed_bootstrap_flow.py), lines 1–4 and 83–119; [consumer upgrade](../../tests/validate_consumer_upgrade.py); [local upgrade](../../tests/validate_local_upgrade.py), lines 882–894.

The inspected suite does not establish that an arbitrary agent can successfully migrate an arbitrary existing consumer. That is a different acceptance claim. Actual paid upgrade-consumer and upgrade-continuation phases do exist in [sync_stages.py](../../tests/live/v2/sync_stages.py), exposed through [Test-LiveRepositorySync.ps1](../../scripts/Test-LiveRepositorySync.ps1). The active fixture is knowledge-application/v3. The upgrade stage invokes the real updater and a sandboxed coding worker, applies its oracle, and can remain inconclusive pending actual human governance confirmation. Continuation requires its own authorization and confirmed checkpoint. Implementation of those phases is not evidence that a particular candidate passed them; other migration claims need a matching scenario and oracle.

## What belongs locally

| Local concern | Why CI does not supply equivalent evidence today | Scope |
| --- | --- | --- |
| Real coding-agent behavior | Current CI deliberately has no paid agent dispatch; live preflight rejects CI | Actual reasoning, implementation and conformance within supported scenarios |
| Human intake and review | A fictional approval does not establish a human understood or accepted a decision | Start-IntakeSession is foreground human-owned interaction; PrepareOnly is deterministic setup |
| The user's installed environment | Hosted runners cannot establish this device's PATH, login, terminal behavior, Docker Desktop state or installed tool selection | Focused environment diagnostics and reproductions; not a reason to repeat all product tests |
| An explicitly identified manual usability check | A human observation can provide evidence beyond a mechanical assertion | Define the journey and recorded result before treating it as an acceptance obligation |

Windows process cleanup, permission fixtures, mixed Python execution and command launcher behavior are not inherently local-only. CI already tests some on windows-latest. Interactive Desktop experience and this particular user's machine remain distinct from those reproducible Windows tests.

Firefox is a known local host limitation. It remains required in CI; no local retry or production workaround is justified.

Evidence: [live preflight](../../tests/live/v2/cli.py), lines 158–175; [human intake](../../scripts/Start-IntakeSession.ps1), lines 11–21 and 37–51; [CI Windows fixtures](../../.github/workflows/ci.yml), lines 126–162; [contributor policy](../../AGENTS.md).

## Couplings that a patch must address

### Windows coverage

The full Windows run provides additional host coverage even though its IDs overlap Linux CI. Keep a deliberate Windows compatibility lane in CI and select checks by actual platform risk: initializer/source and packaged install, local upgrade, PATH/shims, native workflow run/resume, mixed Python, process supervision and filesystem semantics. Determine whether any remaining runtime contract needs both operating systems before removing its local Windows obligation.

This is a proposed focused lane, not an assertion that all 141 checks need duplication on both operating systems. Current inventory platform declarations alone do not decide which variants are acceptance requirements.

Concrete Windows candidates are source-install, validate_codex_bootstrap, test_workflow_shell_preflight, validate_js_toolchain, validate_local_upgrade, validate_release_install, validate_consumer_upgrade_install, candidate-upgrade, validate_workflow_resumption, the existing mixed-Python workflow-runtimes variant, validate_codex_worker_policy and supervised fixture cases in validate_live_bootstrap_acceptance. Some contain branches skipped on Linux, including CMD launchers and the uv launcher bridge. Coverage selection must inspect each prerequisite and isolate appropriate Windows fixtures rather than assuming hosted Windows can run the Linux Docker service images used by broader qualifiers.

### Receipt and live preparation

The Release receipt writer requires the exact complete platform inventory and hashed execution logs. A reduced local run cannot retain the status `release-validation-passed`. Historical receipts must remain unchanged.

Actual live receipt consumption also binds source commit/tree, host system/release/machine and toolchains. Downloading an Ubuntu CI receipt and presenting it as Windows local qualification will fail that contract. Replacing the local Release dependency therefore needs an honest local preparation receipt, or a separately designed CI artifact identity plus local readiness contract.

There is already a narrower development-trial receipt: components, schema runtime, build and packaged installation, with preserved logs and archive hashes. It explicitly records `releaseValidationPassed: false`. This is a useful existing mechanism, but it still repeats some deterministic setup locally. Under a strict zero-duplicate-execution policy, decide whether local preparation can verify downloaded CI-built packages instead. Build/install steps needed to create the trial workspace must be distinguished from requiring another acceptance run.

Evidence: [journal validation](../../scripts/run_validation.py), lines 159–178; [receipt writer](../../scripts/write_release_receipt.py), lines 123–158; [candidate receipt dispatch](../../tests/live/v2/candidate.py), lines 35–69; [trial preparation](../../tests/live/v2/trial_candidate.py), lines 15 and 52–94.

### CI evidence for direct pushes and publication

A direct main push currently runs Development. The agreed follow-up should automatically run affected deterministic coverage on main. Complete deterministic qualification belongs before publication in CI, including the Firefox leg. The tagged workflow should consume qualifying evidence rather than repeat that qualification; the exact completeness contract remains an interview decision.

Bind acceptance to an exact commit, required check IDs and variants, workflow identity, artifact hashes and recorded results. A successful unrelated main run is insufficient. Publication automation can subsequently update README on main, so the current main SHA is not always the tag SHA.

The current tagged workflow scans the selected published Host, validates, attests, publishes GitHub assets, then tests public installation/upgrade. Pre-publication candidate upgrade and post-publication public upgrade protect different boundaries. The latter can fail after assets are public and must retain the existing recovery disclosure. The inspected checkout does not contain the downstream reusable NuGet/host publication jobs described in contributor policy; do not infer those jobs from the policy text.

### Tagged Release currently repeats CI qualification

Verified again during the second interview round: release.yml line 75 invokes `run_validation.py --suite Release --approved --receipt --workers 4 --engines=chromium,firefox,webkit`. The selection logic includes all 140 non-maintenance Linux inventory entries. That includes the same 101 Development checks scheduled on every main push, and the same full Linux check set available through manual full CI. PR overlap depends on affected selection.

There is no prior-run artifact download, qualification lookup or successful exact-candidate CI dependency in this workflow. Its inventory invocation builds release archives again through the build-release check. The current tagged run therefore repeats testing and packaging; it does not promote an existing qualified artifact set.

The user approved making tagging a publication operation that verifies its prerequisites and consumes prior complete CI qualification for the candidate. The packages published must be the already-built and tested bytes. Current journal validation requires a complete run; any future cross-run aggregation would need an explicit evidence contract, rather than treating affected coverage alone as complete acceptance.

CI's current artifact upload list is not a complete publication handoff: it includes JSON, archives, launchers and checksums, but does not include the generated release/migration Markdown assets required by publication. Its 14-day retention is also a constraint for later promotion. An explicit handoff must inventory every release asset and its hash, identify the trusted run and source, and handle unavailable or expired evidence without silently rebuilding or claiming qualification.

### Artifact handoff and integrity

GitHub Actions supports uploading workflow artifacts and downloading them in a later workflow by run identifier with an appropriately scoped token. This supplies the requested CI-to-tagged-publication handoff. Artifact IDs identify immutable uploaded objects; selecting by a reused display name or merely taking the latest successful main run would not establish the required candidate identity. See [GitHub artifact sharing](https://docs.github.com/en/actions/tutorials/store-and-share-data) and the [official download action](https://github.com/actions/download-artifact).

The publication verifier must establish all of the following together:

- The artifact came from the expected repository and trusted qualification workflow, run and attempt, with all mandatory qualification jobs successful.
- The verified producer provenance and qualification evidence identify the exact commit and source tree resolved by the tag; VERSION agrees with the tag.
- The complete artifact inventory and file hashes match the authenticated qualification manifest and downloaded payload. No rebuilding, regeneration or file substitution occurs during promotion.
- Required operating-system/browser evidence and applicable freshness rules are satisfied before any asset is published.

A checksum detects changed bytes relative to an expected digest. It does not authenticate an attacker-supplied checksum file. Producer identity and provenance must therefore be verified as well. Attestation establishes origin; successful complete qualification still needs its own authenticated evidence. See [GitHub attestation verification](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations).

GitHub's artifact-sharing tutorial describes download digest mismatches as warnings; the newer official download action documents an error default and a digest-mismatch setting. Verify the actual pinned implementation and require hard failure explicitly. Do not rely on a version-dependent default or emit a warning and continue publication.

Main advancing after qualification does not itself invalidate a deliberately selected older candidate. A tag resolving to a different commit from its qualification does. The agreed exact-candidate promotion boundary must not be confused with the historical exception for reusing local evidence after non-shipping corrections.

### AI trial selection and attached evidence

The user confirmed that actual AI trials remain optional and that the chosen trials should depend on the changes being released. Changes to migration instructions, for example, motivate an agent-driven migration scenario; deterministic migration assertions alone do not establish that an agent can follow those instructions. Recommendations should identify any scenario that does not yet exist rather than treating another trial as equivalent coverage.

The agreed public output is a concise assessment rather than full AI-trial evidence. The current workflow does not attach trial evidence: neither its attestation asset list nor its published asset list includes the live harness's run manifests, checkpoint/object store or a portable live-trial evidence bundle. The harness preserves local evidence, and release receipts bind deterministic qualification; neither automatically attaches AI trial outcomes to GitHub release assets.

The user approved preserving full evidence internally and including a concise release assessment stating which trials ran, their relevant scope, outcomes and unresolved findings. Automatically publishing worker logs and checkpoints adds little consumer value relative to that assessment. Public evidence bundles remain available when specifically requested. The assessment is supplemental release information; appending it must not mutate the already-qualified package bytes or silently replace hashed release assets.

The user approved change-based trial recommendations and explicit selection. A repository-only program-kit-release-readiness skill should orchestrate maintenance preparation, CI qualification discovery, change assessment and trial recommendations. Shared configuration and deterministic verification scripts should enforce the CI/publication contracts; prose in a skill alone cannot make them enforceable. The skill must preserve individual paid-phase authorization and publication authority, and remain outside the shipped consumer skills. Its implementation follows the completed interview.

Every reported outcome must bind to the tested candidate and artifact set. Optional trials must not be described as passed when they were not run. The user approved that confirmed product defects discovered by optional trials block readiness until repaired, while harness failures and inconclusive results receive an explicit assessment. Those outcomes must not disappear from the release record.

### Accepted publication freshness and failure behavior

Missing, expired, incomplete or mismatched qualifying artifacts stop publication. The verifier identifies the CI qualification needed; tagged Release does not silently rebuild or run acceptance tests as a recovery path.

Security evidence has a configurable default maximum age of 24 hours at publication. When stale, refresh the security scan in CI against the unchanged candidate inputs. That refresh does not require another deterministic product test run or new package bytes. The freshness rule is distinct from CI artifact storage retention, which governs whether the verified handoff remains available.

The Windows lane will cover installation/upgrades, CMD/Node/Python launchers and PATH, native workflow start/resume, and worker permissions/cleanup. Browser and container integration acceptance remains in Linux CI. CI must exercise those native Windows contracts, rather than reporting the Linux checks under Windows labels.

### Accepted qualification scope

The current runner has no import/resume mechanism for successful checks from another CI run. Its journal compares literal machine-specific executable paths and records less environment identity than a robust reusable per-check cache would require. Some prerequisites also create runtime state, such as an installed browser harness, that is not transferred by the existing artifact uploads. Importing a success result would not restore that state. See [runner](../../scripts/run_validation.py), lines 66–85, 118–121, 159–177 and 222–228, and [browser launch test](../../tests/validate_browser_launch.py), lines 24–36.

The user approved one complete untagged candidate qualification in CI for this first patch, producing a complete immutable artifact bundle and the required Linux/Windows evidence. Reuse an already-successful complete matching qualification rather than requesting another. Ordinary main pushes remain affected checks plus Development. When only partial CI evidence exists, the complete candidate qualification can repeat some earlier CI checks. There is no mandatory local repetition and no deterministic suite rerun during tagged publication.

Eliminating repetition between separate partial CI runs would require a new versioned evidence-composition and prerequisite-state contract; the user approved deferring it. Release-oriented local trials will download the qualified CI packages and produce separate local host-readiness and trial evidence. Existing development-learning trials retain their separate scope.

Evidence: [tagged Release](../../.github/workflows/release.yml), lines 42–75 and 85–131; [published README update](../../.github/workflows/published-readme.yml), lines 26–42.

### Documentation and tests

Changing only Test-ProgramKit would leave contradictory instructions and receipt assumptions. Review AGENTS.md, README, Invoke-LocalRelease, run_validation selection/authority and journal contracts, receipt schemas/writers/consumers, live authorization and preparation guidance, dependency update guidance, and validation-runner/test-suite tests together. README and shipped references are packaging inputs; their changes are product changes for the current evidence-reuse policy.

This report and its data appendix are under docs/reviews, outside the bundle root/source/runtime script allowlists in [build_release.py](../../scripts/build_release.py), lines 21–44. They are not a release-policy implementation.

## Proposed follow-up and verification

1. Settle the interview decisions below, then write the exact ownership and evidence contracts.
2. Keep one inventory. Declare execution environments and required variants separately from cost groups. A local acceptance selector must not transitively pull the complete deterministic suite back in through prerequisites.
3. Preserve CI deterministic coverage, add the agreed Windows compatibility coverage and choose the direct-main qualification route. Keep paid agents and API/Actions integration out of scope.
4. Introduce or adapt honest local trial preparation evidence. Preserve exact one-use authorization, checkpoints, sandboxing, credentials isolation, cleanup and redacted evidence.
5. Align commands, schemas, policy and documentation. Test selection/closure, missing variants, stale source/artifacts, tampered logs, failed checks and refusal to label partial evidence as full acceptance.
6. Use focused relevant validators and bounded Development for the patch. Inspect the new exact-commit CI results before declaring it qualified. Push the agreed follow-up directly to main after reconciling the separately coordinated release work; do not tag or publish it.

This audit used source inspection, inventory enumeration, existing evidence inspection and official GitHub documentation for the artifact handoff. It did not execute Release, start a live acceptance worker, invoke registry operations, change runtime code, or measure projected runtime savings. Scheduling in a workflow is not a claim that the latest candidate has passed it.

## Interview decision tree

The user has already established that CI-capable acceptance should not be mandatory locally, this follow-up will not be released, and adding model/API execution to Actions is out of scope.

The user answered yes to all four questions in round one:

1. A candidate can require no local acceptance run when no specific local concern applies.
2. CI will preserve necessary Windows coverage in a focused lane.
3. Actual AI trials remain optional and individually authorized.
4. Direct main pushes will select affected expensive deterministic checks and prerequisites as well as Development.

The user additionally established that optional AI trials must be chosen in light of the actual changes and that tagged publication should not repeat CI qualification.

Round two settled Q5 through Q8: publish the tested CI-built bytes, require complete CI qualification before tagging, retain publication-specific integrity/attestation/public-download checks, and recommend AI trials based on changes with explicit user selection. The user also authorized a helpful repository-only release-readiness skill.

Round three settled revised Q9 through Q13: keep full trial evidence internally with a concise public release assessment; stop publication on missing/expired/incomplete/mismatched qualification; cover the stated Windows contracts in CI; enforce a configurable 24-hour security scan freshness default with scan-only CI refresh; and block readiness on confirmed product defects found by optional trials while assessing inconclusive/harness outcomes explicitly.

Round four settled Q14 and Q15: reuse complete matching CI qualifications, run one full untagged candidate qualification when necessary, defer cross-run per-check reuse, and prepare release-oriented local trials from the exact qualified CI packages without rebuilding or repeating acceptance. The user then requested the [concrete implementation plan](release-validation-follow-up-implementation-plan-2026-10-15.md), keeping it separate from the active release. All interview policy decisions are settled; this turn changes planning documents only.
