# Azure parallel execution and delivery evidence

Phase 4 adds optional execution policy to an explicitly activated Azure delivery profile. Upgrade
through the existing reviewed profile migration, preserving prior policy/history. Installation and
default-disabled operation make no provider calls. Azure-hosted code and pipelines are the first
execution adapter; GitHub execution follows its adapter phase.

## Policy and review inputs

An authorized executor can explicitly pause or withdraw a claim while a human change awaits
review; coordinator takeover likewise stops at paused. If safe native publication is unavailable,
the claim action commits with an attributable deferred-board record and performs no native write.
The command result and ready-work report expose the reason. Reconcile and revalidate the plan
before board synchronization or renewed execution. An already-dispatched board operation must
first be resolved through its recorded recovery path. Stopping a claim never grants completion.

The optional `execution` object has `schemaVersion: 1`, `teams`, `pipelines` and `tagCategories`.
Each named team declares `repositories`, verified individual `executors` drawn from technical
roles, and a positive `workInProgressWarning` or null. This is an explicit roster, not automatic
directory synchronization. Accountable business ownership remains separate from execution assignment.
The discoverable JSON shapes are `executionPolicy` and `executionPlan` in `delivery.schema.json`;
semantic validators additionally check role membership, repository mappings and activity dependencies.

Each pipeline rule identifies `projectId`, integer `definitionId`, triggering `repositoryId`,
`finalYamlSha256`, repository alias-to-ID mappings in `repositoryAliases`, ID-to-branch mappings in
`targetBranches`, `requiredJobs`, `artifactName` and `manifestPath`. The resolved YAML digest uses
UTF-8 with LF line endings: Azure preview uses LF while its expanded-YAML log can use CRLF. No other
YAML text or artifact bytes are normalized. Record a reviewed preview digest before accepting runs;
do not silently learn a new trusted digest from an unexpected producer. Pipeline changes need policy
review. Tag categories map stable semantic names to concise tags inside the profile namespace.
Optional `ciReaders` contains the actual verified job identity IDs, separate from all human approval
roles. Optional `toolRepositories` maps a producer's tooling alias to immutable `repositoryId` and
`commit`. Pin the read-only checker in this trusted repository and verify the resolved producer YAML;
do not load its authority checks from unreviewed PR code. Tooling revisions are not delivery subjects.

Run all commands as `python .specify/extensions/program-kit-delivery/scripts/azure_execution_cli.py
--profile <pinned-profile> --repositories <locations.json> <command>`. Locations map registered
repository IDs to checkout roots. They do not change binding identity, accepted policy or authority.
Use separate working trees for concurrent sessions; each checkout has one local execution receipt.

Execution plan inputs contain `workId`, `repositoryId`, `teamId`, `executorId`, `targetBranch`,
`baseCommit`, `technicalArtifacts`, `footprint`, `checks`, `dependencies`, `schedule`, `priority`
and `milestones`. Technical artifacts use the Phase 3 repository/commit/path/SHA-256 contract.
Actual Git objects, ancestry and current file bytes are verified even for the first implementation
plan. New work cannot avoid artifact verification by having no prior technical-revision obligation.

The footprint contains bounded `writePaths`, `resources`, `categories` and `generatedSources`.
Resources have `id`, `mode` (`read`, `change`, `exclusive`) and `contractRevision`. Generated paths
map to their source paths, which participate in reassessment. Same categories or potentially
overlapping globs are advisory. Incompatible declared contract versions or exclusive resources block
the named conflict. This predicts coordination needs, not conflict-free merges or arbitrary semantic
compatibility. Actual tracked and untracked changes are checked against the declared scope; new
material scope needs review.

Checks have `id`, `kind` (`pipeline` or `manual`), `acceptanceIds`, `pipeline` (rule name or null) and
`description`. A dependency has `id`, adopted `predecessor`, `blockedActivity`, `condition`,
`checkIds`, `reason` and an HTTPS `externalReference` or null. Activities distinguish implementation,
integration, review, publication, delivery and acceptance. Conditions are `contract`, `integration`,
`delivery` and `acceptance`. A contract condition verifies the predecessor's accepted technical
artifacts. Integration names required receiving checks; upstream issue closure never supplies them.
Reject circular blocking or native dependency links and extract a shared prerequisite instead.

Schedules contain optional `plannedStart`, `targetFinish` and `committedDeadline` ISO dates. Planned
start is scheduling intent, not a prohibition on starting earlier. A forecast is distinct from a
business commitment. Actual start, pause/resume, implementation completion, delivery and acceptance
are separate operational events. Never infer dates from missing estimates. Priority is 1–4 for an
explicit override, or null to inherit. Milestones identify previously approved milestone records.

`plan --input <plan.json> --output <proposal.json>` prepares an exact review. Present it, then
`approve --input <proposal> --approved-sha256 <digest> --decision-source <actual-decision> --role
<business|technical>` for each role, and `apply --proposal-id <id>`. Human roles may be held by the
same verified person. No plan begins execution merely by being approved.

## Claims, checkpoints and visible coordination

`ready --output <report>` reports refinement/implementation eligibility, priorities, assignments,
claims, blockers and workload warnings. Explicit business ordering remains authoritative; unblocking
value and milestone risks explain recommendations, not silent reprioritization.

`claim --work <key> --session <unique-session-id>` conditionally commits against one shared head.
Competing clients cannot both receive the same current entitlement. After a conflict, recompute;
never retry an old admission decision against a new head. The local
`.program-kit/delivery/execution.json` identifies the provider claim, generation and session. A
missing or forged receipt cannot create authority. Use `resume` with the same identity after an
explicit pause. `pause`, `withdraw` and coordinator `takeover` require the expected generation and
a reason. A changed assigned executor needs a reviewed new plan. Claims do not expire automatically.

`checkpoint --repository-id <id> --activity <activity>` verifies the current claim, accepted business
basis, real technical artifacts, relevant dependencies and planned/observed scope. Implementation
records actual start; review marks waiting work visibly. Ordinary core implementation preflight uses
the same provider check. Additional local repository lookup paths may be supplied through
`.program-kit/delivery/repositories.local.json`; each referenced repository still needs its real
registration. Checkpoint validation never treats local configuration as shared authority.

During a provider outage, an already authorized session can finish its current local step and run
local tests within the last verified scope, then stop at the next governed checkpoint. No new claim,
scope expansion, PR publication or governed completion is permitted until refreshed. Preserve local
work when reconnection reveals a changed generation or plan. These are cooperating-session controls;
they do not prevent independent humans from editing code or administrators changing provider rules.

`publish-view --work <key>` creates a platform-hosted readable view and adds supported native
priority/date fields, concise tags and predecessor/successor links. The work item's hyperlink opens
the view in Azure without local repository files. It displays owner/executor, activity, blocker,
dates, milestones, accepted plan and evidence. Human descriptions/comments and unrelated tags are
preserved. Projection intent is recorded before the conditional native update. Use
`resume-projection --projection-id <id>` after uncertainty; unknown effects or intervening human
changes remain blocked instead of being replayed. Historical observations retain original role
review identity and record the narrowly explained projection separately.
After reviewing intervening history, `abandon-projection --projection-id <id> --reason <reason>`
can close an obsolete operation. A dispatched update requires a newer native revision so its old
conditional PATCH can no longer arrive successfully. An unchanged revision remains uncertain.

## Evidence and progression

### Native lifecycle and team boards

Use `board-plan --input <mapping> --output <proposal>`, obtain both business and technical
`board-approve --input ... --approved-sha256 ... --decision-source ... --role ...` decisions, then
`board-apply --proposal-id <id>`. The versioned `boardPolicy` schema and `azure-board-default.json`
define per-type defaults. Resolve the native team and Stories/Features/Epics board IDs into `boards`;
Tasks retain their native workflow and taskboard. Capability discovery verifies state categories and
existing column mappings. It does not rewrite columns, WIP limits or team-specific layouts.

The shared board policy is an approved operational record bound to the delivery profile digest,
similar to execution/milestone plans. Presentation onboarding does not replace technical approvals,
bindings or immutable pipeline inputs. A later delivery-profile migration requires a new board
mapping review. No existing profile silently enables native state writes.

For default Agile Requirements, actual implementation start maps to Active, integrated
implementation maps to Resolved, and verified delivery plus business acceptance maps to Closed.
A claim alone leaves work New. Tasks have no Resolved state and remain Active until their own
required verification and acceptance complete. Pause, review and waiting conditions use owned tags
without resetting lifecycle. Human tags are preserved. Parents can become Active from descendant
activity; they need their own explicit outcome decision to close. `parent-outcome-plan --work <key>
--input <observation> --output <proposal>` requires all scoped descendant Requirements' current
acceptance and an explanation with actual Git artifacts. Business/acceptance authority applies the
exact decision through `parent-outcome-accept`. Native child states never supply that proof.

Every governed transition atomically records its native publication intent with the decision.
Conditional native updates then run from a durable outbox. A write failure reports synchronization
pending and fences further affected progression, rather than claiming the board is current.
`board-resume --operation-id <id>` observes a dispatched update before recording its result and does
not replay uncertain PATCHes. Unrelated human edits or comments cannot be absorbed as workflow
side effects. Reconcile them, then use `board-abandon` only when newer reviewed revisions fence all
remaining conditional updates. `board-sync --work <key>` projects previously verified progression
and its ancestor activity under the same rules. There is no background synchronizer: manual board
edits are detected at the next explicit sync/checkpoint and do not grant evidence or acceptance.

Azure can lazily initialize previously absent board fields when a board is inspected. This is an
observable history change. `board-observe-initialization --work <key>` recognizes only a single
initialization revision from Azure's workflow service, unchanged lifecycle, exact configured board
fields with previously absent values, and unchanged human fields/comments. It preserves both raw
snapshots and the prior business review identity. Every other change still requires reconciliation;
this command performs no native write. Ordinary state publication separately checks the exact
actor, single conditional revision and known workflow-generated audit/column effects.

Workflow references: [state categories](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/workflow-and-state-categories?view=azure-devops),
[native board fields and columns](https://learn.microsoft.com/en-us/rest/api/azure/devops/work/boards/get?view=azure-devops-rest-7.1).

Ordinary pipeline jobs only build, test and publish evidence. They do not acquire human approval
roles or write the coordinator. An authorized developer/verifier reads native run, source, job and
artifact data before recording technical progression. Required native branch policies must actually
be configured and verified before claiming merge enforcement. This adapter does not provision a
general deployment system or treat deployment-resource locks as development claims.
Use `azure_execution_ci.py --profile <profile> --repository <checkout> --organization <organization>
--project <project-id> --coordinator <repository-id> --space <space-id>` from the pinned checker.
The definition fixes these identities and maps `SYSTEM_ACCESSTOKEN`; `BUILD_BUILDID` is verified
against the provider and checked-out commit. The checker reads current history, claims, scope,
dependencies and blocking build policies, and records no progression. Give the project-scoped job
identity coordinator read access and deny contribution, force push, policy editing and permission
management at the repository. Verify effective permissions using the actual job identity.
For migrating consumers, use `--binding <checkout>/.program-kit/delivery/binding.json` instead of
`--profile`: the checker resolves the binding's current immutable profile snapshot, verifies its
bytes and compares the binding with the current provider registration. This avoids fixing CI to an
obsolete snapshot filename after a governed migration. Released parent implementations supply
historical integration proof; their active receiving Tasks remain independently coordinated claims.

The published ZIP contains a JSON manifest with `schemaVersion: 1`, exact repository-ID-to-commit
`sources`, named `checks` whose successful value is `passed`, and `artifacts` mapping every payload
path to its exact SHA-256. All non-manifest files must be covered. The verifier checks the configured
pipeline, actual consumed repository IDs/versions, required successful jobs, reviewed resolved YAML,
current target revisions and downloaded content. Artifact downloads are bounded, follow only the
supported Azure artifact origins, and never send credentials to blob storage redirects. Missing,
expired, skipped, partially successful or mismatched evidence cannot pass. No signed download URL
or credential is copied into the evidence record.

`evidence-plan --work <key> --input <request> --output <proposal>` accepts `checkIds`, `buildId`,
`manualArtifacts` and `explanation`. Pipeline requests identify one exact build and no manual
artifacts. Manual requests identify actual Git artifacts in the receiving repository and explain
the human observation; they cannot satisfy a pipeline check. Manual observations also bind the
current integrated source, so later code changes invalidate reuse. Present and record the reviewed
proposal with `evidence-record --input ... --approved-sha256 ... --decision-source ...`.

Use `progress-plan --work <key> --stage <implementation|delivery|acceptance> --output <proposal>`,
then `complete` with the exact digest and attributable decision. Implementation requires committed
work, a final checkpoint and proof that its source was integrated into the agreed target; it releases
the implementation claim. Delivery needs the current required evidence. Business acceptance needs
the acceptance role and current verified delivery. PR-candidate evidence is distinct from integrated
delivery evidence. This initial completion path verifies Git ancestry; squash/rebase integration
needs an explicit source-to-result proof rather than pretending the original commit is an ancestor.

Milestone inputs contain `id`, `title`, `outcome`, `ownerId`, Requirement `workIds` and `schedule`.
Use `milestone-plan` and `milestone-apply` with business approval. Shared membership and scheduling
are platform records. Closed children do not establish a milestone or Epic's business outcome.
`milestone-status --milestone <id> --output <report>` recomputes each member's current progression.
The accountable owner with acceptance authority uses `milestone-acceptance-plan --milestone <id>
--input <observation> --output <proposal>` and `milestone-accept` with an exact digest and decision
source. The observation contains `explanation` and actual Git `artifacts`. Every member must have
current delivery evidence; the recorded outcome decision remains separate from child acceptance.
Changed milestone membership, delivery evidence or observation artifacts invalidate its current status.
`milestone-publish --milestone <id>` publishes the current outcome, dates, linked Requirements and
verified progress in a readable coordinator view. Publication never grants acceptance.

Provider contracts: [Azure Git ancestry](https://learn.microsoft.com/en-us/rest/api/azure/devops/git/diffs/get?view=azure-devops-rest-7.1),
[job access scopes](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/access-tokens?view=azure-devops),
and [revision-conditional pipeline updates](https://learn.microsoft.com/en-us/rest/api/azure/devops/build/definitions/update?view=azure-devops-rest-7.1).
