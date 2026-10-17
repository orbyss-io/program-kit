# Engineering and foundation evidence

## Knowledge and engineering checks

To repair a contradictory Test materialization map, create a request file with one
structured source alternative per owner. For a suite produced by a prerequisite task:

```json
{"owners":[{"owner":"tests/Orders.Tests/Orders.Tests.csproj","source":{"task":"T009"}}]}
```

For an already executed suite, use `"source":{"evidence":"artifacts/verification/<run>/result.json"}`
instead. Run the installed helper against the current task plan:

```sh
python .specify/extensions/program-kit-governance/scripts/task_draft.py render-materialization --repository . --feature-dir specs/001-orders --content-file materialization-request.json
```

The read-only result contains a proposed Markdown table. The native validator checks
the actual selected owners, retained baseline, producing-task ancestry and existing
receipt hashes. It rejects a source containing both a task and evidence, a suite
produced after its gate, missing/changed evidence and a zero-test receipt. Review and
merge that table, preserving task IDs, dependencies, effort and human decisions, then
run normal finalization. This command executes no suite and establishes no acceptance.

`phase_obligations.py project` prints concise guidance before planning and tasks. The single
implementation preflight prints implementation guidance while validating planned architecture.
The single upstream registry is `phase-obligations.json`. Its source routes identify every
canonical rule group, producer and enforcement scope, including explicit manual and maintainer
routes. The default brief includes essential constraints directly from marked canonical prose;
`--only <id>` adds examples and focused sections. Generated context is disposable.
Accepted targets, compositions and scoped technology inform the brief before source projects exist.
Treat proposed inputs as proposed, resolve scope conflicts, and avoid inheriting neighboring owners.

`phase_obligations.py check` validates the declared `eng/architecture.json` graph after-plan,
after-tasks and before implementation. Before tasks, project `--phase tasks` rather than repeating
the after-plan check. The implementation preflight is the sole before-implement hook.
Roles, edges, declared responsibility kinds/effects and provided-capability bindings must satisfy
the adopted compilation boundaries before a build. Review actual responsibility placement against
the constitution and accepted constraints. A declared graph pass cannot certify that labels are true.
An empty initial graph or pure Core utility remains legitimate; it does not certify later runtime
bindings. Compiled inventory and actual activation/resolution/lifetime tests establish those checks.

Keep design choices and required tests in normal plan.md/tasks.md. Resolve retained feature-plan
decision prerequisites there using the phase-context recording procedure after normal design review.
Native planning eligibility and implementation preflight consume the same current scoped records.
Plan drafting remains possible while these design decisions are pending. Missing old metadata or
stale sections require affected design review; preserve old intake, approvals, ADRs and ledger bytes.
Compatibility execution, delivery and production obligations retain their own proof and due phase.
Implement behavior and
architecture tests in the repository. Use `eng/Invoke-RepositoryVerification.ps1 -Scope Focused`
or `-Scope Affected` while coding. Retain the complete implementation baseline.
When authoring quickstart.md, run `python eng/repository_verification.py
--repository . --list-owners` and include the relevant emitted command with its
actual test-project path or toolkit-check ID. If the owner is not materialized,
retain that prerequisite explicitly and refresh the quickstart after creating it;
a bare Focused command cannot execute or establish coverage. Inspect selection
with `-Plan`; do not select by the last edited file alone. Progress saves and resumes earn only
checks invalidated by changes. `phase_obligations.py finish` returns progress for open tasks/drafts;
closed features or an explicit `--handoff` run complete acceptance once.
These paths consume the retained human story review state before progression/closure; checked tasks
or an engineering pass never manufacture human acceptance. Required deferred reviews remain due at
feature acceptance. Absent hooks invoke the same preflight/finish validators explicitly. See
`phase-evidence.md` for scoped repairs/deferrals and decision freshness; time warnings never block alone.
The scoped plan distinguishes needed checks, reusable successful coverage and unresolved failures,
including prior run references and reasons. Reuse requires matching transitive source, build,
configuration, generated, toolchain and controlled environment inputs; filtered coverage cannot
clear a broader failing regression. Keep successful partial project outcomes if a later project
fails. An unfiltered multi-project Focused selection states its reason and selected scope. Use the
maintained wrapper and supported runner adapter for accepted consumer test systems, preserving
these safeguards. Unknown evaluated inputs must be explicitly owned before narrowing verification.
Keep one compact current checkpoint in tasks.md rather than an append-only command journal; logs
and detailed failure history stay in existing ignored artifacts, with unresolved references retained.
Run `eng/Invoke-RepositoryVerification.ps1` for complete engineering acceptance; it has no dependency on
installed extensions or governance history. Analyzer errors,
architecture violations and failed relevant tests prevent completion. Normal code review assesses
semantic judgments and conditional choices that cannot be proven by static analysis. Report
command execution, declared/compiled structure, behavior tests, semantic review and human acceptance
separately. Successful command exit does not establish all consumer scenarios or overall acceptance.
Roadmap status is consumer-owned status, not a new test receipt. The old `verify-delivery` writer is
retired; explicit historical audits remain readable without becoming ordinary development gates.

No obligation-design/review, semantic-contract, verification-plan/results, architecture-proof
or API-proof attestation is mandatory. Historical evidence can be inspected through
`historical_phase_evidence.py`; it grants no new approval and is not a development prerequisite.
Keep scoped exceptions and their reasons in engineering policy/ADRs and normal review.
Never manufacture passing history or change old hashes to imply current execution.

The verification wrapper selects the absolute Python runtime recorded in
`.specify/python-runtime.json`, or an explicitly selected matching `SPECKIT_PYTHON`,
and validates the current executable/version before dispatch. Without a record it
checks the installed device command. A missing, invalid or stale interpreter requires
repair in the user terminal or explicit core regeneration; verification does not
install Python or mask PATH.

Repositories with provider integration own `eng/ProviderTestEnvironment.psm1` and its
exported `Invoke-WithOfflineProviderTestEnvironment -Action <scriptblock>` function.
Declare `"providerIsolation": { "required": true }` in `eng/verification.json` when
routine checks require that isolation. A missing or invalid required module blocks
verification before child execution. The module scopes consumer-defined credential
clearing and offline mode to all maintained acceptance/scoped routes and restores the
parent environment in `finally`, including failures. Keep credential names in that
consumer module; never emit their values. Repositories without provider integration
remain supported. Direct custom commands need the same consumer isolation boundary.

## Reusable foundation proof and operation prerequisites

Before paid prerequisite preparation, settle accepted selection/placement, normal sync,
current executable fixtures and the complete native lock-renewal batch. Preview impact with
`bootstrap_lifecycle.py invalidation-preview --changed-path <relative-path>` (repeat the option).
The forecast preserves current broad whole-selection bindings: even an unrelated placement
change can invalidate provider evidence when independent closure is not demonstrated. It also
shows bound input changes and the latest failed/incomplete attempt. It executes no proof, closes
no ledger item and grants no spending or human authority. Run normal prerequisite validation
after the actual changes; a preview is not acceptance.

Use `fixture_readiness.py --repository . --contract <old.contract.json> --identity <new-id>`
to preview current fixture pickup. Review its `planDigest`, then use the same arguments with
`--apply --plan-digest <digest>` to archive original bytes and write a distinct current draft.
Never edit old inputs/receipts to imply new execution. Materialization is not a provider proof;
the normal preparation/restore/check path must validate the draft. Existing or incomplete pickup
outcomes require inspection and a new identity, never an automatic retry/reset.

Keep any deliberate paid freshness renewal separate: exact new authorization and attempt state,
unchanged old reservations/unknown outcomes and aggregate ceilings, and no automatic retry or
fallback. Previously approved spending cannot authorize changed inputs. The optional paid coding
worker harness retains its own distinct phase-specific one-use manifests; fixture pickup does
not create or consume them. No new universal approval dossier is introduced.

Preparation derives exact executables/versions, Linux Docker/socket access, image digests and
required browser launches from the recipe. BFF requires Chromium before its first container;
that preparation does not move the later full product browser harness or complete T084.
Missing tools/images/browser support pause dependent behavior for user-terminal preparation.
An installed shared base Python can be selected explicitly with `PROGRAMKIT_DEVICE_PYTHON`;
it is validated against device policy and does not override the separate core workflow runtime,
install software or change PATH.

A supported foundation composition inherits exhaustive component tests from its exact
qualified packages. Maintained setup checks verify the consumer's selected configuration,
binding, activation, authentication and applicable provider integration. Successful file
generation does not establish that readiness. Reuse is bound to exact package/template bytes,
captured profile, configuration, admitted theme changes, service/setup inputs and environment;
a newer failed/interrupted run or an empty selection establishes no acceptance.

The first-code, web and persistence obligations still require their applicable coverage.
They do not require consumers to reconstruct generic reporting, provisioning, readiness,
restart or fault-injection infrastructure. Use maintained setup tooling and the accepted
native runner adapter. Add application tests for real authorization/owner predicates,
transaction contents, conflict outcomes, uncertain commit, replay and recovery. Generic
connectivity or race tests cannot prove those application contracts. Put enabling work
beside the first operation that consumes it; preserve due security/provider/authority
gates. Future independent operations do not wait for a universal foundation phase.
Materialize known scaffold batches first, run maintained generation/configuration/build/integration
checks before dependent behavior, then add missing consumer-specific tests. Select verification by
changed responsibilities/uncertainty, preferring meaningful test-first for critical behavior/bugs;
wiring can use immediate checks and refactoring existing regressions. Do not duplicate publisher suites.

Configuration decisions link `docs/architecture/foundation-configuration.md` and the
redacted settings view. Identify the value's owner, provenance, constraints and lifecycle,
including whether activation-effective binding was actually observed. Product compatibility
policy and protocol identities retain their controlled change procedure. Keep secrets out
of prose, diagrams, logs and public browser settings. Normal artifacts and compact task
progress provide evidence; no additional checkpoint receipt or approval dossier is required.


## Story delivery and human review

### Compact state and maintained transitions

Use the existing current-checkpoint marker in tasks.md. `task_draft.py checkpoint` replaces current
progress while preserving the embedded `delivery` state: every story/explicit early checkpoint,
engineering/human dispositions, reviewer, presentation, decisions, basis and elapsed effort. Detailed
outputs stay in ignored artifacts. `task_draft.py current` exposes a bounded current projection on
resume, including unresolved-failure counts and retained-history references. Use `current --history`
for complete progress and delivery provenance; `--history-sha <reference>` selects an earlier
progress-history prefix. These integrity references never renew human acceptance.
No second ledger or approval dossier is required. Never edit the marker to fabricate human decisions.

The current progress summary is bounded to 8 KiB independently of the 1-MiB retained delivery
state. Storage version 3 interns identical review bases by verified SHA-256 reference inside
that same checkpoint; `current --history` expands them into independent readable objects. Legacy inline
history remains readable and migrates only through the normal atomic save. Repeated review and
deferral cycles preserve every original decision and basis. Missing/tampered references or a
full retained-state budget stop the write; never delete provenance to fit another decision.
Current prose/checks replace their projection; decision, failure and resolution records remain
retained without appending a journal for each resume. Overflow reports submitted, merged-current,
retained-history and retained-state sizes plus their largest contributing fields, preserving the
prior state atomically. Open failures remain binding in normal continuation guards.

Submit a small JSON request with `python .specify/extensions/program-kit-governance/scripts/task_draft.py
delivery --feature-dir specs/<feature> --content-file artifacts/<request>.json`. These are scoped
workflow transitions, not engineering prerequisites for independently runnable builds/tests.

| action | Required request fields and effect |
|--------|------------------------------------|
| initialize | `baseline`, `source` of actual requesting-human conversation. Requires fresh spec/plan policy markers, a normally ratified constitution, finalized story/operation/task maps and no old implementation checkmarks. Default owner/reviewer is requester. |
| start | `operation`; validates progression before product work. `purpose: repair` or `diagnose` permits only repair of the active presented outcome. Same stable work IDs retain effort. |
| engineering | `checkpoint`, `checks` with actual relevant passing artifact paths. Requires checkpoint tasks complete and no retained technical failures. Never establishes human acceptance. |
| present | engineering fields plus `basisPaths`, `entryPoint`, `preparedData`, `walkthrough`, `expected`, `limitations`. Exercise the actual integrated journey first; disclose simulated externals. Pauses for review. |
| decision | `checkpoint`, `verdict` (`accepted`, `changes requested`, `deferred`), `actor: requester` and actual explicit `source`, or an explicitly supplied GitHub `reference`. Deferral requires bounded `permits` operation IDs; broader batches require `actor: owner` and the owner's source. Deferred reviews remain due. |
| verify-reviewer / assign | Owner supplies explicit `source` and nominated `login`/optional `host` to verify-reviewer. Present returned stable ID/login/reference for actual human confirmation. assign adds `checkpoint`, `role`, `confirmedId` and that `confirmation`; a changed ID is rejected. `role: requester` explicitly restores conversation review. |
| early-checkpoint | `actor: owner`, actual agreed `source`, new `checkpoint`, `story`, scoped `taskIds`. Never silently turn every operation into a required human gate. |
| budget | `actor: owner`, explicit `source`, `story`, optional `operation`, positive `minutes`. Revisions preserve accumulated effort. |
| scope | `actor: owner`, explicit `source`, exact affected `stories` after updating existing artifacts. Reopens only affected outcomes; stable operation identity/effort is preserved. |
| reuse-review | `from` accepted earlier checkpoint and target `checkpoint`; allowed only when the unchanged complete story outcome and all its tasks were covered. Retains original human source. |
| status / wait / suspend / resume | status accrues elapsed time and reports first threshold crossings. wait suspends explicit human waiting; suspend records stopped session work before interruption; resume reactivates accounting for authorized repair/work. Resume grants no progression authority. |

Owner powers grant neither spending/publication nor arbitrary review impersonation. Corrections to
existing requirements stay in the current story; consequential new scope requires the owner's actual
decision and updates to affected artifacts. Optional improvements can be explicitly backlogged;
required defects cannot be relabeled or waived. Early checkpoint acceptance is reused when it genuinely
covers the unchanged complete story outcome; record that coverage rather than ask duplicate acceptance.

`implementation_preflight.py` and `phase_obligations.py check --phase implementation` validate entry
and resume. `start` validates each operation transition. `phase_obligations.py finish` validates
progress/closure and `finish --handoff` validates formal handoff. Required pending/changes-requested/
stale/deferred reviews cannot become overall acceptance even with all engineering boxes checked.
Absent hooks use these same entry/finish paths explicitly. Engineering `verify` and native commands
remain independent; their success never supplies human acceptance. The toolkit cannot prevent edits
outside its workflow and claims no agent-supervisor control.

### Freshness and effort

Name actual implementation/configuration inputs covering user meaning, workflow, authorization,
persistence and effects in `basisPaths`; include relevant generated/build/policy inputs. Presentation
binds their exact bytes. Legacy changed/deleted inputs reopen only that checkpoint and retain prior decisions.
Unrelated test corrections/new commits do not invalidate every story. Re-present the repaired outcome
and retain valid prior acceptance; a fresh generic check result is not a human decision.

New presentations may provide `materialScope` version 1 alongside `basisPaths`. Every raw input must
be classified exactly once: `file` binds exact bytes; `json` binds the complete canonical JSON;
`foundation-composition` version 1 selects named `hosts` and `environments` and includes the whole
shared host startup closure; `verification` version 1 selects relevant test `projects` and retains
global verification policy plus every group touching those projects. Use the maintained
`review_material.py` projection; arbitrary JSON pointers or path exclusions are unsupported.
Include selected source, generated activation/settings, project/build/dependency closure and public
contracts in the other basis inputs. Architecture and resolved output use full `json`/`file` bindings
until a supported narrower projection exists; do not discard their provenance hashes manually.
The projection definition and executable implementation are hash-bound. Raw-only changes retain the
actual human decision but require renewed engineering checks before progression or closure. Material
host mounts, authentication, provider settings, outcome/expected results or limitations reopen human
review. Unknown/deleted inputs, unsupported projections and unprovable legacy history remain pending.
An `engineering` transition renews raw-input freshness only with actual successful relevant artifacts;
tests never create acceptance. Original decision objects and their raw basis remain unchanged.

For a new review, `story-document` version 1 can project an explicitly partitioned Markdown plan.
Its input row names `stories` (the reviewed outcome's complete story closure) and `knownStories`
(the reviewed finite set of sibling identities). Delimit a region with exact whole lines
`<!-- program-kit:story-start US1 -->` and `<!-- program-kit:story-end US1 -->`.
All prose outside regions remains shared material; all selected regions remain material.
Only bodies of already declared independent siblings are omitted. Include a sibling in `stories`
whenever its behavior influences the reviewed outcome; markers cannot establish independence.
Unknown, duplicate, nested, mismatched, unclosed or fenced-code markers are errors. Changing
the finite known set, selection or projection implementation cannot manufacture acceptance.
Do not automatically add markers or narrow an earlier review: existing whole-file authority,
decision, reviewer, basis and effort remain historical evidence. A retrospective narrowing needs
a separately authorized material assessment; it is not supplied by this projection.

Run `task_draft.py review-material --repository . --feature-dir specs/<feature> --checkpoint US1`
for read-only per-input raw/material diagnostics. It writes no checkpoint, grants no authority and
does not renew engineering evidence. Its output distinguishes a changed projection policy from
changed reviewed material. Architecture/solution/build/package/runtime closure remains under its
existing full bindings until a supported, reviewed projection/transition establishes that scope.

New presentations can explicitly select `architecture-closure` version 1 for
`docs/architecture/architecture-map.json` with an `elements` array. The native
validated canonical projection follows actual ownership and boundary dependencies
to a fixed point, retains decisions and complete shared authority/configuration,
and includes relevant journeys/contracts/provider and failure ownership. Ancestors
remain shared without automatically owning every sibling implementation. Projection
and native model/schema implementation hashes remain part of the original policy.

For a plain C# SDK solution, `solution-closure` version 1 names its `.slnx` `path`
and original entry `projects`. It binds selected forward project dependencies,
source files and shared build/SDK/configuration policy, including newly added selected
source files. Only disconnected, explicitly nonpackable library members can be
omitted. This bounded policy rejects packages, custom/conditional/imported/dynamic
MSBuild, alternate SDKs, solution configurations/folders, external/aliased inputs
and broader output policy. Retain those inputs whole or use a separate explicit
native material assessment; do not infer independence from filenames.
Shared or unknown policy remains material. Fresh native build, package and runtime
evidence is still required independently of an unchanged human review projection.

For an existing accepted review, a separately instructed owner may use the `delivery` action
`assess-material`. This records an exact retrospective assessment; it never narrows the old
`basisPaths` or changes the presentation, reviewer, decision or measured effort. It grants no
authority to perform an assessment without that actual owner instruction. Solution membership
and architecture remain whole-file inputs. An additive member is not inherently nonmaterial.

The request names `checkpoint`, `actor: "owner"`, actual instruction `source`, the SHA-256 of
the canonical original decision (`decisionSha256`), current successful native `checks`, and a
`changes` row for every changed basis input. Each row supplies `path`, retained exact `before`
`{path, sha256}`, `afterSha256`, `conclusion: "nonmaterial"`, a concrete `rationale`, and separate
`effects` conclusions for `build`, `dependencies`, `packaging` and `runtime`. Inspect the actual
diff and effective closures to reach those conclusions. Passing regressions alone do not prove
nonmateriality. A material change requires renewed outcome review instead.

Read-only `review-material` supplies `decisionSha256` and the reviewed/current input hashes.
Refreshing engineering checks does not turn the current raw hashes into a new human basis.

The command rejects omitted/extra inputs, stale hashes, missing before bytes, failed technical
checks, unfinished tasks, wrong actor/decision and attempted scope changes. It appends a
separate assessment event binding those exact snapshots, evidence and current policy. Later
input, evidence or projection-policy changes invalidate its applicability; they cannot borrow
the earlier assessment. Preserve its before-byte and check artifacts. Deterministic fixtures
use simulated decisions and cannot establish real consumer acceptance.

The retrospective event also binds a conservative current engineering context: authored
`src`, `tests`, `eng`, `web`, `contracts`, root inputs and native restore observations. Newly
introduced solution-member sources and project configuration therefore cannot change later
under the authority of an earlier solution-only assessment. This is an exact-state transition;
further unrelated authored work can require another explicit assessment. It is not automatic
semantic independence detection or a narrower architecture/solution projection.
Subsequent assessments cover changes to that bound context as well as original basis inputs.
An added context input uses `before: {"absent": true}` only when the prior complete context
proves its absence; a removed context input has an explicit null `afterSha256`. Existing
inputs still need retained exact before bytes. All earlier assessment originals and evidence
must remain intact; a later event cannot hide damage to the earlier chain.
When the outcome changes materially, a fresh `present` retains the earlier accepted
presentation and assessment chain in `materialAssessmentHistory` and requires a new human
decision. It cannot reuse the older decision to approve the new presentation. This preserves
history without preventing normal renewed review.

An owner's existing explicit deferral can retain permission for the same named operations while
changed engineering or review evidence remains due. Refresh preserves that scoped permission;
it does not turn a stale decision into acceptance. The original owner identity, assignment,
presentation and permits remain bound. Changed operation meaning invalidates affected permits.
Other operations, unmet enabling tasks, recorded technical failures and feature closure stay
guarded. Requester deferral does not acquire the owner's broader continuation authority.

A parser dependency pin alone does not identify the executing runtime. Qualification evidence names
the actual runtime, packaged closure, configuration and exercised deferred paths, and proves only
the demonstrated admission and resource guarantees.

Use stable story/operation IDs. Elapsed wall time accrues once for the active operation and story,
including preparation, planning, builds, integration, tests and repairs, rather than summing commands.
Explicit human waiting is suspended. Save before interruption; resume the retained clock/work, never
start another ID to erase effort. Report once at 60 active operation minutes/120 story minutes with
what works, what remains, cause and smallest corrective action. Materially changed diagnosis/scope
merits an update, not a warning on every command. Owner budget revisions are explicit. Time alone
never blocks implementation; real technical, authority and human progression gates still do.

A deferral permitting the active operation is authorized work, so its clock keeps accruing when
all other checkpoints and enabling tasks permit it. A genuinely blocked operation is human waiting;
an explicit suspension stays suspended. Resume restores accounting only for permitted work and
grants no new authority. Preserve accumulated effort, budget revisions and original corrections.

### Optional authenticated GitHub decisions

Use the existing authenticated `gh api` read route. Bind a nominated account only after verifying
its stable numeric ID, host, login/reference and the human's assignment confirmation. Repository
ownership, commit authorship or the CLI's connected account never identifies the requesting human.
Retrieve only a supplied exact issue comment, PR review or review-comment URL. Verify its source URL,
human author/stable ID against the assignment and exact checkpoint scope. A generic approval is pending.
The reviewer supplies an explicit marker in that decision's body:

```text
<!-- program-kit:story-decision {"feature":"specs/001-example","checkpoint":"US1","basis":"<review_digest(presentation)>","verdict":"accepted"} -->
```

`task_draft.review_digest` hashes sorted JSON of basis, covered outcome, expected results and limitations,
so changed user meaning cannot reuse an older same-code decision. Deferred markers also include the
exact `permits` list. The body must contain one unambiguous scoped decision. Verify it through authenticated read, not
a user-provided JSON response. Offline/unavailable/wrong-author/out-of-scope decisions remain pending;
preserve established decisions through outages. Owner reassignment is explicit, never an automatic
fallback. Fixture identities/decisions are simulated and establish no real human acceptance.
Posting requests, polling and monitoring need their own explicit authorization.

### Fresh-feature adoption

For the diagnostics-patch restart, use recipe `fresh-feature-delete-v1`. Keep the confirmed
specification intake. Install the published toolkit through the supported updater and refresh all
installed phase commands, skills, templates and hooks. Ratify any actually changed constitution
policy through its normal route. Select the complete unfinished specification and its exclusively
owned implementation, tests, frontend and contracts; reconcile its shared registrations separately.
Delete the old attempt with `task_draft.py reset` and request `method: fresh-feature-delete-v1`.
This route removes the entire selected specification directory and creates no content archive.
Clear owned derived build/runtime outputs and stale phase evidence through their maintained owners.
Do not consult old source, archives, Git history or old attempt transcripts to reconstruct the work.
Execute **specify itself**, clarification, plan, tasks, analysis and implement anew, with hooks once
at owning boundaries. The new attempt receives only retained confirmed intake, current accepted
architecture and installed foundations/tooling/dependencies. Old checkmarks, reviews and receipts
are not new progress. Unrelated shared work and live data are outside this reset. Historical
`fresh-story-delivery-v1` remains a separate older recipe; it is not this patch's restart route.
