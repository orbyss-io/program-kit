# Consumer upgrade and migration planning method

The maintained initializer and native CLI bridge retain original generation
profiles under `.specify/program-kit/render-profiles`. Each record binds actual
native writes, the selected interpreter literal, installed producer/template hashes
and original inputs; later component refreshes retain prior records and do not
assign new provenance to untouched outputs. Historical comparison re-renders from
authenticated installed sources with that recorded selection, without executing
the old interpreter. Current device/PATH readiness remains a separate check.
Preserve this history with the installation. Missing, changed, detached or partial
records require explicit ownership reconciliation; never backfill an old alias
from today's PATH, normalize arbitrary Python spellings, or rewrite historical
records. Unwrapped third-party CLI writes supply no Program Kit generation record.

Use the exact extracted release outside the consumer. The conversation owns semantic
inspection and consequential questions; deterministic helpers inventory, persist and
verify bounded contracts. No helper accepts an ADR or confirms product intent.

`scripts/consumer_upgrade_workspace.py prepare --source <consumer> --target <fresh sibling>
--release-root <release> --branch <upgrade-branch>` selects a committed clean baseline.
Commit intended authored untracked work first. Owned ignored setup is archived by an
explicit file inventory and reproduced exactly, including registries, integration
manifests and retained profile snapshots. Customization remains byte-for-byte; conflicting
tracked installation assets stop preparation. Arbitrary caches are excluded. Re-establish
schema runtime with its existing setup command, then repository readiness locally;
relocated historical proofs are not fresh results. The source checkout remains usable.
The preparation ledger and archive live in source artifacts. `resume --ledger <relative>
--source <consumer> --target <isolated>` resumes an interrupted owned preparation.
`abandon` preserves the isolated evidence and source setup; clean up only owned paths
after review. It never resets source or removes user edits.

The installed `consumer_upgrade.py` uses one `.program-kit/consumer-upgrade.json` record:
source/target and workspace, findings/decisions, bounded migration briefs, checks and
append-only events. Stage distinguishes preparation, assessment, convergence and
activation. Low-level updater transactions and normal architecture/feature documents
retain their owners. Application builds never require this record.

Run `assess --guidance <verified release guidance>` in isolation. Inspect inventory and
cumulative semantic descriptions alongside actual code, contracts, customization,
architecture, unfinished features and exact dependency inputs. Signals identify candidates;
they cannot prove incompatibility or semantic safety. Superseded defaults are joined to
target semantics. Missing history (including versions before 0.12.5) requires actual
layout inspection and honest uncertainties, never invented authority or age-only blockers.

Group questions by actual adoption/contract and dependency closure. Offer supported
retention and valid optional adoption. Use normal architecture/constitution review for
substantive changes and `dependency_profiles.py draft/accept` for exact dependency
transitions. Use `decide --id <change> --input <amendment.json>` to record disposition,
rationale, concrete scope and evidence paths, plus `retainedCompatibility` for retention
or deferral. Set `substantiveChange` and `decisionId` when an Accepted ADR is needed.
An `adoptDependencyProfile` names the accepted resolution SHA-256, not the newer default.
Unchanged product confirmation and accepted bootstrap history carry forward.
After executed correction use disposition `corrected` with resolutionMigrations naming
the current completed migrations covering that finding. Planning cannot discharge it.

Offer an optional software update review once during the upgrade: keep current versions,
review qualified dependency profiles, or review all repository software. Honor the
consumer's existing choice. Declining or deferring this review leaves installation and
retained dependency authority intact; the offer creates no additional upgrade gate.
The standalone updater also prints this invitation and includes it in `--plan`.

For a profile review, run the installed building-block `dependency_profiles.py list` and
compare the captured exact profile with available qualified profiles. Show current and
proposed package/tool/image versions, qualification scope, limitations, affected activation
closures and consumer migration work. The release's qualified default is an available
candidate; verify its applicability to this consumer before recommending adoption.
Report newer publisher versions outside the registry as requiring qualification;
preserve historical qualified profiles and identify the next action to obtain a qualified candidate.
Use the existing `draft --profile <id> --target .` and reviewed `accept` transition when
the consumer chooses a profile. Preserve originals and renew only affected contracts,
engineering pins, native locks and compatibility checks through their maintained owners.

For the broader review, inventory the actual repository's package manifests and locks,
SDK/runtime and toolchain pins, CI actions and container images, including software outside
the Program Kit profile. After the consumer opts in, verify newer stable versions against
official registries and publisher release guidance. Include current/proposed versions,
source links, support/security status, breaking changes, peer/engine constraints and the
required tests in a grouped proposal. Identify unpinned inputs and failed lookups honestly;
never describe unavailable metadata as up to date. Prereleases need an explicit choice.
Assess related packages as compatible groups; the newest individual versions may require
a coordinated migration. Profile software uses the qualified transition above; other
software uses its native manifests, lockfiles and existing consumer review authority.
Choose updates before changing pins or locks, then perform affected restore/build/test and
security checks. Shared device installations follow device-toolchain-policy.md and remain
human-owned. This consumer review does not invoke Program Kit's publisher-maintenance
workflow or start a paid worker. Keep historical accepted pins and evidence until the
selected transition is reviewed and verified.

`brief --input <brief.json>` records only bounded work: stable id, origin, reason/evidence,
scope (`owners`, `contracts`, `paths`, `features`, `shared`), outcome/invariants, trigger,
duePhase, dependencies, maintained method, uncertainties and nextAction. Status is
conditional/planned/analysis/implementation/deferred/blocked/completed. Group a shared
contract migration once across its actual consumers. Use maintained recipes in
`consumer-migration-recipes.json`; `consumer-specific` permits a bounded reviewed proposal
when none fits. Deferral needs credible supported retention. An upgrade-due incompatibility
cannot be deferred. Trigger conditions are investigated before promoting a conditional brief.

At `pickup --id <migration>`, inspect current inputs and recipe; create ordinary detailed
requirements/plan.md/tasks.md/tests only for that work. Reopen changed dependent inputs,
resolve concrete affected code/contract paths in the brief before binding verification;
owner names alone cannot prove that code inputs are current.
resolve consequential choices through their normal route and link `--plan <plan.md>`.
Then implement, `verify --id <migration> --input <check-vectors.json>` and `complete --id
<migration> --input <semantic-review.json>`. Checks are explicit local vectors with id,
command and affected flag; no shell expansion. Completion requires actual current passing
checks, normal plan/tasks and semantic review with outcome, invariantsVerified, provenance
and local evidence. A plan, compiler/graph pass or installed package alone cannot close
the migration. Deployment, destructive data changes and external rollouts need separate
authority/resources/recovery; workspace restoration cannot reverse them.

`reconcile` identifies affected existing features and the earliest affected phase. Edit
only affected architecture/spec/plan/tasks in place. Preserve requirements and saved task
IDs/completed work. Use task_draft resume for marked drafts; unmarked tasks remain valid.
Run normal analyze and preflight at the repaired boundary. Tasks-phase work does not
automatically restart specify; a deliberate restart remains possible when intent changes.

`scan --input <request-or-brief.json> --phase specification` accepts architectureScope,
contracts and affectedPaths before a feature directory exists. `--feature-dir <existing>`
refines scope during normal planning/tasks/implementation. Owners, neighbors and touched
contracts are projected through the existing scope reader. Output is regenerable; carry
real dependencies in the existing plan/tasks. No per-feature upgrade dossier or generic
bootstrap gate is created. Unknown scope is a limited finding, not a fabricated pass.

New discoveries use `discover --cause <cause> --input <brief.json>` immediately: classify
detectable-omission, activated-condition, changed-inputs, new-scope or unresolved-cause.
Include discoveryEvidence and local recovery action. Preserve earlier findings; do not
rewrite history to make discovery look anticipated. Demonstrated omissions require a
semantic-review regression object with a local path and an actually executed checkId
at completion. Only affected work and due phases are blocked.
Escalate to maintenance only when a supported local correction cannot be established.
For an existing conditional/shared migration, `revise --id <migration> --cause <cause>
--input <amendment.json>` appends the prior brief to history and records changed concrete
scope, trigger evidence and recovery without creating a duplicate migration. Re-enter
focused analysis and current verification; stale completion cannot carry forward.

Before mutation run `baseline --input <check-vectors.json>` for relevant known conditions.
Use workspace `install` to invoke the maintained updater with a deliberately scoped
SPECIFY_INIT_DIR. Direct updater rejects a different inherited destination. Run required
affected checks and resolve all applicability/retention questions before claiming prepared
upgrade. Unrelated baseline failures may remain identified; affected verification must pass.
`status` separates toolkit convergence from actual checks, decisions and destination activation.

Before integration merge/rebase intervening source into the isolated branch under consumer
authority, reassess affected inputs and verify the combined result. Workspace `integrate`
records destination HEAD, source delta and ignored setup changes. Commit/review the candidate,
then merge reviewed source under consumer authority. Git merge cannot promote ignored setup.
`activate --target <isolated> --destination <consumer> --input <destination-checks.json>`
archives original destination inputs, reproduces the verified release there through the
updater and reruns required checks. Changed source or installation inputs stop stale
activation. Failure/observed interruption archives diagnostics and restores original setup;
content-addressed installation originals altered only by Git newline conversion are
restored to exact candidate bytes after checking the reviewed Git blob and both copies.
Other differences remain conflicts; recovery retains the original destination bytes.
conflicting consumer edits stop recovery without overwrite. `recover --ledger <relative>`
resumes a preserved recovery. Keep original recovery assets until destination acceptance.
An abrupt process/host loss retains an activating ledger. Inspect its owned mutation
surface, stop any surviving children, then supply `recover --input <observed-state.json>`
with processesStopped, actual reviewProvenance and the exact current path/hash inputs.
Changed inputs reject that recovery without overwrite. Source integration remains a Git
decision; recovery never resets a reviewed source merge or discards application edits.
Input inventories are checksum-bound generated views linked from the small coordination
record. Activation transports only these explicit views; executed proof logs and runtime
caches do not become current destination results. Destination checks run there afresh.

`export --output <fresh-local-report.json>` creates a bounded field-allowlisted sanitized
report with versions, findings, identities, phases, expected/observed outcomes and check
results, uncertainty/recovery and provenance/redaction/truncation metadata (at most 64 KiB). Record a short
reproduction and recoveryOutcome in the coordination record. Inspect the report for
consumer-sensitive facts before sharing. Original logs, architecture and source remain
local unchanged; the summary stays useful when original run retention expires. Sending
is an explicit consumer action; this workflow sends nothing.

## Fresh story-delivery adoption

Unfinished features adopting the diagnostics patch use `fresh-feature-delete-v1` and the current
`phase-evidence.md` restart instructions. Preserve confirmed specification intake and unchanged
accepted product architecture. Delete the complete old specification and all exclusively owned
implementation/test/frontend/contract files, then reconcile obsolete shared registrations and clear
owned derived outputs. Select the concrete complete inventory; the delete-only reset creates no
content archive. Old code, archives, Git history and attempt transcripts are not learning or reuse
inputs for the fresh attempt. Installation alone performs none of these consumer deletions.

The supported updater regenerates every installed Spec Kit integration and its phase commands,
skills, templates and hooks. Then execute specify itself, clarify, plan, tasks, analyze and implement
from the retained intake. Reusing the old spec.md or merely resuming implement is not this route.
Prior phase state, checkmarks, human reviews and test receipts cannot establish new progress.
Keep unrelated shared work, foundations/tooling, dependency history and live data outside deletion.
Historical recipes retain their earlier applicability; no mid-implementation continuation is offered
for this fresh diagnostics-patch attempt.

## Retained exact tooling source

Before the maintained updater mutates components, it retains the complete actual
release source under `.program-kit/tooling-witnesses/sha256/`. The original upgrade
attempt and new migration receipt bind the exact record digest and original release
fingerprint. This location is durable evidence, outside ordinary caches/scratch;
retain it with its installation history. No automatic cleanup or eviction is provided.
The composite publication includes `program-kit-source-witness.json`, generated
from the actual packaged files and all five component inventories. Publication
qualification authenticates its enclosing archive and producer. A checksum or
this manifest alone cannot establish public origin; explicit local sources retain
their disclosed local scope and gain no publisher or application acceptance.

Run the current installed helper in a later session:

```sh
python .specify/extensions/program-kit-governance/scripts/tooling_witness.py verify --receipt .program-kit/installation/migration.json
```

The returned retained archive is bounded read-only comparison data. Historical
projects/props remain inside the archive, outside active build/dependency discovery.
Never extract into an active source tree, import or
execute its scripts, replay local patches, renew evidence or alter an old receipt
to make a comparison pass. Missing original staging can use the retained original;
an existing partial or modified original fails, even when the retained copy is good.
The complete original file set, packaged witness and both platform fingerprint
orders are checked. Project moves preserve the relative retained binding; the
original staging location remains historical rather than being silently rewritten.

If retained source alone is missing, explicitly reacquire the original input under
its original provenance, then run `recover --receipt <original-receipt> --candidate
<exact-original-release>`. Recovery validates every original byte and records a
separate location/recovery event. Wrong/rehashed candidates, modified or partial
existing copies, missing record authority and unknown legacy receipts fail. Legacy
receipts without this original binding require separate authenticated original
evidence; this helper never backfills them. Historical receipts remain unchanged.
Local repair declarations and actual executed regression coverage retain their
separate validation requirements; source retention does not certify a local repair.

## Required shared regression cases

Use the current installed `scripts/case_inventory.py` through a named Python
`toolkitChecks` owner for shared engineering regressions. Keep native application
tests in their actual native owner; a C# wrapper calling Python is not an
application test merely because it appears in a native test report.

Commit a reviewed current contract containing `schemaVersion: 1`, `modules` and
`inputs`. Each module declares its literal current Python path, exact source
SHA-256, import name and complete fully qualified `module.Class.test_method` to
platform-list mapping. `inputs` lists the actual current mechanism/helpers tested.
Pass the original reviewed contract digest explicitly:

```sh
python .specify/extensions/program-kit-governance/scripts/case_inventory.py --contract tests/current-shared-cases.json --contract-sha256 <reviewed-contract-sha256>
```

The toolkit declaration uses that installed script and literal arguments, includes
the contract, current cases and mechanism files in its exact owned inputs, and
sets a bounded timeout. Select it with the existing Focused `Checks` argument.
Review a changed contract deliberately with its obligation mapping. Do not rebuild
the expected inventory from discovery during verification or refresh its digest
just to make missing cases pass. The caller's authenticated source/review supplies
the anchor; the manifest cannot authenticate its own publisher.

Missing, added, renamed, duplicate, skipped, expected-failure, failing and empty
required execution fails independently of unrelated passing counts. Every current
platform case must actually start once and pass. Explicit other-platform cases are
reported as not applicable and require their platform's qualification; they are
never recorded as passed. Source and declared inputs must remain unchanged through
execution. Each run retains source hashes, required/executed identities and bounded
logs in a new `artifacts/tests/toolkit-cases/` directory. This establishes scoped
regression execution, not semantic completeness or application acceptance.

When replacing old shared fixtures, retain a reviewed old-obligation-to-new-case
mapping. Preserve consumer-specific provider budgets, paid authority, domain,
deployment and original-history checks under their actual current owners. Generic
toolkit cases cannot replace those obligations, and archived code is never imported
to manufacture current coverage. Preserve original failed and historical results.

## Reconcile declared local tooling repairs

Use the trusted staged release's updater with both `--local-repairs
<consumer-relative-declaration.json>` and `--local-repairs-sha256
<original-reviewed-declaration-sha256>`. Review the concrete declaration and its
coverage rationale before selecting that digest. Preview reports that fresh
execution is still required; it supplies no tested-source admission.

The declaration has `schemaVersion: 1`, `contract`, `contractSha256` and a finite
`repairs` array. The contract uses the current exact-case format above. Each repair
names its exact installed machine-source `path`, `beforeSha256`, `afterSha256`,
nonempty fully qualified `requiredCases`, and reviewed `rationale`. An explicit
addition uses `beforeSha256: null`; deletion requires separate owner reconciliation.
Every changed path must be a declared current case input. Generated command/skill
customizations and manifests still pass their ordinary ownership checks.

The maintained updater compares each original against one complete authenticated
component baseline before executing current cases. Missing publisher helpers,
unregistered/spurious repair owners, wrong original/changed bytes, absent or skipped
required cases, and changed inputs fail. A C# method's existence or a supplied
passing JSON report cannot substitute for fresh execution. The reviewer remains
responsible for whether the selected cases test the repair's semantics.

Before component replacement, the original attempt retains the complete exact
managed/native input set, explicit absences, local patch, declaration, case contract
and selected case sources as bounded data under
`.program-kit/installation/attempt-inputs/sha256/`. The new attempt and migration
receipt bind this original inventory; `tooling_witness.py verify-inputs --receipt
<original-attempt-or-migration-receipt>` verifies it in a later process without
replaying archived source. This verifies original bytes, not migration completion.
The normal migration validator separately requires its canonical checks.

An interrupted repair reconciliation retains the original arguments and canonical
originals. Retry freshly executes the current cases against the actual remaining
installed sources, including components already replaced by authentic target bytes.
Original patch/evidence remains historical. Legacy partial mutations without the
complete original input binding cannot be backfilled from current mixed state.
Public publisher identity, local tested deviation, generated output, historical
receipt and current application acceptance remain distinct claims.
