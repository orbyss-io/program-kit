# Program Kit maintenance repair plan

Prepared 16 October 2026. **Draft for review before implementation.** Planning baseline: Program Kit main `02d772cecb064a96f6755637fbd1950eca8fb647`. Published comparison baseline: 0.13.2 at `fff643af3a12b6f7f975106992a792aab2df7cf3`. Refresh source and reconcile concurrent work when implementation starts.

This batch fixes the confirmed toolkit defects and replaces repeated consumer infrastructure invention with supported, configured capabilities. Its main consumer outcome is a fresh or upgraded application whose standard sign-in, sign-out and error journeys work immediately from configuration. The batch also repairs interrupted upgrades, retired-input classification, tooling verification, preparation and native integration guidance.

Every original report item has a disposition in the coverage matrix below. **Covered by this plan does not mean repaired or verified.** Product implementation has not started in this task. Several original causes still require diagnosis; those investigations have explicit completion conditions rather than assumed repairs.

The [root cause review](maintenance-report-root-cause-review-2026-10-16.md) contains source findings, independent reproductions, consumer-repair critiques, evidence limitations and all eighteen accepted interview decisions. The original and corrected sanitized packets are retained under `artifacts/maintenance-research-2026-10-16/`. They are research inputs, not publisher attestations or substitutes for fresh execution. Eleven additional findings arrived from the active US2 consumer work during planning and review; their proposed repairs and evidence limits are included in L and its separate coverage matrix. N9–N11 arrived after the initial 40-item coverage audit.

## Agreed outcomes

1. Foundation owns reusable runtime browser presentation and its public extension contracts. Program Kit selects, configures, brands, packages and qualifies that capability without creating a dependency from Foundation to Program Kit.
2. Supported browser compositions automatically provide sign-in/recovery, sign-out, expired-session, access-denied, callback/provider-failure, general exception and not-found presentation. The running Host supplies a safe neutral browser fallback before an application is identifiable. API and native machine/control contracts retain their established representations and protocol behavior.
3. Application pages use the owning frontend's accepted branding/locales. Shared identity providers retain their separately accepted theme; application-specific provider theming is explicit.
4. Sign-out confirmation is configurable as `never`, `when-unsaved` (default), or `always`. A small browser-side source interface supplies application-specific unsaved state. Shared code owns aggregation, dialog behavior and logout.
5. Existing consumers receive preview/apply migration, including adoption of verified local repairs. Preserve business code, data, accepted decisions, task IDs, implementation baseline, effort, approvals, original patches and historical evidence.
6. Program Kit supplies reusable installation, updater, archive/retirement and CLI checks with generated ownership mappings. Consumers retain tests for domain rules and custom behavior, without bespoke generic integrity suites or Python-to-C# bridges.
7. Shared database preparation establishes the correct deployment/runtime permissions and owns disposable fixture lifecycle. Consumers declare their domain migrations and configuration.
8. Clean-source isolation remains the supported reproduction model. Dirty consumers use an inspectable resumable direct upgrade with normal provenance and conflict checks.
9. Foundation's corrected public package/Host/knowledge closure precedes final Program Kit adoption. Independent toolkit repairs may proceed earlier. One complete Program Kit maintenance candidate is qualified through the new CI workflow.
10. After public publication is verified, upgrade claim_evaluator through the normal updater and present the repaired journeys for the user's review. The implementation plan does not treat that future review as already accepted.

## Scope and execution boundaries

Work spans Program Kit and the required Foundation runtime/publisher changes. Nuplane's culture-aware repair is already publicly available; no consumer workaround or Nuplane source patch is planned. Package names and exact new versions will follow the repositories' conventions and actual compatible public outputs. No version/tag is selected by this document.

The verified Nuplane fixed reference is `1.0.0-preview.111`: all eight public Feedz archives declare PR 136's merge commit `b8c48b9253209a6c42b7111015a3cc50e17dd13a`; publishing run 38775714721 succeeded at that source. Keep that as the demonstrated fix baseline. The feed also contains later previews. The required dependency-maintenance workflow must reconcile current publisher versions and compatibility explicitly; it must not silently substitute an unqualified version or treat a repository release label as a package version.

Keep ordinary implementation on focused validators and bounded Development. CI owns complete candidate qualification, including Linux Chromium/Firefox/WebKit and required Windows compatibility. The known local Firefox launch failure is a host limitation; preserve Firefox in CI. Do not run retired local Release entry points.

Preserve the already published 0.13.2 tag/assets and historical receipts. The new workflow's qualification and non-publishing verification are proven at the prior follow-up source; its first actual tagged promotion/public smoke remains a future outcome to establish honestly.

This review starts no product implementation, paid worker, device installation, live-data migration or external message. During later execution, actual publication and any failed-tag correction retain their exact commit/tag authorization. Optional paid acceptance remains separately user-invoked under its existing one-use manifests. Future user-owned device updates retain their documented preparation boundary.

## Work packages

### A Establish authoritative baselines and close attribution gaps

**Owner:** Program Kit maintenance, with Foundation source/provenance inspection. **Depends on:** plan review. **Covers:** U0, C1/C2/C6/C9 attribution, V3/V4, S1, packet provenance/sanitization.

- Refresh main in both repositories and inspect their applicable contributor instructions. The available local Foundation checkout has behavior older than the selected 0.3.5 capture; establish intended current source before editing it. Preserve unrelated work and use isolated development branches/checkouts where appropriate.
- Record exact source IDs, selected profile/Host/toolchain identities, original report/manifest digests, current local deviations and actual affected files. Keep sanitized packet identity separate from original-source hashes; normalization/path sanitization explains legitimate differences.
- Diagnose the six core Specify manifest discrepancies using the exact current distribution, canonical generation inputs, actual script bytes and line-ending rules: `check_prerequisites.py`, `common.py`, `create_new_feature.py`, `resolve_template.py`, `setup_plan.py`, `setup_tasks.py` under `.specify/scripts/python/`.
- Determine whether each discrepancy is an installation/generation defect, supported transformation, customization or stale manifest. Matching an old Git object is historical evidence only. A benign conclusion requires authenticated comparison; a repair uses supported current ownership reconciliation while retaining the old record unchanged. Otherwise keep an explicit unresolved integrity finding.
- Obtain original generated/owned Node checks, six project definitions, frontend typing/import configuration and consumer workflow provenance where needed for C2/C6/C9. Correct current generation/update behavior if implicated; do not blame current templates merely because an older consumer file failed.
- Correct R7's withdrawn causal claim in the issue/acceptance ledger. Retain the later viewport assertions as assurance; the earlier runs are not proven to have used wrong dimensions.
- For the packet scanner, inspect its actual generic source/regressions if available and verify complete PEM-header detection, positive key fixtures, known-fixture credentials, personal-path cases and detector-source negative. Keep this bounded evidence-tooling task separate from production credential scanning. Preserve failed packet builds and sharing boundaries.
- Record S1 as user-confirmed Docker-reset recovery, not a product regression. Verify synthetic identity recovery through supported records and disclose that a Node 24 smoke does not qualify an accepted Node 26 build. The earlier report's pending review and later actual US1 approval remain separate dated facts.

**Completion evidence:** a disposition with source/provenance for each attribution gap; six-file integrity diagnosis or an explicit remaining blocker; no invented receipts, reconstructed retired business code or modified historical evidence.

### B Foundation shared browser presentation and fixed runtime closure

**Owner:** Foundation. **Depends on:** A authoritative source. **Covers:** new presentation finding; Nuplane collision; native portions of C3/C5.

Implement a provider-neutral presentation capability in the existing feature/package architecture. A separately selected Web presentation feature is the proposed boundary; finalize the smallest package split that follows current Foundation conventions. The Host remains application-neutral and independent of Program Kit.

The public contract must include:

- Typed per-application/shell branding, locale/copy, public presentation routes, safe return target, selected response policies and sign-out confirmation policy. Validate paths and collisions against existing pages, API/control routes and shell prefixes before activation.
- A versioned, centrally supplied browser module and checked consumer-facing types for common authentication controls, recovery focus, confirmation and unsaved-state registration. Program Kit consumes the authoritative artifact; it does not fork the shared implementation into another helper.
- An explicit custom-presentation extension seam. Existing public writer registrations, custom pages, themes and error handlers remain inventoried configuration/customizations that migration must reconcile.
- An authoritative request/endpoint-purpose classification for browser presentation versus machine/API/protocol handling. Do not infer all requests outside `/api` are browser pages or let an Accept header change a machine endpoint's contract.
- HTML selection after the same bounded safe error admission used for JSON. The current bounded ProblemDetails writer claims every response and is registered first; adding a later HTML writer is insufficient. Extend native selection/ordering without weakening safe codes, closed shapes, status ownership or exception redaction.
- Application-level exception/status pages and a generic neutral Host fallback for eligible browser HTTP failures before shell selection. Qualify unmatched root/prefixed URLs, unknown shell/default-shell routing and known-application failures. A running HTTP fallback cannot establish availability when the server itself is unreachable.

Preserve `/bff/user`, `/bff/antiforgery` and `/bff/signed-out` machine contracts. Preserve native challenge/callback/logout redirects and validate browser-purpose recovery explicitly. Configure both the application's landing and native `LogoutLandingPath`; reaching a URL or reading `remote=unavailable` does not prove session/provider state.

Serve readable, branded recovery with public assets available to anonymous users, keyboard/focus support and safe no-script recovery. Preserve private/no-store/no-index/security policies and CSP. Handle actual session state independently of callback-error URLs. Respect cancellation, already-started/streamed responses and existing response bodies rather than attempting to append an error document.

Adopt the corrected Nuplane dependency closure through Foundation's maintenance process. Verify actual package identities/source, lock closure and immutable Host contents; exercise real PdfPig multi-assembly loading and same-simple-name/different-culture satellites, including fallback and retained same-culture conflict rejection. Refresh the public knowledge with the actual selected source and release bytes. A successful Nuplane publishing run alone does not validate Foundation's integrated image.

**Completion evidence:** native feature/options/asset tests, real selected Host browser/protocol tests, package/build/knowledge evidence and required publisher security scans. Publish a new immutable Foundation closure through its own release process after exact-source review. Never replace existing public assets.

### C Browser unsaved work and confirmation contract

**Owner:** Foundation browser capability; Program Kit configuration/adapters. **Depends on:** B public contract. **Covers:** accepted decisions 8/10/11 and the user's explicit extension/disable requirement.

Proposed shape, with final public names following the selected client API conventions:

```ts
type UnsavedWorkState = 'clean' | 'dirty' | 'unknown';

interface UnsavedWorkSource {
  getState(): UnsavedWorkState;
}

// register(source) returns a disposer bound to the current application surface.
```

| Configuration | Shared behavior |
| --- | --- |
| `never` | Bypass unsaved evaluation and confirmation; execute the normal secure sign-out action. |
| `when-unsaved` | Proceed immediately only when every active source is clean. Dirty, unknown, invalid or throwing sources select confirmation. No registered editable source means no claimed unsaved work. |
| `always` | Ask for confirmation on every user-requested sign-out. |

Sources express domain meaning: edited fields, editor buffers, pending autosave or uncertain persistence. They expose current local state synchronously; the shared control does not infer cleanliness from DOM values, save/discard drafts, inspect private storage or start a remote dirty check. Adapt supported shared form APIs when available; custom editors implement the small source contract. No Forms/UI-framework dependency is mandatory.

Use one shared registry per application surface, including independently bundled controls. Registration/disposal follows component lifetime; stale sources cannot create permanent warnings. Aggregate multiple editors and serialize repeated sign-out requests. Recheck current local state when relevant during confirmation; a displayed modal cannot silently turn an old clean snapshot into proof about later work.

Before confirmation, perform no logout dispatch, antiforgery acquisition, provider popup or private-state clearing. Cancellation preserves the current session and work. The Confirm button supplies the fresh trusted gesture for the actual protocol; a clean immediate sign-out preserves the original click. Unknown wording must not falsely claim confirmed data loss. Automatic expiry has separate recovery: clear private presentation, preserve acknowledged server drafts, offer sign-in and never silently replay an uncertain operation.

**Completion evidence:** central tests for every mode; multiple/source-free/disposed/throwing/invalid sources; pending/uncertain saves; cancellation with zero protocol effects; repeated clicks; changed state during dialog; provider failure; postdispatch uncertainty; actual popup/keyboard/focus behavior on required engines. Consumers do not repeat these shared protocol/dialog tests.

### D Program Kit automatic composition and migration

**Owner:** Program Kit. **Depends on:** B/C public contract; prototype integration may use clearly scoped development inputs, while final qualification uses the public closure. **Covers:** presentation finding, C2/C6/C9, existing consumer adoption.

- Extend the canonical composition schema/model/rendering with typed presentation selection, routes, branding/locales and confirmation configuration. The current four-integer settings whitelist cannot express `LogoutLandingPath`; fix the authoring-to-runtime path rather than patching generated output.
- Automatically select and bind the native presentation feature, public pages/assets, browser client and both landing seams for supported browser compositions. Derive links from actual shell/path-base configuration. Keep private page/bootstrap access and public recovery admissions distinct.
- Reconcile existing frontend branding with separately accepted identity-provider branding. Preserve shared-realm authority; an app-specific provider theme is an explicit selection with real browser qualification.
- Use a thin generated binding for supported app entrypoints. Keep shared presentation implementation in Foundation. Provide a runnable source adapter example for custom unsaved state without requiring custom auth writers or copied framework code.
- Generate/consume the actual checked browser types and assets with a compatible frontend root/import structure. Keep strict TypeScript, lint and content-hashed build output intact.
- Drive applicability and concise guidance from typed selected capabilities and exact public knowledge, rather than requiring nearby prose mentioning identity screens.
- Add migration preview for existing landing settings, routes, writers, handlers, client imports, owned branding and custom pages. Apply only unchanged reviewed observations/digests. Known untouched generated integration migrates automatically; modified/custom integration receives a concrete reconciliation diff.
- Recognize verified local tooling patches that the release supersedes through authenticated predecessor/patch provenance and actual replacement behavior. Retire redundant local integrity rules/bridges only after their central successors are proven; archive patch/evidence history unchanged. Unknown local edits remain visible conflicts, never a blanket overwrite permission.

**Completion evidence:** fresh source and packaged installation render valid actual runtime configuration; repeat rendering is stable; nested-shell paths work; custom/untouched/conflicting/stale migration fixtures; upgrade from a representative locally repaired install; actual rendered pages and controls served from the real Host with no test-injected replacement presentation.

### E Interrupted updater and native restore coverage

**Owner:** Program Kit updater and building-block restore adapter. **Depends on:** A, retirement model in G. **Covers:** U0–U4.

- Keep clean-commit isolated reproduction and dirty direct recovery distinct in the inspectable plan. Preserve authored changes and actual destination/conflict checks. Generate authentic component source witnesses during packaging so consumers need no witness-construction helper.
- Carry one verified retry context containing original version/input identity, target fingerprint, archived originals, attempt stage and expected transitions. Distinguish installed component version, migration origin and the last completed receipt.
- U1: admit the exact authentic prior completed receipt during an interrupted upgrade while retaining plan/version/check guards. Preserve it as history; create new completion evidence only through the real completed update.
- U2: admit complete original or complete target materialized state when justified by that retry context. Keep actual materialization, selection, unmanaged-package and incomplete-transaction checks. Reject mixed/tampered states.
- U3: classify locks through authenticated active/retired ownership. Active owners undergo native restore; retired files retain verified bytes/inactivity; unexplained orphans produce actionable errors. Cover F#/VB/C#, multiple owners in a directory, custom/relocated lock placement and owner reactivation.
- U4: expose one canonical effective-restored-project/output closure from the native adapter. Reuse it for commands, digests, evidence and renewal admission, including direct roots, solution members and forward/reverse project references. A union of solution members and direct restore targets is insufficient.

**Completion evidence:** deterministic real update interruptions after each mutation boundary; successful exact retry; source/target/receipt/original/selection tampering negatives; real direct/solution/forward/reverse restore fixtures; retired/unexplained/changed/reactivated lock cases; installed and dirty-consumer preservation. Mock branch tests complement actual state transitions.

### F Installed commands runner qualification and source freshness

**Owner:** Program Kit governance/dotnet adapters. **Depends on:** A; can proceed independently of Foundation publication. **Covers:** P1/P2, R1/R2/R3/R5/R8 and command parts of C1/C4/C7/C8/C10/C11.

- P1/R3: establish one small consistent installed adapter bootstrap/loader for canonical scripts and engineering templates. Use it for phase and standalone task entrypoints. Test lazy schema-v2 paths and actual installed CLIs in fresh processes from supported working directories; do not rely on another test's imports.
- P2: make planning selection consume declared future project/edge intent while execution verifies physical references. Preserve role/direction and unknown-input checks. Explicitly declare ownership of future external Content/AdditionalFiles; planning evidence cannot qualify execution.
- R1: recognize exact qualified xUnit aliases and runner capabilities using the actual selected identity/version and normal NuGet casing. Preserve direct selected identity and MTP mode; qualify preview/apply/native restore/build/nonempty execution whenever selected runner inputs change. Reject unsupported/missing/ambiguous runners without downgrades or extra unrelated VSTest dependencies.
- R2: route every Python/native wrapper invocation through supported interpreter/tool selection and prepared browser cache. Verification performs read-only readiness and runs prepared tooling; acquisition remains explicit preparation. Missing/mismatched prerequisites report the precise supported recovery command.
- R5: distinguish authored source, generated outputs and explicitly observed restore state across eng/src. Exclude generated directories while retaining required actual assets/locks. Audit real engineering build inputs, including applicable C#/project files, rather than claiming completeness from a suffix filter. Test architecture-build then pack, authored drift and native output freshness.
- R8: make Plan stdout exactly its documented JSON document. Send human summaries/diagnostics through the appropriate non-Plan stream and preserve failures/nonzero outcomes. Capture and parse entire real wrapper stdout on native and scoped-adapter paths.
- Improve invalid Focused/delivery/task-map diagnostics with concrete valid action/command alternatives, preserving producer-versus-existing-evidence rules and current native guard semantics.
- Keep stale frontend/package closure checks intact and explain the changed input/rebuilding owner. Do not hide stale state behind implicit broad refresh or full-suite fallback.

**Completion evidence:** actual installed subprocess/wrapper tests with recording executables where appropriate; current selected-runner native execution; planned versus physical graph cases; full-stdout JSON parsing; authored/generated/native-state pack cases; unknown ownership, unsupported scope and stale evidence negatives. Keep deterministic tests agent-free.

### G Reusable integrity retirement and verification ownership

**Owner:** Program Kit installer/reset/verification. **Depends on:** A exact source classification. **Covers:** V1–V4, R9, U3 and local repair migration.

- Generate bounded input/check ownership from authenticated installation, generated-guidance, managed-output, reset/archive and retirement records. Preserve consumer domain mappings. Unknown inputs remain errors; no catch-all mapping, baseline advance or application-test substitution for toolkit checks.
- Provide a common toolkit-check runner/adapter with named checks and real results/evidence, so consumers need no native C# wrapper around generic Python checks. Integrate those typed checks with current native project selection and failure obligations; do not weaken Acceptance/Release narrowing or change Focused into broad acceptance.
- Anchor archive inventories to their original supported archival/reset record. Define expected roots/file sets and reject changed payload plus rehashed inventory, missing/extra/aliased/traversal inputs and unauthorized owner reactivation.
- Establish inactivity across supported active input mechanisms, including props/targets/imports and applicable evaluated project/file ownership. The reproduced Directory.Build.props bypass must fail. Choose bounded native evaluation/static admission without executing retired product code or replaying historical tests. An unsupported activation path is a diagnosed coverage gap.
- Keep current active-lock checks with native restore, retired-lock preservation with authenticated retirement, and historical protected-context checks with authentic reset witnesses. Historical consistency is not fresh product behavior.
- Reuse canonical source/migration validators and bind the full actual attempt-original inventory, canonical required-check closure, exact component files and generated output ownership. Do not accept a count or content-addressed filename as proof of the complete original set.
- Bind each local deviation to the actual executed required regression identities/results and relevant sources. Existence of a named C# method is insufficient. Preserve distinctions between public baseline, local deviation, generated output, historical receipt and current execution.
- R9: replace obsolete generic test fixtures with current native contracts using a reviewed old-obligation-to-new-case mapping. Maintain an explicit required case/module inventory; required case removal fails even when unrelated test counts rise. Keep missing/empty/skipped/failing execution as failure. Never restore deleted business fixtures simply to satisfy old tests.
- Finish supported current core-manifest reconciliation from A. Any unresolved integrity failure prevents a claim of clean adoption; preserve original manifests/receipts rather than re-signing the baseline.

**Completion evidence:** both reproduced archive negatives fail; required-case substitution/removal fails; real mixed domain/toolkit Affected selection passes from its retained baseline; missing/tampered public/generated/retired/attempt inputs fail; historical records unchanged; supported consumer upgrade needs no bespoke integrity bridge.

### H Database deployment and disposable fixture lifecycle

**Owner:** Foundation native persistence/deployment capability and Program Kit preparation integration; domain migrations remain consumer-owned. **Depends on:** A and selected public persistence contracts. **Covers:** R4/R6 and related C5.

- Inspect/reuse existing public deployment and fixture mechanisms before adding a narrowly scoped supported adapter. Declare separate deployment and runtime identities; configure schema/table/journal permissions required by actual operations and verify admission through the real application connection.
- Application startup checks the required schema/journal revision and permissions; it does not create product tables or gain administrator privileges to hide preparation failures.
- Deploy once before parallel test users, or use independently owned fixture schemas/databases. Verify ownership/cleanup identity and support the actual multi-process fixture model. Prove schema absence before the concurrent-first-preparation regression.
- Treat the consumer's ownership-transfer helper as a bounded disposable repair, not a general production migration. A retained supported ownership-repair mode must bind the exact target, complete declared object kinds/revision/owners/emptiness and apply under a transaction/lock preserving the inspected assumptions. Unexpected views/sequences/functions/objects, rows, foreign ownership and concurrent mutation must refuse. Prefer correct initial deployment/grants so repair is unnecessary.
- Keep deployment credentials scoped to owned preparation processes. Preserve live environments and historical migration bytes. Any application-owner convenience is explicit and limited to disposable fixtures.

**Completion evidence:** real PostgreSQL deployment/runtime role tests; application can perform only declared operations and read admission journal; denied access remains denied; fresh concurrent fixture preparation succeeds without serializing product concurrency; unsafe ownership/concurrency negatives; observed fixture cleanup. Mock dispatch tests do not establish SQL permission semantics.

### I Executable integration knowledge and active documentation

**Owner:** Foundation public knowledge plus Program Kit selected-profile guidance/generators. **Depends on:** actual public mechanisms; independent command corrections may proceed earlier. **Covers:** C1–C11, R1/R7/R9, stale runtime and release guidance.

- Supply one complete selected-version minimal API/provider example that compiles, activates, exports actual OpenAPI, generates a checked client and exercises nondefault native settings. Cover actual service registration, required interceptor namespace, AddOpenApi/document registration, explicit service parameters and typed JSON metadata/transformer seams.
- Use public metadata/export contracts and prove parity with actual runtime problem responses, preserving closed shapes, optional detail/field errors, strict numeric tokens and string unions. Do not expose/copy inaccessible native internals, strip constraints, reset baselines or invent generated clients.
- Demonstrate current public harness registration, scalar option activation, cancellation/analyzer requirements and independently observed durable effects. Keep syntax/setup failures distinct from meaningful behavioral reds.
- Make native generator lock ownership, npm argument routing, explicit prepare/runtime selection and Focused/affected/delivery examples runnable. Smoke-test emitted examples with configured owners. Classify environment/access denial separately from a shipped adapter defect.
- Keep strict frontend project/import typing aligned with managed shared artifacts; verify current Axe import/API rather than blindly copying a local fix. Qualify persisted-page privacy/recovery by actual navigation, including BFCache, rather than source-string checks.
- Preserve C6's existing domain safeguards during integration: committed-response-loss reconciliation through the original operation/status identity without a duplicate POST; raw control-bearing invalid input retained for correction; no private draft data in localStorage/sessionStorage. Retain the real domain regressions, without duplicating the shared authentication protocol tests.
- Replace stale consumer-generated CI commands through normal reconciliation when owned by the toolkit; preserve custom workflow ownership. Prove commands and prerequisites with executable fixtures/CI, not file/string assertions. Correct docs pins/project counts/current status from actual configured inputs.
- Fix the obsolete `update_dependencies.py` Windows local-Release recovery message. Align all active release guidance with CI-owned qualification and exact-artifact promotion. Preserve historical release documents unchanged.
- Refresh selected Nuplane guidance from actual new Foundation knowledge, including resolved satellite behavior and remaining limitations. Remove active “pinned preview.61” assumptions while preserving historical profiles/evidence.
- Route concise mechanism briefs, complete runnable examples and exact supported commands from typed capability selection into the relevant phase. Where the source was already correct, improve its point-of-use projection and executable recipe instead of adding another prose checklist or mandatory per-task gate.
- Provide structured task-map rendering/examples that preserve producer ancestry, native evidence, accumulated effort and recorded human decisions. Toolkit repair does not authorize the next application story or convert narrow engineering checks into full feature acceptance.

**Completion evidence:** fresh installed current-profile example executes end to end; emitted commands parse/run; consumer migration updates only supported owned entrypoints; actual strict frontend/navigation evidence; exact-version knowledge/packaging hashes remain coherent. Missing original provenance in C2/C6/C9 remains an explicit diagnosis task under A rather than a fabricated publisher bug.

## Coverage of every report item

All entries below are **planned dispositions**, not completed fixes. Work-package letters identify the implementation/investigation owner and required evidence above. “Preserve guard” means the original rejection remains correct and its recovery/ergonomics are covered; “correct diagnosis” means the reported product cause was not established.

| Report item | Disposition | Work | Evidence required to close the item |
| --- | --- | --- | --- |
| U0 Dirty baseline and same-version witnesses | Preserve isolation boundary; improve direct recovery and authentic packaged witnesses | A/E/G | Dirty work preserved; isolated baseline explicit; witnesses derive from verified release; unknown source rejected. |
| U1 Prior completed receipt on retry | Fix authentic intermediate-state admission | E | Real interrupted update resumes from original version; altered receipts/originals/checks fail. |
| U2 Target materialized lock on retry | Fix authenticated original/target transition | E | Real complete target accepted only in verified retry; corrupt mixed state fails. |
| U3 Retired project locks | Replace overly broad absence-based skip | E/G | Authenticated retired locks preserved; unknown/tampered/reactivated and language/custom lock cases handled. |
| U4 Restore coverage | Use complete canonical native restore closure | E | Direct/solution/forward/reverse subjects accepted with real evidence; unrelated/stale/tampered coverage fails. |
| P1 Composition import | Fix installed canonical adapter bootstrap | F | Fresh installed schema-v2 phase subprocess succeeds without ambient imports. |
| P2 Planned versus physical graph | Separate planning from execution selection | F | Declared future edges plan successfully; invalid/unknown inputs and stale execution graph fail. |
| R1 xUnit alias | Qualify supported selected identity/version | F/I | Actual default scaffold previews/applies/restores/builds and executes nonempty tests; unqualified runners fail. |
| R2 Browser runtime/acquisition | Use selected shared interpreter and explicit preparation | F | Recording wrapper proves routing/cache/no acquisition; real prepared browser check passes. |
| R3 Standalone task import | Use common installed loader | F | Real standalone CLI/finalize and existing-evidence cases pass; unknown ownership stays rejected. |
| R4 Schema wrong owner | Correct deployment/grant lifecycle; bound any repair | H | Real runtime-role admission and permissions; complete object/atomicity/unsafe-target negatives. |
| R5 Generated eng outputs counted as source | Correct actual authored/generated/native input classification | F | Native architecture-build then pack succeeds; authored drift and changed required restore state still fail. |
| R6 Parallel fixture schema race | Centralize fresh fixture initialization | H | Proved initially absent schema, actual concurrent preparation, preserved product concurrency and verified cleanup. |
| R7 Viewport claim | Correct withdrawn cause; retain measured assurance | A/I/J | No false inheritance rule; central real tests assert effective viewports; no duplicate consumer Playwright tests. |
| R8 Plan invalid JSON | Fix real stdout contract | F | Entire native/scoped-wrapper stdout parses; failure paths retain nonzero diagnostics. |
| R9 Shared test drift | Replace stale fixtures with preserved obligations | G/I | Explicit required identities and old-to-new coverage; removal/substitution/skip/empty/failure negatives. |
| C1 Preparation/runtime selection | Preserve preflight; improve supported preparation recipe | A/F/I | Maintained command chooses real runtime and reports exact missing preparation; attribution retained. |
| C2 Node/Vite/project definitions | Trace provenance; fix generation or update if implicated | A/D/I | Clean actual generated composition builds on accepted pins; stale-owned-file transition tested. |
| C3 Native API/provider/OpenAPI/analyzer wiring | Supply qualified executable integration | B/I | Real compile/export/checked client/runtime wire parity; public native seams and constraints preserved. |
| C4 Generator lock/npm syntax | Preserve lock requirement; prove runnable recipe | F/I | Native selected generator lock and real maintained argument routing; no manual client/baseline reset. |
| C5 Native test/config wiring | Supply shared current harness/example and fixture setup | B/H/I | Nondefault scalar options activate, native public features register and durable behavior is observed. |
| C6 Frontend contracts/recovery | Trace imports; align strict layout and real lifecycle | A/C/D/I | Strict build/lint and real persisted-page/session/privacy recovery; original cause only claimed when substantiated. |
| C7 Invalid wrappers/actions/sandbox | Preserve scope/action/access contracts; improve commands | F/I | Valid commands work; wrong payload/reason/scope still fail actionably; environment failures remain honest. |
| C8 Quickstart owner omission | Correct/test emitted owner-bound commands | I | Actual generated example selects a concrete configured owner; PKV002 remains enforced. |
| C9 Consumer docs/CI/private-file boundary | Trace ownership and reconcile stale entrypoints | A/D/I | Executable current workflow command/prerequisite proof plus settings/pack/private-file boundaries. |
| C10 Stale frontend/package closure | Preserve freshness guards and supported refresh | F/I | Stale outputs reject; maintained refresh/reentry passes; no silent broad bypass. |
| C11 Producer/native-receipt row | Preserve guard; prevent contradictory task edits | F/I | Structured valid alternatives; conflicting producer/evidence fails; human reviews/ancestry unchanged. |
| V1 Original-baseline unmapped inputs | Generate real bounded toolkit owners/checks | G | Real mixed Affected selection from retained baseline; future unknown paths fail; no catch-all/baseline advance. |
| V2 Archive/locks/protected history | Anchor preservation and complete inactivity checks | E/G | Rehashed-payload and props/targets activation negatives; current locks native; no old-code execution. |
| V3 Installed/public/generated provenance | Canonical full-set/source/executed-regression binding | A/G | Complete attempt originals and public/guidance sets; modified/missing/spurious inputs fail; receipts unchanged. |
| V4 Managed/setup/core metadata | Current validators plus authenticated six-file diagnosis | A/G | Real managed render/profile/architecture checks; core mismatch explained/reconciled, never merely re-signed. |
| S1 Later Docker-reset recovery | Preserve expected environment recovery and evidence scope | A/H/K | Exact owned synthetic reconciliation; pinned supported runtime; no data-loss/product-regression invention. |

### Later findings and unnumbered obligations

| Finding or obligation | Planned handling | Closure |
| --- | --- | --- |
| Missing configured identity/exception pages and JSON sign-out | B/C/D/J/K | Actual configured fresh/upgraded consumers navigate to native-owned readable recovery; machine contracts remain correct. |
| Confirmation enable/disable and unsaved extension | C/D/J | Every accepted mode/state/lifecycle/cancellation requirement centrally proven and configurable. |
| Nuplane preview.109 satellite collision | B/I/J | Fixed public packages integrated into actual new Foundation Host and verified in Program Kit closure. |
| Core Specify integrity unexplained | A/G | Exact distribution/generation diagnosis and supported current coherence; no historical rewrite. |
| Broad orphan-lock consumer repair | E/G | Three-way active/authenticated-retired/unknown model replaces absence-based admission. |
| Incomplete solution-only restore repair | E | Canonical native project-reference/output closure used consistently. |
| Archive inventory and props activation holes | G | Both independent negative probes fail in reusable checks. |
| Minimum-count substitute for reviewed tests | G | Required case/module identities and actual execution binding; unrelated green cases cannot substitute. |
| Declared repair-method name or original count as proof | A/G | Actual regression results and canonical complete original sets bound to source. |
| Database table-only and check/use ownership repair gaps | H | Complete declared object safety and atomic checked operation, or obsolete helper retired after correct deployment. |
| Fixture race regression may start after schema creation | H/J | Independent fresh initial-state proof before concurrency. |
| Standard page tests inject missing owner UI | B/D/J | Real emitted/deployed presentation proves integration; mocks remain scoped fault injection/unit evidence. |
| Stale preview.61 guidance and local-Release diagnostic | I | Active selected-version guidance and current CI recovery; historical records preserved. |
| Packet scanner false positive | A | Inspect actual generic source and positive/negative scanner cases; unsupported claims remain explicit until verified. |
| Original baseline, effort, provenance and receipts | All/K | Preserve original IDs/records and claims; new evidence describes only its actual execution/source. |
| Human/full-feature/provider/device/restart/all-copy triggers | I/K | Keep actual later application obligations at their triggers; no new acceptance or spending inferred from maintenance. |
| External sharing/privacy/no history reconstruction | A/J/K | Sanitized minimal fixtures; no private packet/log sharing, retired-business reconstruction, device installation or live-data reset. |

## L Supplemental findings from ongoing consumer implementation

These eleven findings were supplied by the ongoing US2 chat during planning and review and assessed read-only against current Program Kit and relevant current consumer tooling. They are proposed additions for this plan review. Several are consumer-integration defects or incomplete capabilities, rather than broken canonical code. The correct repair is shared support/prevention where justified, with honest attribution. This planning task has no authority to consume the other chat's paid-provider approval.

### N1 Selected Python and workflow dependency readiness

**Work:** F/G/I. The consumer-authored native runner failed to carry the selected interpreter into its .NET-to-Python child chain. Canonical repository_verification already invokes its adapter with sys.executable; do not claim that entire path was broken. The shipped wrapper separately checks interpreter/version without the workflow dependency probe already present in governance python_runtime, exposing inconsistent readiness ownership.

Reuse a canonical applicable runtime/dependency readiness contract and a documented adapter child-runtime contract. Propagate the verified selector only into owned child processes. Probe dependencies required by the selected workflow, not every optional package for every Python command. Missing dependencies produce explicit preparation/readiness errors without validation-time acquisition.

**Evidence:** recording adapter/child/grandchild tests; two synthetic installed interpreters; missing required module; wrong/stale selector/core record; fresh-shell selection. Actual generic checks must run under the intended interpreter. Do not fix this by changing global PATH or only checking the Python version.

### N2 Durable authenticated tooling witnesses

**Work:** A/E/G. A consumer checker depended on a staging source whose temporary directory later disappeared. Its local cache fallback validates the expected fingerprint but hardcodes a v5 location and manual Windows extended-path strings. Available evidence does not establish that Program Kit itself selected OS Temp; the updater's dev installation can retain a staging pointer, which is the general lifecycle issue to qualify.

Provide retained content-addressed witness storage with explicit ownership/retention independent of ordinary cache/temp cleanup. Bind its exact file set/digest, public source identity and declared local deviations. Distinguish missing, partial, recovered and modified states. Never use a recovered copy to overlook an existing modified original. Authenticate any reacquired public input and any local patch replay; keep original receipts unchanged and record recovery/location evidence separately.

Use shared Windows path handling/containment rather than consumer-specific prefix replacements. Verify source/upgrade operation on deep paths without changing device policy or bypassing provenance.

**Evidence:** remove original staging; restore exact witness; reject wrong/partial/rehashed candidate and changed existing original; deep Windows paths; unchanged historical receipts and repeatable later-session verification.

### N3 Accepted story scope and unrelated later work

**Work:** D/G/I. Program Kit already supports material projections and separates human acceptance from fresh engineering evidence. The missing capability is conservative projection of story-owned plan/architecture slices and useful scope-selection diagnostics. A whole-file classification of shared plans/graphs/verifier inputs can reopen an unchanged outcome when another story adds unrelated entries.

Extend/reuse typed projections, including the actual shared dependencies influencing the reviewed story. Report which material inputs changed and why. Unrelated additive story work can retain its original human disposition while current engineering evidence is refreshed. Shared auth/provider/policy/architecture changes affecting the accepted outcome must remain material. Source-file equality of many business files alone cannot prove that changed shared configuration is harmless.

Preserve the original review basis/decision. Narrowing a scope after approval is an explicit material assessment/authorized transition, not a rewrite claiming the old reviewer approved a different basis. A change to projection rules cannot manufacture renewed approval.

**Evidence:** two-story fixtures; unrelated additions preserve legitimate approval; shared behavioral changes reopen the relevant outcome; engineering freshness remains independent; changing projection definitions or retained review records cannot create acceptance.

### N4 Historical rendering versus current executable readiness

**Work:** A/F/G/I. Specify's renderer probes current PATH for python3/python, and ownership reconstruction reruns native rendering. A vanished alias can change rendered bytes even when historical templates/outputs are unchanged. The consumer's hardcoded historical python3 replacement is a bounded workaround, not a general rendering-provenance contract.

Record authenticated generation inputs/render profile at generation time and use that profile for historical reproduction. Validate current executable selection separately. Do not normalize arbitrary command changes or turn a missing current renderer into source-drift evidence. If exact reproduction cannot run, report that scope honestly rather than asserting a fresh render passed. Preserve historical output/receipt bytes; supported new generation writes separate current evidence.

**Evidence:** PATH/alias changes with unchanged historical bytes; changed template/source; tampered or absent render profile; unavailable current runtime versus actual mismatch; current commands continue using the verified current runtime.

### N5 Bounded current checkpoint and retained history

**Work:** F/G/I. Checkpoint instructions say replacement, but implementation retains/appends decisions/failures and counts all non-delivery fields against the summary bound. Small updates can exceed the merged limit; current output also expands accumulated provenance.

Separate bounded current-state projection from retained decision/failure history, with stable authenticated references and explicit current/history output modes. Preserve original baseline, effort, unresolved failures and human decisions. Align command guidance with actual merge/replacement semantics. Error diagnostics report submitted, merged-current and retained-history sizes plus major contributing fields; overflow preserves atomic prior state.

**Evidence:** repeated resumes and growth; concise current output stays bounded; complete history remains accessible; unresolved obligations remain visible; malformed references and atomic overflow fail honestly. Increasing limits or deleting old decisions alone is insufficient.

### N6 Active documents and frozen historical evidence

**Work:** D/G/I. The current consumer tasks target a compatibility README that the consumer's preservation inventory freezes byte-for-byte. This is an ownership contradiction, not proof Program Kit globally freezes all compatibility documents.

Expose active/historical document ownership to task drafting and verification. Detect an immutable target in a proposed output before implementation. Route current work to a mutable current index or new versioned proposal linked to preserved evidence. Provide a supported transition where ownership legitimately changes, without re-signing or weakening historical records.

**Evidence:** immutable compatibility target is diagnosed during planning; valid new proposal/current index is allowed; changed historical bytes and stale ownership transitions fail; emitted task commands agree with preservation checks.

### N7 Task source layout and selected analyzers

**Work:** F/I. A consumer task grouped several contracts under one suggested filename while the selected analyzer enforces one type per file. Current central rules already state that standard; no canonical template specifically generating that consumer filename was identified.

Make generated tasks express responsibility groups/directories or separate concrete type files without implying a conflicting source layout. Project the selected analyzer constraints at planning/scaffolding and qualify representative generated contract examples by actual native compilation. Do not suppress the analyzer or infer that every plural filename necessarily declares multiple types.

**Evidence:** representative contract-task output compiles against actual selected analyzer settings; multi-type negative fails; valid grouped responsibility still permits separate cohesive types/files.

### N8 Narrow provider operation authorization execution and accounting

**Work:** shared Program Kit provider preparation/execution adapters and relevant native public provider seams; I updates selected mechanism guidance. The observed consumer renewal command supports combined model/OCR work and existing checks correctly require that broad authority. A one-page OCR-only approval with a USD 0.01 cap, no model call, retry or fallback cannot safely authorize that command. This is a missing narrow execution capability, not demonstrated approval bypass.

Provide reusable operation-scoped preparation, binding, durable attempt accounting and recovery. Reuse the existing admission/attempt contracts; avoid consumer-specific approval booleans. Bind exact provider operation and fixture/configuration hash, serialization/request limits, allowed submissions/pages, model/fallback prohibition, SDK retry settings, deadlines, cleanup/reconciliation permissions, run ceiling and aggregate historical accounting. OCR operation polling/reconciliation must have an explicit bounded scope and must never become another submission.

Reserve durably before dispatch, exclusively consume exact authority, prevent concurrent duplicate use and retain prior reservations/uncertain outcomes. Crash/timeout after possible dispatch preserves the attempt, reservation and available operation handle; recovery cannot silently POST again. Cleanup does not renew paid authority or claim deletion without independently observed absence. Narrow OCR success cannot establish combined model/provider acceptance.

Keep provider-call authority separate from paid coding-agent authorization. Existing optional live-worker rules remain intact. No actual paid call is needed for maintenance proof; any later provider execution still requires its own exact applicable human authority.

**Evidence:** central offline recording/fake-transport tests reject model/extra-page/fallback/SDK-hidden-retry/reused-authority/changed-fixture execution; concurrent attempts cannot exceed run or aggregate caps; missing/duplicate/tampered reservations fail; postdispatch unknown is preserved; recovery never resubmits or fabricates cleanup. Demonstrate a narrow successful result with an appropriately narrow claim.

### N9 Provider configuration must match the actual composition binding

**Work:** D/F/I/J, with Foundation owning any required native settings contract support. The consumer provider read `PolicyEvidence:RootPath`, while the accepted typed composition supplies `EvidenceFiles:Root`. Direct DI fixtures repeated the invented key, so green unit tests did not demonstrate configured activation. The current repaired provider and settings metadata use the accepted key. This is an established consumer integration mistake, not evidence that Program Kit emitted the wrong binding.

Make the selected composition's emitted bindings and native settings metadata available at the point of provider/task authoring. Reuse the authoritative configuration contract rather than inventing another key or silent alias. Validate declared provider settings against their actual configured bindings before activation where the public contracts permit it; qualify the remaining runtime behavior through real registration and configured activation. Static checks must disclose their limits for dynamic accesses rather than claim exhaustive source inference. Preserve the accepted private volume/location and do not print secret values in diagnostics.

The consumer's key correction is appropriate. General prevention requires an integration case deriving its input key from the actual composition and exercising the provider through public registration. A direct fixture that hardcodes the same key as the implementation can repeat the mistake. Keep domain-specific storage assertions in the consumer; prove shared binding selection and mismatch diagnostics centrally.

**Evidence:** configured synthetic provider succeeds using the emitted binding; an invented key/mismatched metadata is diagnosed before dependent work; missing required binding fails without an alternate-key fallback. Confirm real registration consumes the configured value without changing the private location or exposing it in diagnostics. Dynamic-contract limits are explicit.

### N10 Settings-source metadata generation and validation share normalization

**Work:** A/F/I/J, with Foundation owning native export validation and the authoritative source-hashing contract. The consumer reports PKSM001 after generating a source hash from raw CRLF bytes while native export expects LF-normalized source. Normalizing the edited source and regenerating its current metadata was a valid local repair, preserving strict verification. It does not establish that a shipped Program Kit metadata generator produced the original hash.

Trace the actual selected generator and exporter before assigning the defective owner. In addition to the older local build task, independent inspection of the consumer's installed knowledge index identifies selected Foundation 0.3.5 at `ff091a2` and hash-verified source slices for `EmitSettingsMetadata` and `InspectSettingsSourceGraph` with CRLF-to-LF UTF-8 hashing. These are captured source evidence; actual selected package/export execution and original metadata generation remain to qualify at their exact versions. Supply a canonical generation/validation recipe or shared primitive with an explicit encoding, BOM and newline contract, then route maintained examples and adapters through it. Do not invent broader normalization than the native contract allows.

Qualify equivalent LF/CRLF inputs as specified by that contract, including non-ASCII text and explicit BOM/lone-CR outcomes. Real content changes must still invalidate metadata. Update only current supported metadata through normal regeneration; preserve historical receipts, source snapshots and authenticated package/archive hashes. Text canonicalization is not permission to normalize arbitrary integrity checks or re-sign unexplained discrepancies.

**Evidence:** generated metadata passes actual selected native build/export for supported text forms on Windows and CI; wrong raw hash and meaningful source edits fail; contract edge cases are documented and tested. Establish the original generator's ownership or retain an explicit attribution limit.

### N11 Diagnose and recover the selected Node/npm pair together

**Work:** F/I/J. The consumer's managed Node installation disappeared, and recorded npm command paths correctly became invalid. Restoring the required Node left its bundled npm different from the independent npm pin, causing another user installation round. Preserve exact-version refusal and user-owned device preparation. These observations do not prove a product caused the installation to disappear or establish bundled versions for every distribution.

Reuse the authoritative `.nvmrc` and `.npm-version` pair in recovery diagnostics across missing recorded-command, readiness and composition-update entrypoints. The current device readiness function already aggregates Node/npm failures; extend/reuse that capability at the failing entrypoint rather than claiming all readiness is first-failure-only. Explain that restoring Node may not satisfy the independently pinned npm version. Give ordered supported steps to select the shared Node, verify the npm bundled with that actual selection, install/select the required shared npm if needed, and regenerate evidence/restage only after both are valid.

Resolve the pair from the same selected manager/environment and verify it in a fresh user shell, including npm lifecycle child Node. Respect existing installation ownership, shared prefix and user-terminal boundaries. Do not use a temporary PATH override, repository-local tool install, pin weakening, database reset or volume replacement as recovery. This maintenance plan itself performs no device installation.

**Evidence:** recording tests cover vanished managed installation with a wrong system fallback, correct restored Node with wrong bundled npm, both pins satisfied, stale paths and fresh-shell selection. The first actionable recovery identifies both required pins and their sequence; native command/evidence checks remain strict and dependent work resumes only after actual readiness.

### Supplemental coverage matrix

| Supplemental item | Disposition | Work | Evidence required to close the item |
| --- | --- | --- | --- |
| N1 Interpreter/dependencies | Fix applicable readiness and shared adapter contract; preserve correct canonical interpreter launch | F/G/I | Verified child-grandchild runtime plus applicable missing-dependency negatives. |
| N2 Temporary witness loss | Durable authenticated retention/recovery and platform path support | A/E/G | Removed staging recovers exact witness; modified/partial/deep-path cases and receipt preservation. |
| N3 Accepted story reopened | Extend existing scoped material projections/diagnostics conservatively | D/G/I | Unrelated additions preserve approval; affecting shared changes and rule changes cannot fabricate acceptance. |
| N4 PATH-dependent historical render | Bind historical render profile; separate current readiness | A/F/G/I | Alias changes versus source changes distinguished; tampered/missing provenance stays explicit. |
| N5 Checkpoint accumulation | Bounded current projection plus complete retained history | F/G/I | Repeated resume/growth/overflow; original authority/failures/history remain intact. |
| N6 Frozen/current document conflict | Ownership-aware task output planning and current proposal/index | D/G/I | Immutable target diagnosed; valid new active target allowed; historical bytes protected. |
| N7 Contract layout/analyzer mismatch | Selected-rule-aware task examples and real compile qualification | F/I | Native generated contract examples obey selected analyzer; no suppression. |
| N8 OCR-only authority | Reusable narrow operation binding/execution/accounting/recovery | L/I | Offline exact-scope/concurrent-cap/unknown-outcome/no-resubmit/no-model/no-fallback proof. |
| N9 Provider/composition key mismatch | Authoritative binding guidance, declared-settings checks and configured public-registration proof | D/F/I/J | Real emitted binding works; invented/missing key fails without fallback or secret disclosure. |
| N10 Source metadata line endings | Trace generator ownership; align generation/native export to exact text-hash contract | A/F/I/J | Actual selected export accepts supported canonical text; meaningful changes and wrong hashes still fail. |
| N11 Node/npm recovery split | Reuse joint selected-pair diagnosis and ordered user-owned recovery | F/I/J | Missing installation/wrong bundled npm/fresh-shell cases; both pins valid before evidence renewal. |

## J Central qualification and acceptance matrix

**Owner:** each publisher for component behavior; Program Kit for configured integration and upgrade. These are central tests with disposable synthetic fixtures. Consumers supply configuration and domain/custom adapters; they do not reimplement standard mechanisms or repeat their protocol tests.

| Area | Required central proof |
| --- | --- |
| Fresh configuration | Packaged install; exact selected profile; real restore/build/export/client/package; actual public Host; actual emitted pages/assets. No manual auth writer or replacement test UI needed. |
| Existing repaired installation | Representative verified local patches and retired inputs; preview/apply; interrupted retry; preservation/conflicts; central check successors; current business-shaped synthetic behavior remains intact. |
| Authentication and recovery | Actual controls/provider/themed sign-in; sign-out; cancellation; expired/invalid callbacks; denied access; provider unavailable; local/provider uncertainty; anonymous recovery/assets; independent session observation. |
| Error representation | Application exception/404 and pre-shell neutral fallback; root/non-root/multiple shells; explicit browser versus machine purpose; safe statuses/codes; no private exception payload; existing/started/aborted response behavior. |
| Browser experience | Actual configured small/large viewports asserted, keyboard/focus, light/dark/reduced motion, accessibility, no-script recovery, separate tabs, late responses, back/forward/BFCache privacy. Physical device/assistive obligations remain honestly scoped. |
| Unsaved work | All policy modes; custom sources and optional form adapters; multiple/none/disposed sources; failure/uncertainty; changing state; repeated gestures; no protocol side effects before confirmation. |
| Native persistence | Correct real deployment/runtime grants; startup admission; real disposable initialization race and process scope; cleanup identity. Domain transaction/behavior tests remain domain obligations. |
| Runtime loading | Actual integrated public Nuplane multi-assembly and different-culture satellites, same-culture conflict rejection and resource fallback; actual Host bytes bound. |
| Tooling | Installed isolated CLIs, declared planning versus real execution, selected test scaffold, wrapper streams/runtime/cache, authored/generated/native pack state, named shared-case coverage. |
| Provenance/retirement | Exact original/source/generated/repair/retired sets; anchored archives/inactivity; tampering/addition/omission/alias/activation and stale-record negatives. |
| Supplemental lifecycle | Runtime handoff, durable source retention, scoped approvals, historical render profile, bounded checkpoint/history, active document ownership and analyzer-aligned tasks. |
| Narrow paid-operation contracts | Offline execution/accounting/recovery proof for exact OCR-only scope; no actual provider spending or broader acceptance claim. |

Use fixture fault injection to cause genuine failure paths, not to supply presentation missing from the product. Observe actual effects and effective configuration. A mocked dispatch, package hash, TRX test count or passing protocol response proves only its stated boundary.

Enumerate the currently supported composition/profile combinations explicitly, including applicable BFF, SPA-PKCE and hosted-page arrangements. Fresh and migration qualification cover each supported integration with its own native protocol semantics; BFF cookie/antiforgery behavior cannot stand in for SPA behavior. Do not silently reduce documented support to one default fixture. An unqualified combination receives a precise capability/support disposition before it is advertised as working.

Add new checks to the canonical validation inventory and affected-input/prerequisite selection. Keep costly real integration in appropriate CI qualification jobs, focused checks in development, required Windows compatibility and all Linux browser engines. Do not invent a second release checklist, a per-task full suite or a paid-agent dependency.

## Delivery order and review checkpoints

1. **Review this plan.** Confirm it represents the agreed scope before product edits. Current source/packet audit and documentation preparation are the only work completed here.
2. **Establish A.** Refresh both repositories, preserve current work, diagnose core/source-attribution gaps and freeze representative synthetic fixture inputs. Record any resulting scope change rather than fabricating a diagnosis.
3. **Implement independent fixes in reviewable commits.** E/F/G, the relevant supplemental L repairs and command/knowledge corrections can proceed while Foundation work is prepared. Fix discovered consumer-remedy weaknesses instead of cherry-picking them unchanged.
4. **Implement and qualify Foundation B/C/H native work.** Use existing public mechanisms where sufficient; extend the required runtime seams and central browser client. Adopt the corrected Nuplane closure. Complete Foundation's required maintenance/tests/build/security/knowledge work, review exact source and obtain its publication authorization.
5. **Verify Foundation public outputs.** Inspect complete successful publisher Release, package/source hashes, immutable image manifests/content and exact public knowledge. Failed lookup/test/security is a failure to repair, not permission to use unpublished source or altered image bytes.
6. **Complete Program Kit D/G/H/I/L integration and migration.** Consume that public closure. Retire duplicated local mechanisms only through verified ownership transitions. Complete focused regressions and bounded Development, including offline narrow-provider contracts and all supplemental lifecycle coverage.
7. **Run mandatory dependency maintenance before selecting the Program Kit candidate.** Refresh active external pins/locks through the workflow; add newly introduced dependencies to maintenance-policy.json; qualify the new default profile and versioned knowledge together. Preserve historical profiles/consumer locks. Repair failed maintenance and repeat affected work/qualification as required.
8. **Freeze one complete exact Program Kit candidate on main after normal review/integration.** Choose version from actual final scope and inspect the complete shipped diff. No provisional tag is needed to test candidate qualification.
9. **Qualify through the new untagged CI workflow.** Reuse only a complete matching valid qualification; otherwise dispatch qualify-candidate with the exact expected commit. Require build/Linux/Windows/security/finalize and actual complete coverage. Bind the authoritative tested payload and evidence; inspect failures and requalify corrected source honestly.
10. **Review readiness and verify promotion without publication.** Use the repository readiness skill and actual schema. Record findings, coverage limits and attributable human review. Run the non-publishing verifier. If only security expires, refresh the scan of unchanged immutable inputs; artifact availability and security freshness remain independent.
11. **Publish only the reviewed exact candidate/tag after explicit authorization.** Tagged Release promotes the qualified bytes without rebuilding or repeating deterministic acceptance. Inspect the full promotion/publication and real newly-public installation/upgrade smoke before declaring availability. Preserve and disclose partial publication on failure; failed-tag recovery uses its existing exact-source safeguards.
12. **K Upgrade claim_evaluator after public success.** Reinspect its current working state, advancing stories/data and approved reviews. Preview the normal supported upgrade, preserve original baseline/effort/patch/history/data, reconcile concrete conflicts, apply the released integration, run relevant current engineering checks and demonstrate actual standard journeys. Present for human review; do not start a later story or infer a new approval. Any actual live-data migration or destructive recovery needs its own applicable scope and authority.

The new workflow is tested in two honest stages: untagged qualification plus non-publishing verification, then actual authorized tagged promotion plus public smoke. Neither stage borrows an old-source qualification or claims an unexecuted later stage passed.

## Completion and remaining investigations

The repair batch is complete when every confirmed product defect has implemented code and relevant passing behavioral evidence; each correct guard/false diagnosis has an explicit accurate disposition; the fresh and repaired-consumer central integration cases pass; and all required publisher/Program Kit source, knowledge, security and release evidence is valid for its actual stage.

The current unresolved facts are tracked under A: six core script discrepancy causes, provenance of original C2/C6/C9 consumer files, exact scanner behavior/source evidence, and compatibility/adoption of the final current publisher dependency closure. They are included in the plan, not resolved by planning. New confirmed defects discovered there require an in-scope repair and appropriate tests. Any material change to the agreed product outcome returns for review.

No broad application acceptance is inferred: provider/paid-sensitive capabilities, all-copy cleanup, physical devices, application restart/release and story reviews remain the consumer's real obligations at their actual triggers. Maintenance preserves those requirements while proving the shared mechanisms it changes.

## Review status

All eighteen interview decisions are incorporated. An independent original-scope audit found explicit work/disposition/evidence for all 31 original numbered items and later S1, with no missing or duplicate coverage rows. It also verified coverage of all eighteen decisions and the identified consumer-repair weaknesses and unnumbered preservation/privacy/lifecycle obligations. Its two precision recommendations—every supported browser-profile combination and explicit C6 domain safeguards—are incorporated above.

The eleven supplemental findings have separate N1–N11 work/disposition/evidence rows and a read-only source-attribution assessment. These are part of the proposed review scope; they are not retroactively claimed as original report content or completed repairs. The initial mechanical and independent audits passed for 40 findings and eighteen decisions. N9–N11 subsequently extend the proposed scope to **43 distinct findings**. Revised mechanical and independent audits pass with no omissions, duplicate entries or remaining coverage gaps identified; all eighteen accepted decisions remain incorporated. The revised audit record binds the updated plan and preserves the initial 40-item audit separately. No mandatory paid execution or duplicate consumer framework/protocol test requirement is introduced.

**Current status:** draft plan and coverage review only. No product repair, Foundation publication, Program Kit candidate qualification, tag or consumer upgrade has been performed by this task.
