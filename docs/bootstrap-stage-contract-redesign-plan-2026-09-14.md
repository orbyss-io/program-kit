# Bootstrap responsibilities, decisions and handoffs

Status: approved and implemented for deterministic validation on `codex/repository-sync-coordinator`.
The user additionally required executable default assignment whenever a selection is absent.
See [implementation and validation](bootstrap-stage-contract-implementation-2026-09-14.md) for the
actual scope and evidence. A fresh human-owned live trial remains the next acceptance exercise;
this document does not authorize automated paid phases. The plan extends
[the critical review](bootstrap-system-critical-review-2026-09-14.md).

## Intended result

A consumer starts with an ordinary product vision. Program Kit progressively establishes a small
useful first slice, an evidenced architectural approach and a usable handoff to Spec Kit. At every
point the operator can see what is being resolved, which decision or capability is needed, what
has actually been verified, and what happens next. Future journeys do not acquire first-slice
implementation detail merely because they were mentioned during intake.

The core change is an executable contract for each handoff, using existing authorities and native
Spec Kit execution. More explanatory Markdown, more approvals, or fewer checks alone are not the
solution. The product should maintain routine mechanics; agents should exercise judgment where
product meaning, design alternatives and evidence interpretation require it.

## Findings from current implementation

| Boundary | Current implementation/evidence | Gap |
| --- | --- | --- |
| Intake to assessment | `commands/speckit.program-kit-governance.bootstrap.md` requires subdomains, contexts, founding candidates and a dynamic view for every journey before confirmation. | Intake must construct substantial architecture before the architecture stage. Future scope increases mandatory authoring. |
| Intake proposals to architecture | `architecture_map.py:validate_bootstrap_alignment` requires identical subdomain, bounded-context and capability evidence; the context's modeling invariants preserve seed dynamic relationships/order. | Confirmed observations and proposed interpretation need distinct evolution rules. Architecture is told to refine proposals while much of their representation is frozen. |
| Assessment to research | `bootstrap_context.py:stage_plan` selects research questions by classification; the research command limits work to those questions. | Provider design assigned as `project-owned-design` needs an explicit later owner and exit contract. A general instruction to research does not guarantee its resolution. |
| Architecture to subsequent stages | Architecture validates structure, alignment and governance; tooling output validation primarily checks required artifacts/size. | Producing valid documents can succeed while essential design inputs remain unresolved. That must be an intentional, visible stage result. |
| Human decisions | Workflow YAML provides assessment approval, constitution ratification and final bootstrap approval. Worker questions are outside those native gates. | Approval of an accurate packet does not answer unanswered design questions. The trial continued after two asynchronous constraint questions without recorded answers. |
| Roadmap to closure | Closure has a generic dispatch instruction and no generated stage brief, unlike most other producers. | It reconstructs dependencies and execution details through broad source reads and custom test infrastructure. |
| Proof failure to recovery | `STAGE_STARTS` maps `execute-compatibility-proofs` back to `architecture-prerequisite-closure`; proven-closure reuse requires passing planned evidence. | A routine execution failure can re-enter paid recipe authoring rather than retry the same valid recipe after environment repair. |
| Bootstrap to feature | `before_specify`, `before_plan`, `after_plan` and implementation hooks already separate feature intake, knowledge projection, architecture review and sync. | Bootstrap needs a concrete handoff to these existing boundaries, without preimplementing work that those phases own. |
| Accepted alternative to setup | Governance permits an explicit Foundation host opt-out, but `repository_sync.py:context` raises `PKS003` when that selection has no alternative engineering adapter. | An upstream valid choice is not necessarily downstream executable. Adapter availability must be checked when presenting/adopting an alternative, with a supported route or an early explicit incompatibility. |
| Upgrade | `upgrade_program_kit.py` already invokes the shared sync coordinator's upgrade phase and distinguishes offline changes from pending package verification. | New bootstrap mechanics must reuse that execution/evidence model instead of introducing a second baseline authority. |

Sources are under `extensions/program-kit-governance/` unless explicitly named otherwise.
The latest trial established that the recently repaired profile projection works. These findings
do not claim that every existing validator or knowledge item is wrong.

## Recommended phase model

These are logical responsibilities, not a requirement for one paid agent session per row.
Preserve independent validation boundaries even when one bounded producer resolves adjacent work.

| Phase | Must resolve before handoff | Existing capability/command to retain or adapt | Handoff accepted by the next phase | Legitimate later work |
| --- | --- | --- | --- | --- |
| 0. Execution readiness | Installed component coherence, interpreter/child-shell invocation and agent-dispatch prerequisites. Check stack-specific availability when that stack becomes applicable. | Intake launcher, installation validation, `codex_bootstrap_preflight.py`, toolchain providers. | Valid environment report or an actionable setup pause before paying for dependent work. | Tools unrelated to the selected scope; application provisioning. |
| 1. Product intake | Actors, meaningful journeys, intended first useful outcome, known hard constraints, explicit preferences and material unknowns. | Bootstrap intake + Program Kit grilling; existing authoring builder and source evidence. | Confirmed product understanding, proposed first-slice boundary, future portfolio and owned questions with due phases. | Endpoint layouts, class names, database schema, detailed acceptance examples. |
| 2. Scope and capability assessment | Which journey can be useful first; managed/guided/consumer coverage; dependency consequences; explicit conflicts and scope trade-offs. | Assessment, capability index, catalog and shared profile dependency checks. | A selected first-slice candidate, dependency closure and a bounded research/design worklist. | Detailed future journeys and speculative integrations. |
| 3. Research and architecture decisions | Material first-slice provider/stack choices, evidence, source/version constraints, ownership, runtime composition and architectural risks. Every question has an owner; needed human answers are collected before dependent design proceeds. | Research, architecture, existing decision register and ADR/map machinery, persistence/profile selection. | Complete proposed approach with exact inputs for applicable proofs; safe defaults and reviewed deviations are explicit. | Feature-internal policies and future/production-only choices at their recorded triggers. |
| 4. Verification and setup planning | Which obligations are inherited, which must be proved for this bootstrap, which belong to feature implementation, and what setup each check needs. | Tooling, phase-obligation inventory, repository-sync planning, catalog recipes and prerequisite ledger. | An executable scoped plan, available recipe/adapters, provisioning prerequisites and one precise terminal contract. | Consumer application scaffolding that requires its feature plan. |
| 5. Architecture compatibility | Execute the checks due now using selected inputs. Preserve pass/failure evidence. Resolve failed design assumptions through the appropriate decision owner. | Adapt closure into bounded planning; shared `package_execution`, restore providers, compatibility runner and proof-plan executor. | Evidence for first-slice architectural risks, or a classified and actionable pause/failure. | Full feature behavior and runtime tests whose contracts have not yet been specified. |
| 6. Bootstrap review and completion | Present and accept the actual approach, relevant ADRs and principles; confirm first-slice scope and remaining deferred work. Machine evaluation establishes eligibility. | Existing review/ratification records, roadmap, readiness evaluation and native workflow completion. | Accepted scoped architecture and one explicitly selected Ready-to-specify entry with a derived feature handoff. | Future candidates, feature details, production approval and release publication. |
| 7. First feature | Grill/confirm the exact feature brief; specify and clarify behavior; plan implementation and verification; materialize owned targets; implement and prove the journey. | Existing Spec Kit hooks, `specification-intake`, `phase-context`, `architecture-check`, sync, implementation checks and delivery obligations. | A verified first vertical slice with source-bound evidence. | Later roadmap entries. |

The roadmap is refined throughout these phases; it should not be invented only after most
architecture is fixed. Early prioritization scopes the research and proof work. Final roadmap
status remains owned by the existing canonical roadmap and changes only with current evidence.

Ready-to-specify, ready-to-plan, ready-to-code and ready-to-deliver must retain distinct meanings.
Bootstrap cannot demand feature behavior proofs before the feature defines that behavior. Equally,
an unresolved architectural choice that makes the first specification incoherent cannot be hidden
as ordinary later work. Each obligation needs an explicit earliest-use point and enforcement point.

## The executable handoff contract

Consolidate the currently scattered stage declarations into one executable registry. It should
drive briefs, producer output validation, dispatch prerequisites and recovery routing, while
referencing existing domain authorities. It must replace overlapping declarations, not become
another document that agents manually keep consistent.

Each stage declares:

- required facts and decision states, including first-slice scope;
- applicable capabilities and their canonical knowledge sources;
- exact supported commands/adapters, scoped inputs and allowed mutations;
- outputs owned by this producer and evidence required to accept them;
- questions/decisions that must be resolved now and allowed deferrals with triggers;
- structured outcome, next owner, corrective action and retry boundary;
- source fingerprints and invalidation dependencies.

Keep the native Spec Kit run state authoritative for execution. A structured stage outcome can
distinguish `complete`, `needs-user-answer`, `needs-design-decision`, `needs-provisioning`,
`verification-failed` and `tooling-error`; these are proposed result categories, not an assertion
that those native statuses already exist. Map them to supported native pause/retry/failure behavior.
Verify the installed engine's transport before implementing new question behavior.

Questions require durable IDs, necessary context, a recommendation where possible, their affected
decision, and a recorded response. Use the existing decision/prerequisite sources and native run
inputs; introduce only the missing question-lifecycle data. A worker returning after asking a
question must not imply that the answer arrived. The operator sees one answer-and-resume path.

## Human interaction and approvals

Choose checkpoints by decision consequence, rather than retaining a fixed count of document gates.
The recommended user experience has three kinds of interaction:

1. **Confirm understanding and scope.** “This is the first useful journey and these improvements
   come later.” Confirm consumer meaning; distinguish proposed technical interpretation.
2. **Resolve a consequential choice.** “This dependency needs a decision; here is the researched
   recommendation, trade-offs, defaults and impact.” Invoke only when required. A known safe default
   is explained in review; it does not create another question. Missing answers pause dependent work.
3. **Accept the evidenced baseline and principles.** “This is the architecture we will build on,
   what was verified, and the first feature we can specify.” Record explicit constitution ratification
   and architecture acceptance with their respective authority, even when presented together.

Do not add a compulsory approval for every technical phase. An extra pre-proof decision is needed
only when the proposed activity changes agreed scope or needs separate resource permission.
Adopting a proposed technical approach for bounded evaluation is distinguishable from accepting it
after verification. Existing paid live-run and external-action authorization remain separate.

The review packet is a derived decision view: recommended choice, why, consequences, rejected
alternatives where material, defaults/deviations, passed checks and their limits, and remaining
owned deferrals. Files remain linked for detailed audit. Users should not need to verify JSON
coherence, package IDs or filenames to make an informed product decision.

A final approval is never a substitute for a passing check. Before asking for final acceptance,
the engine should show whether acceptance can actually complete this bootstrap. If a first-slice
dependency still needs a human answer, route that question first. Deliberate partial design review
can remain available, labeled as partial and without a completion claim.

## Knowledge and capability ownership across the full flow

| Knowledge/capability | Bootstrap responsibility | Feature responsibility | Upgrade responsibility |
| --- | --- | --- | --- |
| Domain policies, state transitions and lifecycle | Identify domain language, ownership and critical invariants; distinguish confirmed observations from provisional models. | Define exact admitted actions, policies, effects and outcomes during specification; implement and test them. | Preserve semantics; reopen only affected assumptions. |
| Modularity, Core/Abstractions and extension points | Select ownership boundaries and valid integration mechanisms, with evidence-backed exceptions. | Apply them in project/type/runtime dependencies and architecture tests at the earliest executable stage. | Reconcile changed platform extension contracts and revalidate affected edges. |
| Foundation host and release bundle | Inherit the published-host model and select composition; verify relevant platform risks. | Build feature packages and the settings/Nuplane/feed bundle; verify activation and journey behavior. | Preserve consumer settings; reconcile managed changes and invalidate affected evidence honestly. |
| Persistence and authentication | Select material providers/mechanisms through existing profiles or researched consumer choices; resolve constraints and scope architectural proofs. | Specify transaction/admission behavior and prove actual policies, races and failures. | Check compatibility changes without silently replacing consumer choices. |
| .NET engineering, typed objects and SOLID | Select the profile and applicable enforcement mechanisms. | Project relevant rules before planning/coding and validate source/runtime evidence as applicable. | Update managed tools/profile inputs and rerun affected checks. |
| Browser/UI/accessibility and API compatibility | Inherit profile defaults and establish supported tools, protocol direction and ownership. | Verify the actual UI journey and contracts; toolchain smoke tests are not product acceptance. | Reconcile tool/contract baselines and verify impacted behavior. |
| Package/toolchain sync | Resolve a single coherent execution context; use isolated scratch provisioning for architectural proofs. | Reuse the same coordinator for planning, owned implementation setup and restore evidence. | Use its existing upgrade phase and explicit online verification path. |

Use `knowledge-inventory.json`, `phase-obligations.json`, the catalog, phase projections and existing
validators as source authorities. Add missing first-use/required-by mappings there or in the
consolidated stage registry; do not copy the full knowledge base into every phase instruction.
Test that every adopted capability has a supported next-stage action or an explicit incompatibility.

Provisional domain models may evolve during architecture with a traceable rationale and meaningful
review. Immutable user evidence remains immutable. A proposed bounded context is not transformed
into a user requirement merely because it appeared in a confirmed intake synthesis. Future
journeys can remain a concise portfolio until analysis is needed; preserving them does not require
fully detailing every future interaction before the first slice.

## Maintained execution and recovery

Provide maintained recipe implementations for managed SDK, npm/browser tools and Foundation-host
checks. The first-slice plan selects checks and parameters from the canonical catalog/profile inputs.
Consumer-specific compatibility work still permits bounded custom recipes, with the same runner,
provisioning, redaction, reporting and cleanup contract.

Preserve failed JUnit and classified diagnostics before scratch cleanup. Record the attempted case,
exit status, provisioning state and sanitized underlying reason. A generic failure with no next
action is itself a diagnostics-contract failure. Never mark a failed check successful to ease recovery.

Retries are determined by changed inputs:

- Unchanged valid recipe plus repaired environment: rerun only the failed check and required
  provisioning; reuse matching successful evidence.
- Changed recipe: invalidate that recipe's evidence and rerun its affected checks.
- Changed provider/design: reopen the owning decision and invalidate dependent plans/evidence;
  obtain the appropriate review for changed meaning.
- Changed consumer intent: return to the relevant intake questions and propagate the explicit
  impact, preserving historical records.

Do not require a paid architecture-authoring stage to recover from an ordinary missing browser or
tool execution problem. Preserve the saved workflow's approval and version-migration safeguards.

## Implementation sequence and completion criteria

| Increment | Concrete work | Evidence required before proceeding |
| --- | --- | --- |
| A. Failure evidence | Preserve failing case/results and bounded sanitized diagnostics; add explicit failure classification. | Failed, malformed, missing-result and timeout cases retain useful evidence without exposing seeded test secrets. |
| B. Contract ownership | Consolidate stage declarations; map adopted capabilities, first-use and due points; implement durable question handoff. | No orphan capability/decision; a missing mandatory answer pauses before downstream dispatch; approval cannot answer it implicitly. |
| C. Producer boundaries | Separate consumer evidence from provisional model; revise scope-first intake, bounded research/design and derived review packets. | Proposed model refinement preserves user facts; first-slice inputs become complete; future journeys stay represented without unnecessary detail. |
| D. Shared execution | Maintained recipes, closure brief and package/sync integration; remove obsolete generated mechanics/instructions. | Real deterministic managed checks pass; failure/retry paths work without regenerating unchanged recipes or creating another baseline. |
| E. Feature and upgrade integration | Carry exact scope, authority and obligations into existing hooks; reuse the same sync/check providers on upgrade. | First-feature handoff applies domain/.NET/modularity knowledge; consumer config, explicit overrides and deferred targets survive upgrade. |
| F. Assembled trials without agents | Drive native workflow boundaries with controlled producer outputs and real supported executors. | End-to-end stage sequencing, decision pauses, proof failure, targeted retry, approval invalidation and completion behave correctly. Clearly label simulated producer evidence. |
| G. Fresh live acceptance | One user-started intake, bootstrap and first vertical slice; retain prior runs for comparison. | Observed completion, product-quality review and measured efficiency; no claim of live success before this evidence exists. |

Use targeted tests and the Development suite during implementation. Release validation remains its
own publication gate. Paid phases retain their existing separate authorization requirements.

Representative deterministic cases must include: a technology-neutral vision with managed sign-in;
explicitly anonymous browser use; a supported consumer-owned provider; unsupported override with
an early actionable result; unknown provider constraints; a changed answer after approval; absent
browser/runtime; failed and malformed probe results; unrelated future blockers; changed managed
pins; and an existing consumer upgrade. Test whether supported alternatives can reach the next
stage, not just whether forbidden alternatives are rejected.

## Measurement and release decision

Record per-stage uncached input, cached input, output and reported reasoning counters without
double-counting; capture wall time split by active reasoning, execution and waiting where observable.
Track repeated full reads, unnecessary stage reruns, repeated unchanged restore/proof work,
ad-hoc generated harness code, and repairs caused by missing handoff information.

Quality review asks: is the first journey useful and bounded, are technical choices substantiated,
is applicable knowledge enforced, are deferrals appropriately owned, and do claims match evidence?
Less work is not success if these outcomes degrade. Do not impose arbitrary improvement percentages
before establishing comparable fixtures and conditions. Shared component metrics can be compared
across the historical and fresh trials; changed product scope must be disclosed.

The design-review decision is whether this responsibility model and implementation sequence are
accepted. It is not a publication decision. The current failed consumer remains learning evidence;
the next expensive run should exercise the revised integrated pipeline rather than another isolated
patch followed by a hopeful retry.
