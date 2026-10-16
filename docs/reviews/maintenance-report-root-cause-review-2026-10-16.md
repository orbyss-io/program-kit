# Program Kit maintenance report root cause review

Prepared 16 October 2026 against main `02d772cecb064a96f6755637fbd1950eca8fb647`. The published 0.13.2 baseline is `fff643af3a12b6f7f975106992a792aab2df7cf3`. This is research for the repair interview; it is not an approved implementation plan or a release-readiness assessment.

The report identifies real Program Kit defects, but its local remedies should not be adopted wholesale. Several repairs are incomplete, several explanations remain hypotheses, and some successful checks prove narrower properties than the report implies. The largest effectiveness gap is that a supported configuration does not produce a complete, centrally proven browser identity and exception journey. Documentation currently leaves essential integration to each consumer.

## Evidence and current state

The checkout was fast-forwarded from `9274d4b` to the already-pushed main `02d772c`. Four untracked review documents were preserved byte-for-byte under `artifacts/maintenance-research-2026-10-16/pre-sync-local-files`; unrelated untracked skills remain intact. No production repair was made during this review.

The supplied report matches the locally available sanitized packet's report, SHA-256 `5d8a9f16325d2d9e1d44e04d6de6f910f44752ce77323a2ff16e5281666612b8`. All 73 packet entries matched the manifest's sizes and SHA-256 values. The manifest SHA-256 is `5bc3ab231fd8df9f6e4376dd552b5330359ffc6331b97cb96f722011101c1849`. A research snapshot is retained at `artifacts/maintenance-research-2026-10-16/consumer-packet`.

Packet integrity establishes which sanitized sources were reviewed; it does not authenticate the packet as publisher evidence. The packet builder normalizes text/BOM/newlines and replaces the consumer root. Its `sources[].sourceSha256` describes original source bytes; sanitized-file hashes can therefore differ from local repair witness hashes. Original receipts must remain unchanged.

The author subsequently supplied a newer packet: 77 manifest-listed entries, 78 files including the manifest. Every listed entry was verified again; manifest SHA-256 is `b27a73f7cef1bbdd47f7a6f5831bbc6da8c4ad4967fa4bbc95cddffa86d57620`. The second snapshot is `artifacts/maintenance-research-2026-10-16/consumer-packet-latest`. It adds four Docker-reset recovery sources/records and updates the report/check summary. Both snapshots are preserved. The author's read-only handoff confirmed the logout omission and withdrew R7's original causal claim. It also confirmed that DS01/US1 is now human-approved and that no consumer repair was made for this investigation; the original report's pending-review status belongs to its earlier checkpoint.

Evidence labels below distinguish independently reproduced failures, source-confirmed behavior, reported runtime observations, and unproven causal attribution. The packet omits some original failing consumer sources and raw execution logs. An absence of those originals does not make a reported failure false, but it limits claims about exactly who introduced it and why.

Current CI qualification is owned by the untagged candidate workflow. Tagged Release promotes authenticated qualified artifacts and verifies public installation/upgrade. The new mechanism's non-publishing verifier previously passed; an actual tagged publication through that mechanism remains a future boundary. This review requests no publication, tag change, dependency upgrade, paid run, or consumer implementation.

## Standard sign in sign out and exception journeys

The user's clarified product requirement is settled: for supported standard journeys, the consumer declares configuration and branding and receives working pages. Program Kit and the relevant publisher own reusable implementation and proof. Each consumer should not have to recreate presentation writers or repeat shared framework tests.

### The immediate sign out failure

The consumer's `web/src/app.ts:40` calls `beginFoundationBffLogout({ onDispatched: ... })` without a `signedOutPath`. Its temporary in-memory signed-out message is then replaced by navigation. The shipped helper makes that option optional and defaults to `/bff/signed-out`, a native JSON protocol endpoint:

- `extensions/program-kit-dotnet/templates/dotnet/web-profiles/bff-cookie/eng/web/bff-session.ts:15` declares the optional argument.
- The same file at line 86 supplies the machine endpoint default; line 141 calls `window.location.assign`.
- The BFF contract deliberately declares `/bff/signed-out` as JSON in `web-profiles/bff-cookie/eng/web/web-contract.json:81`.

The screenshot is consistent with this exact source path. Changing the native JSON contract into HTML or shadowing its route would be the wrong repair.

### Why the supported composition did not prevent it

This is more than a missed consumer argument:

1. `references/secure-web-profiles.md:408` and `references/implementation-boundaries.md:123` describe the necessary application-owned writer, public session page, recovery module, explicit helper destination, and native `Foundation:Web:LogoutLandingPath` setting. They require manual integration rather than supplying the promised configured result.
2. `scripts/composition_model.py:254` restricts shell settings to four integer timeout/session options. It rejects `LogoutLandingPath`. `scripts/foundation_composition.py:317` starts from native defaults, and `scripts/composition_render.py:183` uses that renderer. The principal composition input cannot express the documented landing selection.
3. `scripts/foundation_composition.py:446` generates an HTTP feature with empty service/endpoint methods. It does not install a complete recovery/public presentation mechanism.
4. Central `web-profiles/common/eng/web/tests/authentication.spec.ts:33` constructs fictional owner pages and serves them with `context.route`. The tests exercise real protocol calls and the shared adapter, but supply the integration that the generated consumer lacks.
5. The consumer's `web/tests/policy-create.spec.ts:45` uses an API POST to terminate a session, then tests expired private-form recovery. That is useful behavior, but it never proves the actual Sign out button's destination. Adding this missing consumer test would expose the symptom without solving the shared product gap.

The standard presentation mechanism should be centrally maintained and selected from typed browser-auth configuration. Its branding, public routes, recovery asset, local return paths, provider theme and native settings must be rendered together. The agent should receive a concrete configured capability rather than a reminder to invent one. Typed selection should drive applicable guidance; prose proximity in `feature_context.py:205` is insufficient authority for a standard obligation.

Central acceptance must install/render the actual composition and use its real controls and served pages. Cover successful sign-in and sign-out, expired/invalid callback, denied access, provider outage, local termination with uncertain provider completion, reload, back/forward privacy, keyboard/focus, public asset availability, safe browser exceptions, and preserved API JSON. The exact division between publisher runtime capability and Program Kit integration is a design decision for the interview. An authentication-error writer alone does not cover all general application exceptions.

The implementation author confirms that the selected settings contract itself described the machine acknowledgement and required a public application landing. The guidance was available but was not applied. The shared `bff-session.spec.ts:93` explicitly expected the machine destination. Sign-in used the themed Keycloak page; dedicated anonymous sign-out/exception presentation was neither implemented nor verified. This establishes an agent integration omission alongside the upstream incomplete-default/configuration/qualification design. It does not establish a failure of the native logout protocol.

## Updater findings

### U0 Dirty baseline and same version repair witnesses

Dirty-source isolation rejection and demand for authentic same-version witnesses are functioning safeguards. A dirty working tree is not permission to commit unrelated work, manufacture provenance, or treat local patches as publisher originals. A supported resumable direct update can be appropriate, but the report explicitly does not establish isolated integration/destination activation.

The generic repair need is an inspectable recovery path that preserves authored changes and distinguishes authenticated public originals from declared local deviations. Whether to extend isolated staging to dirty sources is a separate scope decision. Do not silently broaden it merely to make this case proceed.

The local witness helper hashes staged component bytes but does not independently authenticate the complete staged public release before assigning its public commit identity. It therefore depends on the caller's separately verified public input. Generate canonical component witnesses during release packaging instead of requiring consumers to construct them.

### U1 Previous completed receipt during retry

Confirmed missing retry transition. A prior completed receipt can legitimately describe the original installation while an interrupted new update has already advanced components. Current `scripts/upgrade_program_kit.py:1306` checks migration provenance without admitting that narrowly verified prior state in the retry context. The consumer's targeted admission is directionally right if bound to the authentic interrupted attempt, original inputs, exact target fingerprint and required checks.

The local 17-case updater proof is useful, but relies heavily on mocked resolution/materialization and does not establish every interrupted installation stage. Proper upstream acceptance should inject interruption after each mutating stage and resume with real generated state, retaining failures and original receipts. Changed/tampered source, target, receipt and checkpoints must still fail.

### U2 Materialized lock advanced by supported sync

Confirmed missing second valid state. `scripts/upgrade_program_kit.py:993` derives building-block preflight using the original producer; a verified supported sync may already have materialized the target plan before interruption. The repair should admit exactly the current target plan under authenticated retry provenance, never any convenient lock with matching versions.

Keep real materialized-state, selected-package, unmanaged-dependency and destination checks. A complete target transition and a corrupt mixed transition need distinct fixtures. This is a state-machine repair, not a stale-lock exception.

Carry an explicit verified recovery context from `prior_attempt` through these checks. A recovered previous-version string should not become an implicit authentication token for future callers. Packet tests mock resolver/materialization auditing, so add real original/target/mixed-state fixtures rather than relying only on verified function-call routing.

### U3 Retired project locks

Renewal currently scans retained locks in `scripts/upgrade_program_kit.py:1105`, including owners whose project was deleted. That can create an impossible renewal demand. However, the consumer patch skips every lock with no sibling project before parsing/qualifying it. This is broader than the report's claim that unverified orphans remain rejected.

Do not adopt that shortcut unchanged. Use authenticated active/retired ownership to distinguish deliberately preserved inactive bytes from unexpected orphan inputs. Verify retired bytes and inactivity; reject tampered, unexplained or newly introduced orphan locks. Test owner removal, multi-project directories, unexpected orphans and unchanged retirement. The packet regression covers an unchanged orphan, not these negative distinctions.

### U4 Restore coverage beyond direct targets

The consumer correctly recognizes that a native restore can cover more than its direct project target. Its union of verified restore subjects and solution members is incomplete, however: native restore also follows project-reference closure. `restore_dependencies.py` already computes recursive subject outputs; the repair should reuse that actual coverage contract.

Keep package-target provenance separate from restore-subject coverage. Test direct providers, solution members and transitive referenced providers, while rejecting unrelated or tampered subjects. Do not infer complete coverage merely because one solution restore passed.

## Phase and tooling defects

| Item | Verified cause and consumer remedy assessment | Proper upstream repair and prevention |
| --- | --- | --- |
| P1 | Independently reproduced `ModuleNotFoundError: composition_model`. `phase_obligations.py:17` adds engineering templates, but schema-v2 `shell_composition.py:15` lazily needs the canonical dotnet script directory. The packet's additional path is a reasonable immediate repair. | Establish one consistent installed adapter bootstrap; test real installed phase commands in isolated processes and unrelated working directories. Shared test-process imports can conceal this defect. |
| P2 | Task drafting calls execution-oriented `literal_edges`; the principal trigger is an existing project whose declared future references have not yet been materialized. `repository_verification.py:366` selects and line 388 checks physical edges; `task_draft.py:366` uses it during drafting. Packet `planning=True` correctly suppresses only the physical check. | Separate planning selection/result from execution evidence. Preserve direction/role/unknown-input checks and execution's physical check. Future external file items still need explicit declared ownership; current `input_owners` reads physical props/targets/items. Planning mode must never become a successful execution receipt. |
| R1 | Independently reproduced PKA020 for selected `xunit.v3` 4.0.2. `test_project.py:23` only recognizes direct `xunit.v3.mtp-v2`. The exact alias repair preserves the selected identity and is appropriate. | Derive supported runner capabilities from qualified identity/version data. Qualify the current default through preview, apply, native restore/build and nonempty test execution. Existing tests use historical runner fixtures. Avoid another disconnected alias/version conditional. |
| R2 | Source-confirmed wrapper bypasses supported Python selection and unconditionally runs `playwright install --with-deps` (`web-profiles/common/eng/Test-Web.ps1:21`, line 47). Packet shared-Python/prepared-cache change is correct in principle. | Verification should consume explicit preparation. Execute wrapper tests with recording executables and verify child runtime/cache selection and absence of acquisition. The packet regressions are string assertions. Missing preparation needs an actionable read-only diagnostic. |
| R3 | Independently reproduced standalone `ModuleNotFoundError: repository_verification`. `task_draft.py:343` and line 366 rely on caller import state. The packet's common helper is a good immediate repair. | Test actual task CLI verification/finalization and existing-evidence paths in fresh subprocesses. Packet subprocess tests invoke a function via `-c`, which is narrower. Share the canonical adapter loader with P1. |
| R5 | Independently reproduced generated `eng/tool/obj/T.csproj.nuget.g.props` entering authored source inventory. `handoff_contract.py:905` filters generated src directories while line 912 does not apply the same exclusion to eng. | Apply consistent authored/generated classification while retaining explicit assets/lock observations. Test real architecture-build then pack, authored props drift, generated props/targets and restore state. Sequential execution mitigates timing but does not fix classification. Inspect actual build inputs: the suffix allowlist also omits engineering C#/project files, so do not claim complete engineering-source coverage without a closure audit. |
| R8 | Independently reproduced real wrapper exit 0 with JSON followed by a summary; parsing all stdout fails with `Extra data`. `Invoke-RepositoryVerification.ps1:162` unconditionally prints the summary. Packet `if (-not $Plan)` is correct. | Parse the complete actual subprocess stdout for native and scoped-adapter Plan paths. Existing forwarding-marker tests do not test output. Keep diagnostics/failures distinct and nonzero. |

The selected xUnit alias is supported by the publisher: MTP v2 is the default for xUnit package versions 4.0.0 onward. This supports exact 4.0.2 qualification, not accepting arbitrary future runners. [Official xUnit MTP documentation](https://xunit.net/docs/getting-started/v3/microsoft-testing-platform).

The report's phrase “exact qualified runner table” is inaccurate: current canonical `xunit.v3.mtp-v2` admission is based on package identity plus selected pin, not a comprehensive version table. Preserve this distinction when designing the repair.

## Consumer helper repairs needing stronger boundaries

### R4 Schema deployment and runtime identity

The initial permission failure is plausible and the corrected disposable host reportedly activated. Nevertheless, deployment as the application role is not the general production repair. Shipped `references/persistence-profiles.md:3` separates administrator deployment from minimum runtime privileges and read-only admission checks.

Packet `eng/policy_schema.py:20` constrains synthetic target/roles, but its “exact three objects” claim is too broad: it inspects only table relations, ignoring other schema object kinds. Inspection and ownership alteration run in separate processes, leaving a check/use race. Its mocked regressions establish dispatch guards, not PostgreSQL ownership semantics or atomic safety under concurrent mutation.

A maintained deployment adapter should distinguish deployment and application identities, apply narrow grants, and verify admission with the real runtime connection. An application-owner mode can be explicit for disposable fixtures. Any ownership repair needs complete declared-object admission and a transaction/locking strategy adequate to preserve its checked assumptions. Do not promote the local empty-synthetic helper into a live migration facility.

### R6 Concurrent fixture preparation

The process-local semaphore is a reasonable repair for multiple classes sharing one owned fixture in one test process. It serializes migration DDL while preserving product-operation concurrency. It is not a database-wide or multi-process coordination mechanism.

The six-concurrent regression does not independently establish that the schema is absent at its start. If another test created it first, the regression can pass without reproducing the original catalog-creation race. Central reusable fixture setup should deploy once before parallel consumers, or use separate fixture schemas. Prove the fresh initial state and retain cleanup identity. Do not disable all test parallelism.

### R7 Viewport evidence and withdrawn diagnosis

Copying the configured viewport and asserting actual dimensions is useful evidence. It does not prove the original helper discarded project options. Playwright documents option inheritance for contexts created through the test-runner instance, including the built-in browser fixture. [Official context option inheritance](https://playwright.dev/docs/test-use-options#explicit-context-creation-and-option-inheritance).

The original packet shows a helper receiving a Playwright `Browser`. The author subsequently confirmed it was the test-runner browser fixture and that there was no original dimension measurement or contrary version-specific reproduction. The original defect diagnosis is withdrawn. The new assertions improve measured assurance; they do not establish that earlier runs used the wrong viewport. Do not ship a false rule that every manual `newContext` ignores project configuration.

### R9 Shared suite drift and incomplete coverage identity

Replacing deleted product fixtures with generic maintained fixtures is reasonable if each replacement preserves the original obligation. The reported 166 passing cases and native bridge establish execution, not that every old obligation survived.

Packet `eng/shared_engineering_tests.py:5` uses a minimum count of 126 and rejects skips/failures. An independent research probe supplied 126 unrelated passing cases, using none of the reviewed cases; `run` returned true. Thus “missing cases still fail” is not established by this bridge. A minimum count cannot authenticate coverage identity.

Maintain an explicit reviewed module/case inventory and compare old-to-new behavioral obligations. Missing required cases must fail independently of how many unrelated tests were added. Preserve stronger tests that reject unknown scope/failure waivers. Do not transplant this consumer's native C# bridge as a universal ownership solution.

## Verification and retained history

| Item | Assessment | Appropriate generic repair |
| --- | --- | --- |
| V1 | PKV003 is correct for unknown inputs. The supported upgrade/reset integration did not provide current owners/checks for installed tooling, generated guidance, original inputs and retired state. Packet bounded groups with actual checks are much better than catch-all mapping or moving the baseline. | Generate bounded classifications and reusable checks from authenticated install/reset/retirement records. Supply a supported executable tooling-check owner/adapter; consumers should not hand-build hundreds of integrity rules or make arbitrary application tests stand in for tooling proof. Preserve unknown-input failure. |
| V2 | Anchored byte inventories and complete inactivity tests can prove preservation of retired archives/locks/history. The packet archive helper has the independently reproduced gaps below, so its stronger guarantee is not established. Hardcoded 705/8/134 counts are local witnesses. | Preserve exact inventories through authenticated retirement records; reject additions, missing files, aliases/traversal, edits and active references. Keep native restore responsible for current active locks. Do not import or execute archived product code to qualify preservation. |
| V3 | Authentic originals plus explicit local deviations is the right provenance model. Rerendering generated guidance read-only is useful. Exact local versions, fingerprints, 35-file guidance sets and 490-file tooling boundaries are consumer evidence, not universal implementation constants. | Provide reusable installed-source/guidance verification against authenticated manifests and declared repair provenance. A method name listed beside a changed hash does not itself prove that the method tests that change. Keep publisher-original, locally repaired and historical receipt claims distinct. |
| V4 | Current configuration/architecture/composition validators are relevant; setup-history hash checks prove consistency/preservation only. Six core Specify files differing from their own manifest remain unresolved coherence discrepancies. Matching old Git object identities does not make the manifest coherent. | Diagnose the creator/refresh lifecycle and repair supported current ownership without re-signing old evidence. Preserve historical records; emit honest current diagnostics rather than treating baseline equality or a working CLI as full integrity. Local counts/digests should derive from actual authenticated records. |

The verification layer should explain which category a file belongs to and which real check verifies it. “Everything has an owner” is ineffective if the selected owner does not test the changed mechanism. Conversely, preserving inactive bytes does not require replaying retired applications.

Two independent negative probes found holes in the packet's archive helper itself. Changing historical payload bytes and updating the local inventory hash still passed `retained_archives.verify`. Adding a `Directory.Build.props` Compile item pointing into the archive also passed its inactivity check. The helper trusts current archive inventories without an independent original witness and scans only selected literal architecture/composition/tsconfig/C# project inputs, omitting props/targets/import/evaluated activation. These probes establish gaps in the claimed verification, not evidence that this consumer's archive was actually altered or activated. Generic archival support must anchor the inventory to authenticated reset/archive evidence and include supported evaluated activation inputs.

Other V3 claims also need their exact boundaries: declaring a changed hash plus the name of an existing C# test method does not prove execution or coverage. `verify_migration` checks a historical plan self-hash and content-addressed originals but does not independently bind the complete original-file set to the canonical attempt inventory; a count of 63 cannot provide that binding. Reuse canonical validators and actual executed regression identities.

The author identified the six core files under `.specify/scripts/python/`: `check_prerequisites.py`, `common.py`, `create_new_feature.py`, `resolve_template.py`, `setup_plan.py` and `setup_tasks.py`. Their bytes match the original baseline; their introduction cause remains unknown. Distinguish line-ending conversion, stale manifests and actual customizations using the exact installed core distribution and generation inputs. Do not re-sign unchanged bytes merely to clear a mismatch.

## Consumer wiring and expected failures

These items need separate immediate-cause and effectiveness assessments. A correct rejection does not require weakening the guard; repeated avoidable misuse can still justify a supported command/configuration improvement.

| Item | Finding and repair assessment | Knowledge or mechanism that should prevent recurrence |
| --- | --- | --- |
| C1 | Unprepared composition and inaccessible/unselected Python are expected preflight failures. Current maintained selectors and explicit prepare/run guidance already exist. Attribution depends on the original invocation. | One canonical command should identify the selected executable and exact missing preparation. Avoid bare interpreter guesses and repeated prehooks within one invocation. |
| C2 | Old Node checking, missing Vite typing and six invalid project definitions are reported; their original provenance is not in the packet. Current hosted-page tsconfig already includes `vite/client`, and the native renderer emits project definitions. | Centrally install and build the exact generated default with accepted pins. Determine whether stale owned scaffolding survived update or whether current generation was wrong before choosing an upstream patch. |
| C3 | FromServices, real OpenAPI document registration, interceptors, typed JSON metadata and public problem DTO wiring are predictable integration difficulties. Existing guidance explains parts, but no complete centrally compiled/exported example of their combination was found. | Supply a minimal selected-version endpoint/configuration path that compiles, exports and produces a checked client. Use native public seams, preserve closed shapes/string unions, and prove runtime/export parity. More generic prose alone is insufficient. |
| C4 | Native generator lock ownership and maintained npm syntax are already documented. The local remedy is plausible; downgrade/manual generation would be wrong. | Exercise the runnable recipe and command argument routing centrally against the selected generator. Keep the generator's own real lock. |
| C5 | Native registrations/scalar settings and analyzer compliance are consumer setup issues with a useful upstream example gap. Report correctly does not call syntax/build failures meaningful product reds. | Qualify the actual public harness/configuration seam with nondefault effective options and durable observations. Keep the shared harness tests centrally reusable. |
| C6 | Expanding rootDir to cover real managed imports can be appropriate if strictness/include are retained. The original Axe/import failure is not independently attributable from this packet. BFCache listener code alone is not behavioral proof. | Align generated frontend layout with real imports, and centrally prove shared session/recovery navigation. Preserve domain input correction and app-specific behavior checks without repeating standard auth internals in each consumer. |
| C7 | PKV002 for unreasoned multi-owner Focused execution and rejection of result JSON as an action are correct contracts. Native sandbox access failures are environment observations. | Emit exact valid invocation/action examples and actionable diagnostics. Do not invent full-suite fallback, unknown-transition tolerance or implicit permission changes. |
| C8 | The incomplete consumer quickstart command was wrong; the central eng README already names the owner. Local correction is appropriate. | Centrally smoke-test emitted command examples and bind placeholders to real configured owners where possible. |
| C9 | Stale consumer CI/docs are plausible; packet tests check strings/paths rather than execute remote CI. Current central templates do not contain the reported legacy entry-point strings. | Trace generated versus owned workflow provenance and update reconciliation. Exercise emitted workflow commands with explicit prerequisites. Do not claim remote green from text assertions. |
| C10 | Stale frontend/package closure guards are doing their job. Maintained refresh and a fresh entry are appropriate. | Explain the changed source and exact rebuilding owner. Preserve freshness; avoid invisible refresh that hides inconsistent state. |
| C11 | PKT021 correctly rejected a producer task combined with existing native evidence. Restoring producer/none while retaining actual evidence separately is the right repair. | Prefer structured task-map generation and diagnostics showing the two valid alternatives. Preserve ancestry, effort, baseline and human decisions. |

The newer report adds S1, recovery after the user reset Docker. Missing pinned images, volumes and old realm client IDs are expected environmental changes. Exact synthetic identity reconciliation and preserving the pre-reset record are appropriate; no Program Kit product defect is established by the reset itself. The recovery smoke is distinct from the earlier complete affected regression. Its driver used Node 24.22.0 while accepted source/build pins were unchanged, so do not promote that smoke into proof of the selected build toolchain. The subsequent human US1 approval is an actual separate decision, not a consequence inferred from the smoke.

## Upstream dependency and active knowledge

The retained preview.109 satellite collision was independently observed in the 0.13.2 release investigation. Passing PdfPig loading does not prove different-culture satellite correctness. Active `references/dotnet-runtime-and-application-bundles.md:113` still describes a “pinned” preview.61 runtime, while its earlier PdfPig link describes the older issue. Historical evidence should remain intact, but active selected-version guidance must not mix those states.

Current upstream research changes the recovery options: Nuplane PR 136 merged on 15 October 2026 at 17:14:45 UTC, and public release 0.0.12 was published on 16 October at 02:31:43 UTC. Its release source `80f74d02bef70a0410f9dd21064692bc088bb87c` descends from the culture-aware merge `b8c48b9253209a6c42b7111015a3cc50e17dd13a`; the release notes explicitly retain multi-assembly/culture-aware support. [Merged repair](https://github.com/valence-works/nuplane/pull/136), [public release](https://github.com/valence-works/nuplane/releases/tag/0.0.12).

The user identified the more precise package target: **`1.0.0-preview.111` on Feedz**, rather than the separate repository release label. This was independently verified by downloading all eight public archives without installing or executing them: Nuplane, Nuplane.Abstractions, Nuplane.Admin, Nuplane.Admin.Api, Nuplane.Loading, Nuplane.Loading.Abstractions, Nuplane.Loading.Api and Nuplane.Sources.Directory. Every nuspec declares the exact requested version and repository commit `b8c48b9253209a6c42b7111015a3cc50e17dd13a`. Publishing run 38775714721 succeeded from that same merge commit. Package sizes, SHA-256 values and exact URLs are retained in `artifacts/maintenance-research-2026-10-16/nuplane-preview111/package-evidence.json`. [Publishing run](https://github.com/valence-works/nuplane/actions/runs/38775714721), [public feed](https://f.feedz.io/valence-works/nuplane/nuget/index.json).

Thus preview.111 is an available fixed package target for the repair investigation, not an unpublished branch dependency. The feed also advertises later preview.114 versions; that observation does not silently substitute them for the user's identified preview.111 target. The eventual dependency-maintenance review must explicitly reconcile the chosen exact compatible closure and current publisher versions.

Foundation's latest public runtime release at research time is still 0.3.5. The retained public 0.3.5 image binds preview.109. Availability of fixed preview.111 packages does not change that image. The repair dependency is adoption of the fixed Nuplane closure by Foundation, a publicly released compatible Foundation package/image/knowledge closure, and then Program Kit qualification, including both PdfPig/multi-assembly and different-culture satellite behavior. Do not modify existing public package/image bytes or invent parser isolation to hide a loader defect.

One additional current workflow diagnostic is stale after the release-workflow follow-up: `scripts/update_dependencies.py:37` directs Windows users to a user-owned local Release terminal, but current `AGENTS.md` and local wrappers retire that gate. Correct that recovery instruction to the current CI-owned maintenance/qualification path. This is a newly found guidance defect, not evidence that the new publication mechanism failed.

## Packet sanitization

Narrowing a private-key detector from any source-code mention to actual complete PEM header lines can be a valid false-positive repair. It must preserve positive key/known-credential/personal-path tests and must not add diagnostic payloads to the allowlist. The narrative says those tests passed; the scanner regression source is not among the reviewed 73 packet entries, so that claim is not independently reproduced here. This remains packet-tooling evidence, not a reason to change Program Kit security behavior.

## Research verification

- Five independent local reproductions confirmed P1, R1, R3, R5 and R8 as described above. R2 is confirmed directly in the shipped wrapper; P2's source and focused local repair tests establish the phase mismatch.
- The existing `tests/validate_scoped_verification.py` suite passed all 50 tests despite the identified integration failures. Its log is `artifacts/maintenance-research-2026-10-16/tooling-scoped-baseline.log`. That coexistence demonstrates a coverage boundary, not a reason to ignore those tests.
- An initial test invocation could not access the sandbox's default temporary directory. Repeating it with process-local TEMP/TMP under the owned research directory passed. The initial failure is an environment observation.
- A pure isolated probe confirmed the shared-runner threshold accepts 126 unrelated green cases while using zero of the reviewed case identities.
- Disposable archive probes confirmed that payload-plus-rehashed-inventory changes and an archive reference from Directory.Build.props pass the packet helper; temporary fixtures were cleaned.
- No complete Development or candidate qualification execution was needed to claim a production fix: no production fix was made. Implementation will use targeted validators and bounded Development; the new exact-candidate CI workflow owns complete publication qualification.

## Repair workstreams for the interview

1. Complete the standard configured browser experience and centrally prove the actual emitted composition, preserving native protocol/API contracts.
2. Repair updater retry transitions, verified retirement and real native restore coverage with interruption and tampering tests.
3. Repair installed CLI imports, planning/execution separation, selected runner qualification, verification preparation ownership, source inventory and JSON output.
4. Supply reusable installation/reset/retirement checks and generated bounded mappings, with explicit required shared-test identity rather than consumer-specific hash collections and minimum counts.
5. Provide selected-version runnable integration knowledge for native API/export, options/harness, frontend imports and current commands. Route it from typed capability selection at the point of use.
6. Adopt a corrected public dependency closure through the established publisher and Program Kit maintenance process; use the current CI qualification/promotion workflow for the eventual candidate.

These are proposed workstreams. The interview must settle remaining configuration/customization, migration, verification ownership and dependency/release sequencing before implementation starts.

## Agreed interview decisions

On 16 October 2026 the user accepted all three first-round recommendations:

1. Foundation owns the reusable runtime presentation capability. Program Kit automatically configures its routes, branding and integration and centrally qualifies the configured result.
2. The shared default covers sign-in, sign-out, expired sessions, denied access, callback/provider failures, general browser exceptions and not-found pages. Machine/API calls retain structured JSON.
3. Isolated upgrade reproduction retains its clean-commit requirement. Dirty consumers use an inspectable resumable direct-upgrade path that preserves authored changes and normal integrity/conflict checks.

The configuration-only standard-journey requirement is also settled: consumers do not recreate the shared presentation mechanism or write duplicate framework/protocol tests. Consumer-specific domain behavior remains distinct.

The user accepted all three second-round recommendations:

4. Every supported browser composition automatically enables the complete page set using configured branding, localized copy and routes. Custom presentation uses an explicit extension point.
5. The batch includes supported preview/apply migration for existing consumers, preserving business code, accepted decisions and customized pages. Conflicts are presented for review; consumers do not copy presentation examples or construct the shared infrastructure.
6. Program Kit centrally maintains installation/updater/archive/retirement/CLI checks and generates their ownership mappings. Consumers retain domain/custom-behavior tests, without bespoke native bridges or hardcoded tooling-integrity maps.

The user accepted all three third-round recommendations:

7. Foundation also supplies a safe generic browser page for HTTP failures before an application can be identified. Once identity is known, application branding applies; status codes and safe recovery remain meaningful.
8. Sign-out normally proceeds immediately when no unsaved work exists and requests confirmation when work would be lost. The user explicitly requires configuration to disable confirmation entirely or require it every time, plus a simple overridable consumer interface for determining unsaved work. The shared capability owns the dialog and logout protocol. The resulting page distinguishes local session termination from uncertain provider-wide termination.
9. Application presentation uses its frontend's configured brand and language. Shared identity providers retain their separately accepted realm theme; an application-specific provider theme uses an explicit supported selection.

The proposed confirmation modes are `never`, `when-unsaved` (default), and `always`. This names the agreed behaviors; the concrete public API remains to be designed. Unsaved-work evaluation belongs to browser application state and should have a small framework-neutral extension contract. Implementation must preserve trusted-user-gesture requirements and leave session/private state intact when confirmation is cancelled.

The proposed browser extension contract is a synchronous `UnsavedWorkSource.getState()` returning `clean`, `dirty` or `unknown`. A shared registry accepts multiple sources and returns a disposer for each registration. Existing form/editor frameworks can adapt their own dirty/autosave state; no mandatory Forms or UI-framework dependency is required. Pending or uncertain asynchronous saves are exposed through the source's current local state rather than a remote query inside the sign-out click. This preserves the current logout helper's synchronous popup creation before its first await. When confirmation is shown, its Confirm button supplies the fresh gesture for actual logout; opening/cancelling the dialog performs no logout dispatch or private-state clearing. Concrete API names remain provisional.

The user accepted all three fourth-round recommendations:

10. In `when-unsaved` mode every active source must report clean to skip confirmation. Unknown/invalid/throwing evaluation selects a confirmation with honest uncertainty wording. `never` bypasses unsaved evaluation and confirmation entirely while retaining the normal secure logout protocol.
11. Automatic session expiry bypasses sign-out confirmation, clears private presentation and offers sign-in recovery. Acknowledged server drafts remain preserved; recovery distinguishes unsaved/uncertain outcomes and never silently resubmits them.
12. Foundation first qualifies and publishes the corrected Nuplane integration and shared presentation capability. Program Kit then adopts the public package/Host/knowledge closure and qualifies the complete maintenance candidate through the new workflow. Independent Program Kit repairs may proceed before adoption. Actual exact-publication approvals remain later decisions.

After requesting concrete explanations, the user explicitly included all three fifth-round repairs:

13. Reliable database setup: shared tooling establishes deployment/application permissions correctly and prepares disposable schemas before parallel tests. Consumers supply domain migrations/configuration rather than ad hoc permission-repair helpers.
14. Correct handling of old files: supported retirement records distinguish deliberately preserved inactive locks/archives from damaged or unexplained active inputs. The updater does not demand renewal for authenticated retired projects and does not infer retirement merely from a missing project.
15. Clean adoption of shared fixes: normal upgrade preview/application recognizes verified local Program Kit repairs, moves the consumer onto released shared implementations and retires redundant local tooling checks after equivalent coverage is proven. Preserve historical patches/evidence, business code and accepted decisions; reconcile customizations explicitly.

The remaining interview should use concrete consumer outcomes and release evidence. The user does not need to select routine internal implementation mechanics.

The user accepted all three final-round recommendations:

16. Qualification creates a real fresh consumer from configuration and upgrades a representative locally repaired consumer. It exercises actual served pages/controls; test-injected replacement presentation is not proof that the configured application works. Shared journey tests belong centrally.
17. After the new public release is verified, the work includes upgrading claim_evaluator through the supported updater, preserving current business work, data, task history and recorded approvals, then presenting the repaired journeys for human review.
18. Hold the Program Kit maintenance release until the Foundation integration and all confirmed batch repairs are ready. Keep changes reviewable in separate commits, then qualify one complete candidate through the new workflow.

The interview is complete. The user requested a complete repair plan and coverage audit for review before implementation; the plan is recorded separately in maintenance-repair-plan-2026-10-16.md. No product implementation begins until that review is confirmed.

### Supplemental findings received during plan drafting

The active US2 consumer chat supplied eight further findings, assessed read-only against current source. They are separate from the original 31 report items and S1. The complete plan assigns N1–N8 to them with concrete work and evidence:

- N1: consumer adapter child/grandchild interpreter propagation plus inconsistent applicable dependency readiness. The canonical verifier already uses sys.executable correctly; improve the shared adapter/readiness contract rather than misattribute the whole chain.
- N2: a temporary staging witness disappeared. Provide durable content-addressed retention and authenticated recovery with platform path support; distinguish missing from modified and preserve original receipts. OS Temp selection by Program Kit itself is not established.
- N3: whole shared-file review scope can reopen unrelated accepted work. Existing material projections already help; extend conservative story-plan/architecture projections and diagnostics without rewriting historical human authority.
- N4: historical render reproduction depends on current PATH alias resolution. Bind authentic historical render inputs separately from present executable readiness; do not generalize a literal python3 mock into provenance.
- N5: replacement-style checkpoint guidance conflicts with retained/appended decisions/failures and merged summary size. Separate bounded current state from complete retained history with actionable size diagnostics and atomic failure.
- N6: current tasks target a compatibility document frozen by consumer preservation rules. Make active/historical ownership available to drafting; use a mutable current index/new proposal while retaining historical bytes.
- N7: a consumer task's grouped contract filename conflicts with the selected one-type-per-file analyzer. Qualify generated task examples under actual selected rules; no canonical template specifically generating that consumer filename was identified.
- N8: combined model/OCR renewal cannot consume narrow OCR-only authority. Add reusable operation-scoped preparation/binding/accounting/recovery with offline central proof, preserving aggregate reservations and unknown outcomes. The observed limitation is not an approval bypass and grants this task no paid execution authority.

The plan's original-scope independent audit covers all 31 original items, S1 and eighteen decisions; final auditing additionally covers this supplement. Source-level findings and planned inclusion remain distinct from implementation and fresh acceptance.

### Further findings received after the initial plan audit

The ongoing consumer chat supplied three more diagnostics after the initial 40-item audit. Its local continuation report records them as D24–D26; the repair plan assigns N9–N11. This task inspected the report, relevant repaired consumer source, current Program Kit toolchain paths and the available older Foundation build implementation read-only. These observations do not claim a new consumer acceptance or paid execution.

- **N9 / D24:** the provider invented `PolicyEvidence:RootPath` while accepted typed composition uses `EvidenceFiles:Root`. Direct DI tests copied the invented key. The corrected provider and settings metadata now use the accepted key. This is a consumer integration error. Upstream prevention should expose the actual binding at authoring, validate declared settings where contracts allow, and centrally exercise public registration with inputs derived from the real composition. Hardcoding the same mistaken key in a fixture cannot qualify integration; silent aliases would conceal the mismatch.
- **N10 / D25:** current metadata used a raw CRLF hash, while the reported native export expects LF canonicalization. Normalizing edited source and regenerating current metadata appropriately preserved the guard. The available older Foundation `EmitFeatureDescriptor` implementation independently demonstrates CRLF-to-LF UTF-8 hashing, but that is not a substitute for tracing the exact selected exporter and original generator. The plan requires one precise generation/validation contract, cross-platform native proof and explicit encoding/BOM/lone-CR behavior. Do not normalize unrelated archive hashes or re-sign historical records.
- **N11 / D26:** an absent managed Node invalidated recorded npm command paths. The user restored Node, but its bundled npm differed from the independent npm pin, requiring a second preparation round. Exact-pin refusal is correct. Current `device_toolchain.ensure` already aggregates Node/npm failures; the gap is consistent joint recovery at the earlier recorded-command/composition entrypoint and instructions accounting for npm after Node selection. Plan paired diagnosis and ordered user-owned preparation, followed by fresh-shell checks and normal evidence renewal. No installation occurred in this task, and no cause is established for the vanished installation.

Independent follow-up for N10 inspected the consumer's installed knowledge index, identifying selected Foundation 0.3.5 at `ff091a2`. Its hash-verified `EmitSettingsMetadata.cs` slice (`84ea92555331b0cbe259ac3fb84ea1379920833095e0885e9e6b81808ece3216`, lines 102–104) reads source text, replaces CRLF with LF, hashes UTF-8 and checks the recorded hash. `InspectSettingsSourceGraph` lines 45–47 uses the same newline rule. The individual unchanged document's origin is `aa7ae11`; selected-index membership does not mean the document changed in `ff091a2`. This strengthens the captured-source contract evidence while leaving actual package/export execution and the original generator's ownership as implementation-stage qualification work.

The report's D22 is an automatic message-review restriction, not a Program Kit defect. D23 is correct stale runtime-source rejection after changed packaged sources; its supported restage/fresh-preflight recovery is already covered by C10 and current evidence requirements. These two observations do not require new product-defect rows. The additional three distinct findings bring total planned coverage to 43, with all eighteen accepted interview decisions retained. Revised mechanical and independent audits pass with no coverage omissions or duplicates. Work remains planning-only.

### Runtime constraints for the remaining interview

The selected exact Foundation 0.3.5 source capture, commit `ff091a2be8daab217291efe5309d2289567339c8`, supplies the authoritative mechanism facts. The available local Foundation checkout has older relevant behavior and must be refreshed/reconciled before implementation; do not infer the selected public contracts from that older source.

- Authentication uses a replaceable `IAuthenticationErrorWriter` registration, but general ProblemDetails does not expose an equivalent HTML writer seam through `IProblemRepresentationPolicy`. The latter adjusts safe problem fields only.
- `FoundationBoundedProblemDetailsWriter.CanWrite` returns true, is inserted first and writes application/problem+json. Registering an ordinary HTML writer later will not create the desired representation. A native classified representation seam must preserve bounded problem admission and safety.
- The BFF currently recognizes `/api` for redirect-as-error behavior. Accept headers alone cannot determine whether a caller is entitled to browser presentation. Explicit endpoint/request purpose is required to preserve machine/API/BFF-control contracts.
- HostedPages supports public versus authenticated page/bootstrap admission. Its static page plus bootstrap mechanism does not itself supply authentication-state-aware recovery, general exception presentation or the required standard state/copy model.
- Current exception/status handling runs inside a resolved shell. A failure or unmatched request before shell resolution needs a separately qualified, application-neutral host fallback if the standard browser promise is to cover it. A shell feature cannot promise to handle failures outside its pipeline. The shared Host must remain independent of Program Kit.
