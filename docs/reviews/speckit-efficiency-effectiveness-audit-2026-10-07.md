# Spec Kit efficiency and effectiveness review

Date: 7 October 2026. Branch: `codex/human-infrastructure-handoff`.

**The branch materially improves the mechanisms that protect code quality. Its main remaining weakness is deciding how much knowledge and verification to apply at each moment.** Keep the architecture, behavioral, security and contract guarantees. Make their execution depend on changed inputs, affected responsibilities and delivery boundaries.

The concern about excessive testing is justified. The current instructions say to run targeted tests, but they do not define a consistent test-selection policy or a distinction between an implementation checkpoint and feature acceptance. Completion verification can invoke a broad build/test/package pipeline. An agent following these instructions conservatively can repeat expensive work while a feature is still being developed.

My recommendation is to make the focused testing policy, scoped engineering commands and phase context corrections before starting the Notes workflow exercise. Do not wait for proof that the workflow is perfectly efficient: that requires observing an actual exercise. Establish the deterministic safeguards first, then use Notes to measure the remaining uncertainty.

## Scope and strength of the conclusions

The implementation sources were inspected at `886299efe5bce40c1a00b2a002908d637299633e`, initially equal to the local tracking ref for the requested branch. During this review, concurrent work advanced HEAD to `820adcad78ad8a71db5c2c6df5fe9fa064bd8799`. The complete intervening diff changed only the Foundation execution journal; the analyzed product sources were unchanged.

The review covers extension manifests, command instructions, governance presets, knowledge projection, architecture enforcement, generated engineering scripts, relevant negative tests, the Notes scenario, and the installed Spec Kit 1.1.1 implementation command. Selected existing De Zaaglijst verification scripts, hook configuration and task notes were inspected read-only to check how the instructions can play out in a real consumer. That consumer is an illustrative working snapshot with an older installed hook list, not an exact installation of every current branch change.

Structural improvement is supported by source and reproduced validators. Semantic code quality still depends on actual consumer behavior and source review. No complete Spec Kit flow was executed, so this review does not claim a measured end-to-end speedup, comprehensive SOLID compliance, or a quantified cause of all observed implementation latency. Notes was not started. No consumer source or product implementation was changed.

## What has improved and should be retained

| Area | Current improvement | What establishes confidence |
| --- | --- | --- |
| Physical architecture | Core, API, runtime implementation and persistence use distinct compilation responsibilities; one deployment does not waive them. | Planned roles and edges are checked before builds; evaluated MSBuild and compiled assemblies check the resulting graph. |
| Capability ownership | Bindings require a Core capability and an implementation in a distinct permitted project. Omitted active bindings are rejected. | Negative cases cover omitted bindings, relabeled roles, mixed projects, forbidden dependencies and invented registration names. |
| Relevant programming knowledge | Guidance reaches planning, tasks and implementation, rather than arriving only during final review. | One registry supplies summaries and focused section pointers. This is a sound foundation even though selection needs refinement. |
| Runtime correctness | Cancellation, fault observation, concurrency, disposal, DI scopes, provider confinement and immutable contracts receive explicit treatment. | Native analyzers cover selected properties; actual runtime/provider tests and review remain necessary. |
| Foundation reuse | Guidance now calls for public typed identity, JSON and Problem Details mechanisms when the selected qualified version provides them. | Exact package/Host qualification and independent application tests avoid treating package presence as proof of correct integration. |
| Behavioral testing | The constitution requires tests before changed behavior and preserves application-specific acceptance scenarios. | Tests are tied to user stories; scoped exceptions require a concrete alternative. Publisher internals need not be duplicated. |
| Reduced ceremony | Ordinary coding does not require phase dossiers, historical bootstrap receipts, renewed ratification or proof attestations. | The normal-development validator demonstrates ordinary phases without additional maintained artifacts or approvals. |
| Resumption | Task drafting persists incrementally, preserves IDs and checked tasks, and schedules analysis after the completed draft. | The explicit resume instructions prevent restarting broad preparation after every interruption. |
| Independent engineering | Build, test, contracts and packaging remain runnable without an agent or governance history. | Retained `eng/` scripts own application checks. This separation should also own test selection. |

The [earlier coding standards audit](C:/Users/tech_/Code/program-kit/docs/reviews/consumer-coding-standards-audit-2026-10-06.md) identified real blind spots, including mixed-role assemblies and omitted bindings. The current [architecture recipe](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_architecture.py:32) and [negative tests](C:/Users/tech_/Code/program-kit/tests/validate_architecture_recipe.py:84) address several of them. It would be inaccurate to judge this branch solely by the earlier audit's description of the old verifier.

The remaining qualification is important: metadata can establish dependency shape, but it cannot establish correct registration behavior, lifetime ownership, a cohesive responsibility or a production caller for a policy. The current recipe explicitly acknowledges this. Keep real activation/resolution tests and source review; do not replace them with more declarations.

## Findings in priority order

### Completion verification has no feature scope

**High priority.** [`phase_obligations.py execute`](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/scripts/phase_obligations.py:120) receives a feature directory but invokes `eng/Invoke-RepositoryVerification.ps1` without passing that directory, changed paths, test projects or an acceptance level. The [generated wrapper](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/templates/dotnet/files/eng/Invoke-RepositoryVerification.ps1:1) accepts only `CI` or `Release`; its own branches do not vary verification breadth by that mode.

When a consumer supplies `eng/verify.ps1`, the wrapper delegates to it and then runs compiled architecture verification. Otherwise, it invokes [Build.ps1](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/templates/dotnet/files/eng/Build.ps1:137), which performs solution restore, solution build, solution tests, and solution pack. `-SkipReleaseBundle` still permits staging when OpenAPI is enabled. Registered OpenAPI production and comparison also run.

That is a reasonable acceptance fallback. It is a poor default for an inner development loop. The scope information exists at the hook boundary but is lost before engineering execution.

**Recommended change:** give ordinary engineering verification explicit focused, affected and acceptance paths. Preserve a comprehensive acceptance default for humans and CI, and keep existing callers compatible. Add an explicit scoped path for development; a scoped success must never be reported as complete acceptance. Keep package/build/contract consistency checks when a test actually consumes those artifacts.

### Checkpoints do not have a clear testing contract

**High priority.** The installed Spec Kit 1.1.1 implementation command says to verify each phase before proceeding. It also reads optional feature documents when present and reports task progress. Program Kit's [task template](C:/Users/tech_/Code/program-kit/presets/program-kit-governance-preset/templates/tasks-governance.md:17) adds relevant tests during coding and ordinary engineering verification before completion, but does not define how those instructions interact with partial stops, resumes or small task batches.

There is no branch instruction explicitly requiring all tests after each task. The problem is ambiguity: a cautious agent can interpret a phase checkpoint, a resumed implement command or a request for progress as another completion boundary.

The inspected [consumer verifier](C:/Users/tech_/Code/dezaaglijst/eng/Invoke-RepositoryVerification.ps1:1) defaults to `Scope=Full` and `Stage=All`. Its preparation installs npm dependencies, builds assets, restores/builds the solution and helper projects, verifies formatting, runs engineering tests, and packs/stages the application. Its native runner selects every architecture-declared test project. `Source/All` still includes native and browser work before returning. Stage controls split broad pipelines; they do not select the tests affected by one operation.

The consumer's [task notes](C:/Users/tech_/Code/dezaaglijst/specs/002-wall-cut-list/tasks.md:627) record a full browser regression and another broad architecture/engineering hook while feature acceptance remains open. This supports a credible explanation for excess work. It does not establish the exact invocation count, elapsed cost, or whether every invocation was unnecessary.

**Recommended change:** state that saving progress, completing a task batch, resuming and reporting status are not full acceptance events. At such checkpoints, run tests for changes since the last relevant check and expand only for an identified dependency or risk. Full acceptance belongs at completed feature/domain delivery or a formal review handoff. A story boundary normally earns that story's regression set, not every repository test.

### Architecture guidance and planned checks are repeated

**Medium priority.** The current [manifest](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/extension.yml:110) registers 12 mandatory hook entries across specify, plan, tasks and implement, excluding constitution hooks. Five entries invoke architecture-check. This count describes command-boundary hooks, not hooks per implementation task.

The ordinary chain validates planned architecture after-plan, validates the same phase before tasks, validates after-tasks, then validates implementation both through phase-context and implementation-check. The latter two use the same `check(..., 'implementation')` path. They also return the same guidance. [Implementation-check](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/commands/speckit.program-kit-governance.implementation-check.md:6) requests another read of spec, plan and tasks that the upstream implement command also loads.

The checks themselves are cheap: a synthetic normal-development test completed four phases plus preflight in approximately 0.004 seconds. Removing them will not by itself solve long implementation runs. Their repeated guidance and agent interpretation can still consume attention and tools.

**Recommended change:** merge phase-context and implementation-check into one pre-implementation operation. Before tasks, reuse the immediately preceding planned check when its architecture inputs are unchanged. Retain after-tasks consistency analysis once and a structural check when task preparation changed the graph or prerequisites. Return a concise status on reuse. Revalidate changed architecture inputs before affected implementation; never suppress a real gate merely to reduce the hook count.

### Knowledge selection is only partly contextual

**High priority for the stated goal of having the right knowledge at the right time.** All 17 registry requirements are eligible in all five supported phases. Every .NET rule uses the broad `dotnet` applicability tag, including concurrency, query, I/O and lifecycle guidance. Conditions are expressed in prose for the agent to interpret.

A synthetic .NET persistence feature returned the same 13 requirement IDs at planning, after-plan, after-tasks, implementation and delivery. Each output contained approximately 1,139 whitespace-separated words and 10.1 thousand characters. These are measured output sizes, not tokenizer counts or an end-to-end latency estimate.

The [intent detector](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/scripts/phase_obligations.py:35) searches feature prose and selected project/source text using keywords. Two probes exposed limitations:

- `C# policy only. No database. API and browser are future out of scope.` activated API and browser guidance despite the exclusions.
- A declared `Notes.Store.csproj` with a `Microsoft.EntityFrameworkCore` PackageReference did not activate persistence during planning. The same specimen activated it during implementation once its `DbContext` source was scanned. The omission is specifically early design guidance, not a demonstrated implementation omission.

The detector also scans selected project source during implementation, while several hook uses request the default planning projection. The command needs an explicit event-to-phase contract; one multifunction command should not leave the agent to infer which projection is appropriate.

**Recommended change:** combine existing engineering configuration, declared project/package identity and normal plan choices. Treat positive capability declarations and exclusions deliberately. Do not make a new feature evidence dossier. Use source inference as a fallback and show a short diagnostic for genuine uncertainty. Planning should explain decisions to make; tasks should carry tests and prerequisites; implementation should return rules for the affected operation; closure should return acceptance and review obligations. Retain `--only` and section pointers for deeper lookup.

### Compiled architecture verification repeats builds

**Medium priority, potentially significant in larger consumers.** After the wrapper has run the consumer build or fallback build, [`repository_architecture.py execute`](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_architecture.py:236) builds every manifest project again, evaluates each through MSBuild, then runs the assembly metadata reader. Incremental builds can reduce compiler work, but process launches and repeated dependency traversal remain.

The rebuild deliberately prevents stale DLLs from becoming evidence. Preserve that protection.

**Recommended change:** let one engineering invocation build the required graph once and pass current evaluated outputs directly to the metadata checks. Alternatively, validate a complete build input identity before reusing outputs. A previous DLL's existence or timestamp alone is insufficient. Include project files, imports, analyzer inputs, generated sources, configuration, target framework, lockfiles and toolchain in freshness decisions.

### Review expectations need sharper responsibility boundaries

**Medium priority.** The registry and guardrails rightly distinguish compiler guarantees from semantic judgment. However, broad demands to substantiate SOLID, ownership, lifecycle and every conditional mechanism can become repetitive if interpreted as a report for each small edit.

Use normal code review to address changed responsibilities and concrete risks. A private pure calculation does not require a new interface or a DI integration test. A transaction, owner check, shared public contract or scoped registration does require behavioral or composition evidence at the appropriate boundary. An analyzer pass never substitutes for that evidence.

Some standards are deliberate Orbyss policy rather than universal runtime best practices. The [.NET profile](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/references/dotnet-engineering.md:171) requires one named type per file and XML documentation for every type and member, including private members. These rules can increase editing and review work. Keep their status explicit and evaluate whether the documentation adds contract meaning; do not weaken runtime guarantees to reduce formatting overhead. Any policy change should be a separate choice, not an incidental efficiency fix.

## Recommended testing cadence

Keep TDD frequent and focused. The behavior under development needs immediate feedback; unrelated behavior does not need repeated execution merely because another task has finished. The Agile Alliance describes TDD as a small test/code/refactor cycle and identifies overly coarse tests and slow suites as common problems. This supports a focused loop without abandoning regression safety. [TDD guidance](https://agilealliance.org/glossary/tdd/)

| Event | Run now | Expand when |
| --- | --- | --- |
| New or changed behavior | The new failing case and the closest existing behavior tests. Build the affected code with its analyzers. | The implementation changes an additional responsibility or shared input. |
| Green and refactor | The operation's relevant regression tests and changed compilation targets. | Refactoring moves a boundary, changes a contract or affects another caller. |
| Progress save, task batch or resume | Checks made necessary by edits since their last successful run. | Dependencies, configuration, generated inputs or runtime assumptions changed. |
| Story completed within an open feature | Story acceptance tests and affected neighboring behavior. | Shared contracts or integration paths were modified. |
| Entire feature or domain implementation closed | Complete acceptance for that delivery, including required provider, contracts, architecture, runtime, documentation and security checks. | Application-wide shared inputs justify the repository-wide acceptance set. |
| Formal review handoff | The full agreed application acceptance set once on the final candidate, plus source review. | New edits invalidate particular results or change the candidate. |
| Package publication | The existing complete publication gate and exact artifact checks. | Follow the repository's existing release rules. |

“Full” must name its scope: full operation, full domain, full application and full Program Kit Release are different things. Completing a consumer story cannot imply running the publisher's Release suite.

The user's proposal to reserve whole-repository testing for feature/domain closure and formal handoff is a strong default. One qualification is necessary: a cross-cutting change can affect other domains before closure. Run those identified dependent tests promptly. If the dependency graph cannot establish a safe subset, surface that as a deliberate broader verification boundary; do not silently defer potentially affected behavior because the edit happened inside one domain folder.

Test selection should be the union of new tests, previously failing tests, tests mapped to changed responsibilities, reverse dependencies and risk-triggered integration checks. Selection is based on the complete delta since the relevant successful check, including committed, staged, unstaged, new, deleted and generated inputs. Looking only at the last edited file or `HEAD` misses changes during a long implement session.

## Blast radius rules that fit this architecture

| Change | Expected affected checks |
| --- | --- |
| Private pure policy implementation | Policy/operation unit tests and known callers. No database or browser solely because the application has them. |
| Public Core contract or invariant | All consuming implementations, substitution tests, serialization adapters and compatibility cases for that contract. |
| Endpoint admission or response | Operation HTTP tests, parser/schema parity and generated contract checks for that API. Browser/client consumers when their contract changed. |
| Persistence query, entity mapping or migration | Owner's real-provider tests, ordering/translation, ownership, constraints and migration compatibility as relevant. |
| Mutation or replay mechanism | Atomicity, concurrency, retry identity, ambiguous commit and acknowledgement tests for the affected operation. |
| DI registration, shell feature selection or lifetime | Real activation/resolution/disposal and affected consumer behavior. |
| Authentication, authorization, common JSON or error envelope | Shared boundary tests and all affected operation/consumer contract groups. |
| SDK, central package versions, build imports, analyzer policy or generator | Dependent compilation/test targets and relevant packaging/runtime compatibility. These changes are not confined by domain folders. |
| Documentation or stylesheet | Relevant link/content or visual/accessibility checks; runtime tests only if delivered executable/generated content changed. |

Start with project dependency closures and explicit test groups in existing test projects. Coverage-informed selection can be added if measurements justify it. Microsoft documents both selecting impacted tests and falling back to broader coverage where dependencies cannot be tracked reliably; selection cannot safely rely on directory proximity alone. Its Azure mechanism is not a drop-in solution for this repository's MTP setup. [Microsoft Test Impact Analysis](https://learn.microsoft.com/en-us/azure/devops/pipelines/test/test-impact-analysis?view=azure-devops)

The generated baseline pins .NET SDK 10.0.202 and Microsoft.Testing.Platform. Use its project/module selection and the selected test framework's filtering syntax. Do not copy VSTest filters into every MTP framework. Discovery must confirm the intended tests actually ran; an empty selection is not green evidence. Current Microsoft documentation also describes newer experimental affected-test options, but they require later tooling and are not a reason to change this pinned baseline for the efficiency repair. [MTP commands](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-test-mtp)

Reuse successful results only while their actual inputs and relevant execution environment remain unchanged. Failed or interrupted execution never supplies acceptance. Preserve original results; describe reused coverage honestly. This local development optimization does not change exact-source Release or paid-worker receipt requirements.

## Knowledge at the right phase

| Phase | Decisions and knowledge to surface | Checks appropriate now |
| --- | --- | --- |
| Intake and specify | User outcomes, ownership, permissions, constraints, failure semantics and unresolved consequential choices. | Scope/ambiguity review. No application build or provider provisioning. |
| Plan | Public capabilities, legal dependency graph, Foundation mechanisms, DTO/admission contracts, lifetimes, persistence consistency, compatibility and test strategy. | Planned graph validation and concrete design findings. Research only a new gap or override. |
| Tasks | Test-to-scenario mapping, dependency order, actual engineering commands and prerequisites. | One completed-document consistency analysis. No repeated broad reference lookup per drafting phase. |
| Implement | Current operation, relevant tests, selected contracts, accepted boundaries and the mechanisms actually used. | Focused red/green/refactor; expand on a concrete change in blast radius. |
| Closure and handoff | Complete acceptance obligations, runtime integration, public/settings/documentation contracts and changed-source review. | Full delivery acceptance and relevant semantic review. Publication checks at their separate boundary. |

For each important practice, identify who enforces it. Dependency direction belongs to architecture checks; selected async errors belong to analyzers; transaction and isolation semantics belong to real-provider tests; error-envelope parity belongs to contract/HTTP tests; SOLID, cohesive ownership and meaningful documentation belong to source review supported by behavior. This prevents five hooks from repeating the same vague request to “check quality.”

The evidence supports selective context, but not deleting guidance wholesale. OpenAI recommends practical repository instructions and task-specific references when the main file becomes large. Anthropic describes retrieving detailed material when it is needed. Program Kit already has the summaries and section pointers needed for that approach. [OpenAI best practices](https://learn.chatgpt.com/guides/best-practices), [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

Recent empirical work found repository context files increased testing/exploration and inference cost without generally improving issue-resolution success in its experiments. Its Python task datasets and tested agents do not establish the effect on this .NET/Spec Kit workflow, nor do they measure all maintainability or security goals. It supports measuring useful guidance rather than assuming more instructions always improve quality. [Evaluating AGENTS.md version 3](https://arxiv.org/html/2602.11988v3)

## Hook changes to make before Notes

| Hook boundary | Recommended behavior |
| --- | --- |
| Before specify | Brief applicable architecture constraints, then reuse confirmed intake. Ask only unresolved material questions. |
| After specify | Clarify material ambiguity, then report specific specification conflicts. No repeated intake or broad design inventory. |
| Before plan | One focused planning projection with known capability choices and genuine unresolved decisions. |
| After plan | One substantive design review and planned graph check. |
| Before tasks | Carry relevant choices and tests; reuse unchanged plan preparation and graph status. |
| After tasks | Analyze the finalized document once; validate structural changes not already checked. |
| Before implement | One combined guidance/structural preflight. No second full context read or build. |
| During implement | No full acceptance hook per task or task count. Focused engineering feedback based on changed inputs. |
| After implement | Run acceptance when the feature is complete or formally handed off; distinguish partial progress explicitly. |

Keep these checks inside normal engineering and existing plan/tasks/review output. Do not introduce a new verification-plan JSON, review ledger, approval checkpoint or signed progress receipt.

Do not implement conditional execution merely by filling the manifest's `condition` fields. The installed upstream commands skip nonempty hook conditions rather than evaluating them, and they traverse configured YAML order rather than sorting by priority. Perform change-aware dispatch inside the hook or a tested adapter, preserve explicit ordering, and verify the installed generated commands. [Spec Kit hook behavior](https://github.com/github/spec-kit/blob/main/docs/reference/extensions.md)

The upstream Lean preset is useful as an example of a concise command, but the locally installed Lean implement command has no pre/post hook dispatch. Adopting it directly could remove Program Kit's required checks. A concise Program Kit implementation command must preserve hook execution, TDD, resumption and final acceptance semantics. [Lean preset](https://github.com/github/spec-kit/blob/main/presets/lean/README.md)

## Notes readiness and what the exercise should establish

The existing [Notes scenario](C:/Users/tech_/Code/program-kit/tests/live/scenarios/foundation-notes/v1/scenario.json) is explicitly a deterministic specimen, in preparation, with paid execution disabled. Its prepared source and independent Host/PostgreSQL oracle are valuable qualification assets. Running the supplied completed specimen proves integration behavior; it does not prove that an agent can reach that result efficiently through specify, plan, tasks and implement.

Before the workflow exercise:

1. Establish focused/affected/acceptance engineering commands and explicit checkpoint rules. Verify that selecting an operation does not invoke unrelated browser/runtime/package stages.
2. Consolidate the duplicate pre-implementation path and make phase projection explicit. Verify that exclusions do not activate unrelated guidance and package identity supplies early design context.
3. Preserve the architecture negatives and actual runtime/provider obligations. Test that narrowing execution cannot bypass a relevant shared-contract or lifecycle regression.
4. Inspect the installed composed commands and hook order, including a partial implement/resume path. Do not assume changing source templates automatically updates an existing installation.
5. Prepare the exact Notes dependency profile, independent oracle and an actual workflow scenario when separately authorized. The journal now records Foundation publication; public Program Kit profile promotion and workflow qualification remain distinct work.

Then observe a genuine Notes flow from the reviewed feature intent. Keep the completed specimen and oracle as external reference/acceptance material, not preloaded solution code for the agent. Introduce tests incrementally and verify owner isolation, revision conflicts, replay, atomicity, uncertainty and bounded response behavior at their appropriate seams.

Measure command duration, test identities/counts, restore/build/package frequency, hook invocations, repeated context reads, relevant source-review findings and agent usage by phase. Attribute repeated runs to changed code, changed environment, retries or unnecessary repetition. Compare like-for-like model, reasoning, platform, toolchain, dependencies and cache state; a single successful run cannot establish a robust speedup.

Use the existing [learning metrics](C:/Users/tech_/Code/program-kit/tests/live/v2/learning_metrics.py) and [learning report](C:/Users/tech_/Code/program-kit/tests/live/v2/learning_report.py) where they fit. Extend ordinary execution logs to capture test selection rather than creating another approval system. Missing token usage remains unknown, not zero.

Useful acceptance criteria for that later exercise are: intended failing behavior is observed before its fix; every required negative scenario remains effective; progress checkpoints do not run full acceptance merely because a task batch ended; unchanged checks are not immediately repeated; shared changes select dependent tests; and full acceptance occurs at the final delivery boundary. Numerical speed targets should follow an observed baseline.

## Verification performed for this review

| Check | Result |
| --- | --- |
| `python tests/validate_normal_development.py` | 12 tests passed; approximately 0.916 seconds reported by unittest. The synthetic four-phase/preflight case reported 0.004 seconds, zero maintained artifacts and zero new approvals. |
| `python tests/validate_architecture_recipe.py` | 22 tests passed with the repository's retained SDK 10.0.202; approximately 13.677 seconds, including real compilation/imported-edge rejection. An initial run could not locate dotnet on PATH; that environment failure was resolved for the rerun. |
| `python tests/validate_repository_verification_hook.py` | Passed fallback/delegation, consumer failure propagation and path-safety scenarios. |
| Synthetic phase projection | Same 13 rule IDs across all five phases; approximately 1,139 words per projection for the selected .NET persistence example. |
| Synthetic scope exclusion | Out-of-scope API/browser wording activated those guidance groups. |
| Synthetic early persistence selection | EF package in `Notes.Store` was missed at planning and recognized during implementation when DbContext source was scanned. |
| Source stability | Product sources unchanged between the initial reviewed commit and the later concurrent journal checkpoint. |

These are targeted audit checks, not full Development, Release, consumer acceptance or Notes qualification. No browser validator was needed for this source/process analysis. Firefox remains subject to the documented local-host limitation and CI authority.

**Recommended next work:** repair execution scope and checkpoint semantics first, then reduce duplicate context and improve phase selection. Preserve the existing quality mechanisms. After those bounded changes pass targeted and ordinary Development validation, Notes can test whether the agent uses them effectively and efficiently through a real flow.
