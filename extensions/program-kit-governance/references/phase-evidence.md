# Engineering and foundation evidence

## Knowledge and engineering checks

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
or `-Scope Affected` while coding. Retain the complete implementation baseline and inspect selection
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

## Reusable foundation proof and operation prerequisites

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
outputs stay in ignored artifacts. `task_draft.py current` exposes this readable state on resume.
No second ledger or approval dossier is required. Never edit the marker to fabricate human decisions.

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
binds their exact bytes. Changed/deleted inputs reopen only that checkpoint and retain prior decisions.
Unrelated test corrections/new commits do not invalidate every story. Re-present the repaired outcome
and retain valid prior acceptance; a fresh generic check result is not a human decision.

Use stable story/operation IDs. Elapsed wall time accrues once for the active operation and story,
including preparation, planning, builds, integration, tests and repairs, rather than summing commands.
Explicit human waiting is suspended. Save before interruption; resume the retained clock/work, never
start another ID to erase effort. Report once at 60 active operation minutes/120 story minutes with
what works, what remains, cause and smallest corrective action. Materially changed diagnosis/scope
merits an update, not a warning on every command. Owner budget revisions are explicit. Time alone
never blocks implementation; real technical, authority and human progression gates still do.

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

Archive/checkpoint the abandoned attempt and failed evidence. Install the released toolkit through
the supported updater. Amend and normally review/ratify the constitution for story-delivery-v1.
Review/select an explicit owned reset inventory; shared outputs, migrations and data need clear
ownership. Abandon old unfinished spec/plan/tasks/code/tests as active progress, preserving history.
Rerun specify, clarification, plan, tasks, analysis and implement with hooks once at owning boundaries.
Reuse unchanged confirmed bootstrap/intake intent, accepted architecture, foundations/tooling, locks
and delivered features; do not restart the whole product interview. No partial feature continuation,
real consumer/data migration or unrelated source/live-data deletion is authorized by installation.
