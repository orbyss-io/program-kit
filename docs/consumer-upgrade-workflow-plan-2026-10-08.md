# Consumer upgrade workflow implementation plan

Approved by the user on 2026-10-08 after a design interview. The approved scope is implementation of this capability in Program Kit; consumer rollout and publication retain their separate authority. The companion [fresh session prompt](consumer-upgrade-workflow-implementation-prompt-2026-10-08.md) carries this plan into a new implementation session.

Program Kit consumers need to upgrade their toolkit and guidance while preserving valid architecture choices, implemented behavior and unfinished specifications. Implement a resumable upgrade workflow with a conversational command or skill as its entry point. It must explain applicable changes, reconcile affected inputs, record bounded planned migrations and establish what work can safely proceed.

## Outcome and scope

A consumer selects an exact target release and deliberately upgrades. New releases do not automatically invalidate ongoing work. An upgrade establishes current guidance for future specifications, identifies relevant conflicts with retained designs, and makes the conditions for continuing work explicit.

A safe checkpoint depends on coherent installation, reconciled inputs and readiness for the next work. Reaching specify, plan or tasks alone does not establish that checkpoint. For a consumer already at tasks, retain unchanged requirements, reconsider affected design and tasks, and resume from the earliest affected phase. A full specification restart remains available when warranted or deliberately chosen.

Implement this in Program Kit using the existing release-owned updater, installation guards, dependency transitions, architecture review and Spec Kit hooks. Use disposable consumers for qualification. This plan does not authorize changes to real consumer repositories, machine-wide tooling, public publication, paid live acceptance or messages to maintenance chats.

## Approved decisions

### Version comparison and consumer choices

Compare three sources: the earlier Program Kit guidance, the chosen target guidance, and actual consumer adoption and customization. Use cumulative release history, exact selected dependencies, architecture decisions, contracts and current code. A changed default offers adoption; it does not automatically require migration.

Publish structured, reviewed descriptions of substantive consumer-facing changes alongside existing release guidance. Each needs a stable identity, source and target applicability, affected capability or constraint, supported retained states, available remedies, verification, and dependencies or supersession where relevant. Explain semantic changes; file differences alone cannot establish mandatory migration. Reconcile intermediate guidance with target semantics so retired requirements do not become new gates.

Assess the whole consumer for relevant impacts, including implemented domains, shared infrastructure and unfinished specs. Change only affected areas. Inspect actual code and contracts where declared metadata cannot establish applicability or semantic correctness.

The interview groups related changes and asks only consequential adoption, architecture, dependency or behavior choices. Carry forward supported decisions and unchanged product confirmation. Offer only valid alternatives. Explain unsupported retention and its remedies. Mechanical changes, regenerated context and ordinary test execution do not require repeated human confirmation.

Program Kit installation preserves accepted and scaffold-captured dependency profiles by default. Adopting another profile uses the existing reviewed dependency transition. Optional adoption, supported retention, required correction, deferred work and unresolved assessment must remain distinguishable.

### Architecture and phase readiness

Reassess applicable bootstrap concerns under the target version and refresh affected guidance and architecture through existing substantive review paths. Preserve original bootstrap history, accepted evidence and ratified authority. An upgrade does not mean rerunning founding bootstrap, fabricating approval, or replacing valid consumer decisions.

New guidance governs future work. Existing code may retain older designs where compatibility and applicable constraints permit. New features extending those areas must respect their actual contracts and retained decisions. Relevant exceptions or retention choices belong in ordinary architecture documents.

Every finding has an affected scope and earliest necessary phase. A shared incompatibility may prevent upgrade completion; an ownership question may prevent sound specification; an implementation dependency may allow specification but prevent affected implementation. Delivery or production obligations retain their real due phases. Version age, missing historical paperwork and unrelated future work are insufficient reasons to block.

An upgrade can complete with deferred migrations when retained state is supported, consequential choices are resolved and the consumer knows what work can proceed. Complete migrations needed for the upgrade itself within the isolated attempt. Never mark an unresolved shared incompatibility as safely deferred.

### Planned migrations and execution

Keep one upgrade coordination record with decisions and bounded migration briefs. Group migration work by actual domains, shared contracts, infrastructure and dependency closure. Historical specs provide intent and regression traceability; they do not automatically partition migration work. A shared change affecting ten old specs should appear once with its affected consumers.

During upgrade, record planned migrations without generating every detailed implementation plan. Each brief identifies:

- Its stable identity and originating change or discovery.
- The reason and concrete evidence that it applies.
- Affected owners, mechanisms, projects, contracts and unfinished specs as known.
- The expected outcome and behavior or invariants to preserve.
- Trigger and earliest blocking phase, with relevant prerequisites and dependencies.
- The applicable maintained migration method or recipe.
- Known uncertainties, recovery limits and responsibility or next action.

Investigate enough during upgrade to establish applicability, credible retained compatibility and the blocking phase. Deep implementation analysis waits until pickup unless it is necessary to establish whether the upgrade itself is usable. Predictable future adoption cases can remain conditional entries until concrete scope exists.

Taking up a migration starts focused analysis against current code and dependencies. Reuse its brief and normal requirements; resolve uncertainties and create detailed plans, tasks and meaningful tests using the existing development process. Resolve consequential consumer choices through their normal review. Then implement, verify and update the migration's status. Planning is not execution evidence.

Program Kit supplies a maintained planning method and reusable versioned recipes. Describe applicability, preserved behavior, allowed scope, transition ordering, verification and recovery limits. Agents instantiate those contracts against actual consumers. Where no recipe fits, use a bounded consumer-specific proposal and existing substantive review. Automated plan checks establish completeness and structure; tests and semantic review establish the actual outcome.

Changed source inputs reopen only affected analysis or work. Do not continue stale instructions silently, alter unrelated designs, or infer authorization for external changes. Deployment, destructive data operations and other external rollout require their own planned authority and recovery; workspace restoration does not undo external state.

### Feature compatibility scan

Extend ordinary before-specification architecture review and intake with a lightweight scope compatibility scan. Refine it during planning when new ownership, contracts or dependencies become concrete. Reuse existing scope readers by accepting a request or intake brief before a feature directory exists; do not manufacture a feature to run a check.

The scan identifies relevant owners, touched contracts, retained designs and matching planned migrations, then checks changes since the upgrade assessment. Older guidance alone is not evidence of incompatibility. Missing scope or provenance must be described honestly and investigated proportionally.

Output a short explanation of what can proceed and any relevant migration or unresolved question. Carry dependencies into existing plan/tasks. Keep scans regenerable and avoid per-feature approval packets, phase dossiers and bootstrap receipt requirements for ordinary work.

A new discovery is classified using evidence as a previously detectable omission, activation of a known condition, changed inputs, new scope, or unresolved cause. A detectable omission is an upgrade-assessment defect and should supply a Program Kit regression case. A later requirement or integration may legitimately create new migration needs.

Create an actionable migration entry immediately when one is discovered. Use the same planning and recovery route; keep unaffected work available. Await upstream maintenance only when a supported correction cannot be established locally. Preserve earlier findings and append the discovery rather than rewriting history to imply it was anticipated.

### Isolation and activation

Prepare an upgrade branch in a separate worktree from a known consumer commit and installation state. Preserve the original checkout and user changes. Consumers may continue development on the original version; before merge, reassess intervening changes, reopen affected findings and run relevant validation against the combined result.

Inventory Git-tracked content, owned installed assets, user customization, registries and local authority separately. A new Git worktree may lack ignored installation state. Preserve and reproduce the actual baseline through an explicit supported procedure before applying the target updater. Do not blindly copy caches or treat relocated proof/toolchain records as current.

Validate effective tool destinations, ownership and paths before mutation. In particular, inherited `SPECIFY_INIT_DIR` can make installed Specify resolve a different project from the command's working directory. The adapter must establish that the effective project is the intended isolated target. Handle any scoped environment adjustment deliberately; do not reuse live-worker environment sanitization or bypass a sandbox.

Keep preparation within isolated repository state and disposable test resources. Preserve interruption and failure evidence. Abandoning an attempt should leave the original consumer setup usable. Preserve needed diagnostics before any cleanup and never delete unowned paths.

Merge reviewed source changes and reproduce or reconcile the verified toolkit installation in the destination checkout. Git merge alone cannot carry all ignored assets, generated integrations, registries or local runtime state. Validate installation and affected dependency/phase readiness there before declaring activation complete. Recover the original setup if activation fails. Test this recovery; do not claim that the forward-only updater already implements downgrade or promotion.

### Validation and evidence

Record relevant baseline conditions before mutation. Verify installation coherence, retained or deliberately transitioned dependencies, affected design and behavior, and actual destination activation. Distinguish pre-existing failures from introduced failures. An unrelated baseline failure should not automatically prevent upgrade, but a failure that prevents required affected verification leaves that outcome unresolved.

Readiness is scoped. A successful installer, graph check, planning command or evidence export does not establish application correctness, semantic approval or delivery acceptance. Existing consumer validation gates retain their actual meaning.

Provide a local, reviewable maintenance evidence export for missed or newly required migrations. Include relevant source/target versions and profiles, change and migration identities, affected scope/phase, expected and observed behavior, reproduction or check results, uncertainty, and recovery outcome. Preserve original local evidence unchanged. Derive a minimal sanitized report with provenance and redaction/truncation metadata; do not export raw run archives, full environment, secrets, full architecture or source by default. Make the export useful after local completed-run retention ages out its original logs. Sending it is an explicit consumer action.

Consumers outside complete structured history use actual installation and layout assessment. Current packaged history starts at 0.12.5. Disclose missing coverage, use trustworthy historical guidance and investigate consequential gaps. Do not invent history, assert safety from missing evidence, or require a migration merely because a version is old.

## Workflow stages and persistence

| Stage | Work and durable outcome |
| --- | --- |
| Prepare | Exact target, source commit/installation inventory, preserved originals, isolated branch/worktree and baseline conditions. |
| Assess | Cumulative changes joined to actual adoption, affected scope, compatibility findings and uncertainties. |
| Decide | Grouped consequential choices, retained designs, optional adoption and reviewed substantive amendments. |
| Reconcile | Affected architecture/spec/plan/tasks updates, dependency transitions and bounded migration briefs. Required immediate migrations enter focused planning/execution here. |
| Validate | Required checks with honest baseline/introduced-failure classification and explicit remaining phase prerequisites. |
| Integrate | Reassess intervening changes and validate the combined candidate; merge reviewed changes under consumer authority. |
| Activate | Reproduce destination installation, verify required readiness, and retain recovery until activation succeeds. |

Keep one authoritative consumer upgrade record for decisions, briefs and resumable progress. Link existing architecture and normal migration plans/tasks instead of duplicating them. Generated summaries and scans are views. Low-level installation transactions and diagnostics retain their existing owners; the coordination record must not become an application build prerequisite.

Migration status must distinguish planned or conditional, active analysis/implementation, deferred, blocked, and completed without implying execution from a plan. Overall status must distinguish toolkit convergence, preparation/integration, activation and scoped future work. Choose a small coherent schema and expose clear next actions. Exact field names and file placement are implementation choices.

## Existing implementation foundations

Recheck current source before editing; these files were examined during the design interview and may have changed since then.

- [Release guidance](../extensions/program-kit-governance/scripts/release_guidance.py), [release history](../releases/history.json), [guidance build](../scripts/build_release_guidance.py) and migration guides: verified cumulative history and existing publication inputs.
- [Sequential updater](../scripts/upgrade_program_kit.py), [local bundle record](../scripts/record_local_bundle.py), [managed reconciliation](../extensions/program-kit-dotnet/scripts/reconciliation.py) and [managed migrations](../extensions/program-kit-dotnet/templates/dotnet/migrations.json): installation, ownership, transaction and recovery seams.
- [Dependency transitions](../extensions/program-kit-building-blocks/scripts/dependency_profiles.py), [building blocks](../extensions/program-kit-building-blocks/scripts/building_blocks.py) and profile catalogs: exact selected dependencies, qualification scope and existing reviewed transition authority.
- [Governance hooks](../extensions/program-kit-governance/extension.yml), [architecture check](../extensions/program-kit-governance/commands/speckit.program-kit-governance.architecture-check.md), [intake](../extensions/program-kit-governance/scripts/specification_intake.py), [feature knowledge](../extensions/program-kit-governance/scripts/feature_knowledge.py), [feature context](../extensions/program-kit-governance/scripts/feature_context.py) and [phase obligations](../extensions/program-kit-governance/scripts/phase_obligations.py): scope projection and normal phase integration.
- [Task draft](../extensions/program-kit-governance/scripts/task_draft.py), [phase context](../extensions/program-kit-governance/commands/speckit.program-kit-governance.phase-context.md) and [implementation check](../extensions/program-kit-governance/commands/speckit.program-kit-governance.implementation-check.md): selective repair, saved work and ordinary engineering boundaries.
- [Current upgrade remediation](../extensions/program-kit-governance/scripts/upgrade_remediation.py): presently supplies no feature migration verification and does not establish application readiness. Extend the semantics explicitly.
- [Diagnostic sanitization](../extensions/program-kit-governance/scripts/compatibility_diagnostics.py) and [execution history](../extensions/program-kit-governance/scripts/execution_history.py): bounded local evidence and retention. Current updater step logs are raw; a shareable export is new work.
- [Consumer engineering](consumer-engineering.md), [workflow resumption](../extensions/program-kit-governance/references/workflow-resumption.md) and [specification intake contract](../extensions/program-kit-governance/references/specification-intake.md): preserve low ceremony and existing authority. Historical recovery prose must be reconciled with current commands rather than promoted into routine gates.

The reviewed patterns include [Nx migration generation and execution](https://nx.dev/docs/features/automate-updating-dependencies), [OpenRewrite recipe composition](https://docs.openrewrite.org/concepts-and-explanations/recipes) and [recipe testing](https://docs.openrewrite.org/authoring-recipes/recipe-testing). Use these as design precedents, not new runtime dependencies. [Git worktree documentation](https://git-scm.com/docs/git-worktree) and [EF Core migration guidance](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying) establish why workspace isolation and external rollback need distinct treatment.

## Implementation sequence

1. Establish the clean implementation base, read current contributor instructions, map contracts and define fixture consumers and baseline assertions. Preserve concurrent changes.
2. Extend verified cumulative change metadata and implement consumer inventory, applicability and scoped impact assessment. Keep semantic uncertainty explicit and change adoption optional where supported.
3. Implement the minimal coordination record, bounded migration brief contract, maintained planning method and reusable recipe contract. Integrate existing dependency transitions.
4. Implement isolated preparation, resume/abandon and destination activation/recovery around the existing updater. Prove effective project targeting and local-state portability before integrating authoring stages.
5. Add the conversational workflow entry and affected architecture/spec/plan/tasks reconciliation. Preserve existing human-owned outer bootstrap launch rules; ordinary upgrades must not restart founding bootstrap or dispatch paid workers.
6. Integrate lightweight pre-specification scanning and planning refinements. Add migration pickup, local recovery from discoveries, and minimal evidence export.
7. Qualify installed and packaged behavior in disposable consumers, update consumer/release documentation, and run targeted checks plus the bounded Development suite. Deliver a reviewable implementation with explicit limitations.

Use current source and tests to choose exact command names, schema paths and workflow packaging. Update release guidance/validation so future changes and recipes are maintained together. Add new external dependencies to maintenance-policy.json only if justified; prefer existing tools. Avoid introducing redundant lifecycle authority.

## Acceptance scenarios

The implementation must demonstrate these behaviors with meaningful deterministic or installed-consumer checks:

1. A change affecting only toolkit instructions carries forward supported consumer decisions and unchanged intake; no bootstrap restart or fabricated approval occurs.
2. A newer default remains optional for an existing accepted profile; explicit adoption uses the existing exact reviewed transition and affected checks.
3. A skip across multiple versions applies cumulative changes without resurrecting superseded requirements or repeating the same choice.
4. Actual consumer customization and unsupported retention produce concrete scoped findings instead of silent overwrite or a false safe verdict.
5. Whole-consumer assessment identifies shared dependencies and groups one shared migration across affected domains/specs, with correct blocking phases.
6. A first feature at tasks retains valid requirements and completed task identity; only affected inputs are repaired and normal consistency/preflight checks run.
7. Known and conditional migration briefs are concise; detailed plans appear at pickup. Changed code reopens affected analysis and completion requires actual verification.
8. An upgrade with a credible deferred implementation migration can allow specification; a shared incompatibility required for activation prevents false completion.
9. A normal new feature finds a matching planned migration before dependent work. Additional scope during planning is reassessed without duplicate dossiers or renewed unchanged product confirmation.
10. Missing or misleading ownership metadata yields honest limited findings; a version difference, regex match or graph pass is not semantic compatibility proof.
11. A newly missed migration gets a local recovery entry and next action without globally blocking unaffected work or waiting unnecessarily for maintenance.
12. Evidence export preserves raw local originals, sanitizes sensitive material, records provenance and remains useful after log retention. It sends nothing automatically.
13. Isolated preparation reproduces owned ignored installation state, protects custom files and leaves the original setup usable on failure or abandonment.
14. Effective Specify targeting rejects or safely handles an inherited project-root override; sibling/source consumers are untouched.
15. Interruption, changed destination inputs, conflicting consumer edits and failed activation preserve evidence and recover safely. Git merge is not treated as complete installation promotion.
16. Intervening development is assessed against the combined result before integration; stale successes are not relabeled current.
17. Existing unrelated baseline failures are identified; introduced failures and inability to perform required affected verification remain unresolved.
18. Legacy/incomplete history uses actual inspection, names limitations and neither guesses semantic history nor blocks solely on age.
19. The standalone consumer engineering model survives: new coordination metadata and scan output are not application build/runtime prerequisites.
20. Packaged installation exposes the maintained workflow, planning method, scan and export through the actual supported integration and preserves historical evidence and consumer locks.

Tests must verify invariants, observable behavior and failure recovery, rather than merely mirror new implementation functions. Keep native proof execution, structural validation, semantic review, consumer behavior and human acceptance separate in results.

## Validation and publication boundaries

Follow AGENTS.md throughout. Use relevant targeted validators and the bounded Development suite:

```powershell
./scripts/Test-ProgramKit.ps1 -Suite Development -BrowserEngines 'chromium,webkit'
```

Firefox cannot launch on this Windows host. Preserve the CI Firefox matrix and report the known host limitation. Do not repeatedly retry Firefox or change production code for that host error.

Do not run the complete Release suite during the edit loop. Release candidate selection requires the dependency review workflow under docs/maintenance/dependency-review.md. Publication preparation, complete local Release validation, exact tag approval and publication remain separate user decisions. On this host the complete Release suite normally belongs in the user's own terminal. This implementation request does not authorize Release, paid live acceptance, interactive intake launch, consumer rollout or publication.

Record relevant checks, installed-consumer results, remaining limitations and recovery behavior in an implementation journal. Finish with a scoped diff, validation results and concrete next actions. Do not claim the overall plan complete while required implementation or recovery scenarios remain unresolved.
