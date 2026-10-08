# Consumer upgrade and migration planning method

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
