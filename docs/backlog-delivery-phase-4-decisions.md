# Phase 4: Azure parallel delivery and evidence

Status: interview complete. The user accepted all four rounds (Q1–Q14), confirmed the complete
Phase 4 plan and authorized implementation. Phase 3 is complete at
`a2e8e216d1a75e39e52387b9ebad56be072106b7`.
Continue on `codex/backlog-delivery`; commit and push after the completed phase's validation.

## Settled earlier decisions

Keep cloud delivery authority separate from code hosting and Git technical authority. Claims use
the shared coordinator and distinguish accountable people from execution sessions. Claims do not
expire into reassignment; explicit takeover creates a new generation, checked at governed
checkpoints. Simple execution can claim a Requirement; meaningful independently executable child
Tasks permit parallel work and exclude a simultaneous parent-wide claim. Broad path/tag overlap
is advisory; confirmed incompatible contracts or exclusive resources need scoped coordination.
Native closure does not substitute for implementation, delivery or business-acceptance evidence.
No background coordination service or automatic commitment changes are introduced.

## Accepted round 1

1. **Readiness:** expose ready-to-refine and ready-to-implement separately. Implementation needs
   accepted business inputs, verified current Git planning artifacts, resolved technical revisions
   and satisfied conditions for the specific activity. A blocked integration step need not block
   independently scoped implementation with a sufficiently defined contract.
2. **Ordering:** respect explicit business priority and backlog order. Lower-level work inherits
   its parent's priority unless an authorized owner explicitly overrides it. Explain milestone
   risk, unblocking value and compatibility with active work alongside recommendations. Propose
   priority changes instead of silently changing business order. Assigned work requires a recorded
   handoff before another person takes it.
3. **Concurrent sessions:** allow multiple execution sessions per person, each with distinct
   identity and claims. Exclusive claims apply to actual work/resources. Expose aggregate active
   workload and optional team warning thresholds; no universal one-person/one-item restriction.
4. **Dates:** planned start is optional scheduling intent, not an automatic prohibition on starting
   earlier. Actual start records explicit implementation beginning, not assignment or a claim;
   retain pause/resume history. Target finish is an optional attributable forecast. A committed
   deadline is a separately approved business commitment and must not move silently. Preserve
   distinct actual implementation completion, verified delivery and acceptance events. Milestones
   can begin with outcomes and participating Requirements without dates; never invent dates from
   missing estimates.

## Accepted round 2

5. **Dependency conditions:** each edge names the blocked activity, releasing condition and
   required evidence. Start with approved contract, passing receiving integration test, verified
   delivery and explicit business acceptance. A reviewed contract may permit implementation with
   a test double while actual integration remains gated. Reject circular blocking conditions and
   propose a shared prerequisite where appropriate.
6. **Scope uncertainty and conflicts:** require a bounded current footprint before a new
   implementation claim. Uncertain compatibility with active work means parallel safety is
   unresolved and requires assessment before the potentially conflicting activity. A confirmed
   conflict needs an attributable technical resolution: narrow scope, establish compatibility,
   extract shared work or sequence the activity. Generic warning dismissal cannot erase it.
   Refinement/exploration can continue without implying implementation clearance.
7. **Claim completion:** retain the implementation claim through review and integration into the
   agreed target branch. Show awaiting-review work separately from active implementation without
   hiding unfinished work. Release when that implementation activity completes; integration and
   acceptance obligations remain open, with meaningful separate Tasks where needed. Explicit
   pause, handoff and takeover remain available. An open PR or released claim is not delivery.
8. **Outage boundary:** an already authorized session may finish its current local implementation
   step and run local tests within its last verified scope, stopping at the next governed
   checkpoint. No new claims, scope expansion, PR publication or governed completion during the
   outage. Reconnection rechecks generation, human changes, dependencies and overlap. Preserve
   local work and resolve changed authority or technical direction explicitly.

## Accepted round 3

9. **Delivery evidence:** define required checks against named acceptance criteria during planning.
   Verify configured pipeline identity, successful run, tested source and contract revisions and
   actual artifact contents. Cross-repository integration identifies both sides' versions. Separate
   PR-candidate validation from verification of the integrated result. Missing, expired, failed or
   mismatched evidence cannot pass. Attributable manual evidence is allowed for criteria explicitly
   requiring human observation and cannot substitute for mandatory automated tests. Delivery means
   the agreed delivery boundary; production deployment is required only when included. Business
   acceptance remains separate.
10. **CI authority:** ordinary test/build jobs produce evidence without permission to approve
    business changes or rewrite shared coordination records. An independently authorized verifier
    or developer session reads provider evidence and records permitted technical progression.
    Business acceptance and architecture approval remain human decisions. Reuse existing pipelines,
    add required validation integration, and verify required branch checks before claiming merge
    enforcement. No general pipeline-management platform is introduced.
11. **Portal visibility:** teammates must be able to find owner, priority, activity, blocker,
    milestone and evidence without reconstructing repository files. Prefer supported native fields,
    predecessor/successor links and concise tags. Clearly owned summaries and evidence links expose
    claims and coordination findings where native fields cannot. Preserve human text and unrelated
    tags. Keep planned start, forecast finish and committed deadline distinct. Default setup does
    not require organization-wide custom process changes; richer mappings remain configurable.
12. **Execution eligibility:** configure explicit teams, participating repositories and eligible
    individual executors in the shared profile. Claims require both the appropriate role and
    repository/team eligibility. Accountable ownership is distinct from execution eligibility;
    people may join several teams and use multiple separately identified sessions. Start with
    explicit rosters; automatic directory/group synchronization and capacity planning are deferred.

## Provider facts informing these decisions

- Azure native predecessor/successor links express ordering; Program Kit evaluates the activity
  conditions. Delivery Plans' date-based dependency conflicts are distinct from technical readiness.
  [Link types](https://learn.microsoft.com/en-us/azure/devops/boards/queries/link-type-reference?view=azure-devops),
  [Delivery Plans](https://learn.microsoft.com/en-us/azure/devops/boards/plans/track-dependencies?view=azure-devops).
- Build records identify definition/revision, repository, source, status and result. Pipeline runs
  additionally describe consumed resources; multiple-repository verification needs all relevant
  versions, with response completeness to prove in native acceptance.
  [Build GET](https://learn.microsoft.com/en-us/rest/api/azure/devops/build/builds/get?view=azure-devops-rest-7.1),
  [Runs GET](https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/runs/get?view=azure-devops-rest-7.1).
- PR build source versions can identify a merge candidate rather than the source branch head.
  Artifact lookup identifies the producing build but supplies no universal SHA-256 receipt.
  [Variables](https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops),
  [Artifacts](https://learn.microsoft.com/en-us/rest/api/azure/devops/build/artifacts/get-artifact?view=azure-devops-rest-7.1).
- Job access tokens derive authority from configured scope and build-service permissions, separate
  from the initiating human. Required branch validation and its expiration policy need explicit
  configuration; deployment-resource checks are a separate mechanism, not development claims.
  [Job tokens](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/access-tokens?view=azure-devops),
  [Branch policies](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies?view=azure-devops).

## Accepted final round

13. Create a new private Agile project `Unfussiness/ProgramKit.Delivery.Phase4` with two synthetic
    code repositories and a dedicated coordinator. Configure minimal test pipelines and required
    branch checks only inside this isolated project. Exercise competing sessions, shared milestones,
    dependency/overlap gates, multi-repository integration evidence, stale evidence and interrupted
    handoffs. Permit up to 12 pipeline runs with 10-minute job timeouts using existing capacity;
    no capacity purchases, production deployments, organization-wide process changes or coding-agent
    sessions. Preserve resources and evidence. If real CI cannot execute, finish independent work
    and report the specific unresolved acceptance condition rather than substituting fake CI proof.
14. When independent tests are ready, the user personally marks one synthetic claimed Requirement
    complete prematurely and adds an ordinary human tag. Verify that native closure supplies no
    missing delivery evidence and does not release the execution claim or grant business acceptance;
    reconcile the change and preserve the unrelated human tag. Provide the exact item/action when
    ready. Keep the Customer Service Pilot (Epic 82 and children) outside this Phase 4 test scope.

Read-only scope check: the proposed project name returned `ProjectDoesNotExistWithNameException`.
The organization exposes non-legacy hosted Azure Pipelines pool 9; existing Phase 2 has queue 128
for it. This proves an accessible route, not hosted-minute entitlement, execution availability or
permissions for a new project's queues. No pipeline was queued or resource changed by this check.

## Accepted board-state completion amendment

The user approved closing the native board-state gap before Phase 4 completion. Governed start,
implementation, delivery and acceptance must project a truthful native lifecycle. Default Agile
Requirements map to New before start, Active during implementation, Resolved after integrated
implementation while verification/acceptance remains, and Closed only after verified delivery and
business acceptance. Discover and validate mappings per work-item type, including Tasks and custom
processes; validate the team's existing board column mappings without replacing its layout.

Native updates belong to the governed operation, with conditional revisions, durable recovery and
explicit synchronization failures. Human edits require reconciliation and cannot grant missing
evidence or be silently overwritten. Blocked/paused/review activity stays separate from lifecycle.
Parent start may reflect descendant activity, but parent closure requires its own explicit outcome
decision and current evidence rather than a child-count roll-up. Before the human portal exercise,
Requirement 100 must appear Active for its already-started unfinished implementation. Extend tests
to cover native progression, recovery and false human completion.
