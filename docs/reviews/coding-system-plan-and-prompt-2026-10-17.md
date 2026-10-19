# Coding system: feature implementation plan and agent prompt

**F8 approval update, 19 October 2026:** F1–F8 are human approved within the
recorded acceptance scopes. The human completed the separate Spec Kit session,
reviewed the snapshot-pattern explanation and said “Super. I approve. Commit and
close this.” Read the [F8 approval/closeout](coding-system-f8-checkpoint-2026-10-18.md)
and [final matrix](coding-system-final-handoff-2026-10-18.md). The 126.204s/120s
fresh overrun remains over-budget; approval preserves every failure, cost and
proof limit. Commit the scoped F8 work locally and close its task. Retain review
material and the stopped consumer; no push, publication or cleanup is authorized.
The development skill was separately created on codex/program-kit-development-skill;
its other chat owns that work and commit. This supersedes older pending/deferral
wording below and does not authorize merging the separate branch.

**F8 review update, 18 October 2026:** F1–F7 remain human approved. The human
agreed the F8 recommendations and extended Q2 to an actual human-operated agent
journey. F8 implementation and scoped installed proof are retained for review;
read the [F8 checkpoint](coding-system-f8-checkpoint-2026-10-18.md) and
[final F1–F8 matrix/handoff](coding-system-final-handoff-2026-10-18.md), starting at
its guided actual-output index. Final fresh execution completed functionally but
exceeded 120s at 126.204s; retain that finding. The separate untouched consumer is
prepared for the human to perform Specify/Clarify/Plan/Tasks/Analyze/Implement with
an agent and return its exact session for analysis. No agent session has started.
This is the current continuation boundary; earlier checkpoint wording is historical. Stop at F8 human review;
complete acceptance and F8 approval remain pending. Do not commit, push, clean,
publish or create the deferred development skill without further authority.

**Approved implementation scope, synchronized with main on 17 October 2026.** The human approved the feature and its knowledge-ownership, modularity, domain-event, endpoint and browser refinements, then requested that implementation build on the latest release changes. This plan and its [implementation prompt](coding-system-agent-prompt-2026-10-17.md) are the current self-contained handoff. They do not start or message an agent.

The original investigation and approval remain historical context in Git at commit `dabe83d85da148ed426ef2fb7dff9088f2f0e5c2` and in the original planning checkout. Main subsequently retired those reports and their campaign gates. This handoff carries forward the approved feature behavior without restoring obsolete reports, ledgers or release procedures. Historical findings do not automatically establish a defect in the current source.

## Outcome

A supported implementation task should arrive with settled product intent, applicable architecture/models/contracts, ownership and evaluation duties. The coding system translates that context into code through composable skills and safe scaffolding, then reconciles the actual change with the duties that apply. An endpoint that queries PostgreSQL receives both endpoint and persistence guidance plus its security, configuration, privacy, transaction, cancellation and testing obligations. A file's name or one exclusive role cannot establish complete applicability.

The system is also a core learning system. Maintainers and consumers can teach a new semantic pattern, implementation alternative or measured improvement once, qualify its scope, and demonstrate that a later applicable coding task actually uses it. Consumer-repository patterns are first-class inputs and may remain private. A long reference list, a newly registered skill or an agent's assertion that it read documentation does not establish either use or correctness.

Existing knowledge is substantial: endpoint, provider ownership, Options, constructors, factories and SOLID guidance already exists alongside curated primary-source links and versioned captures. The investigation does not establish a mirror of all Microsoft documentation or prove which individual references the stopped consumer consulted. This feature repairs selection, context and application where missing; it does not promise automatic enforcement of every engineering practice in arbitrary code.

Each active engineering rule has one authoritative knowledge source. Selection, task briefs, skills, scaffolds, validators and review reference or resolve that source; they do not maintain independent policy copies in prompts, scripts or generated application code. Executable implementations remain necessary, and independent tests establish their behavior. A catalog entry or generated instruction alone establishes neither application nor correctness. This plan defines feature delivery requirements; it is not another consumer rulebook.

## Authority, baseline and boundaries

Implementation base: **`fc402ef784c025caced1770cd12f64af1a0bdf45`**, fetched from `origin/main` on 17 October 2026 (latest published-release README update, following PRs #45 and #46). Create the handoff/feature work on top of this commit; do not start from the older maintenance branch. Read current `AGENTS.md`, [validation](../validation.md), [releasing](../releasing.md) and [consumer engineering](../consumer-engineering.md). This baseline includes the validation/release redesign and subsequent native public-delivery upgrade fixes. Refresh actual selected source/profile facts before implementation; the base is not feature qualification.

Use an isolated feature branch/worktree based on the implementation base plus this documentation handoff. Preserve the shared dirty checkout and authored changes. Do not copy unfinished changes from another owner. Reconcile dependencies against current source and native mechanisms; consume qualified implementations, and report a concrete remaining capability gap without recreating historical repair campaigns or waiting on obsolete ledger statuses. Source changes require fresh affected validation.

The trial consumer remains stopped. No implementation, cleanup, US4 work, paid calls, reset, migration, account initialization or messaging is authorized there. The agreed future target is the **existing** consumer: human-directed removal of implementation/generated implementation followed by a new Specify phase. Historical diagnostics, decisions, locks, approvals, accounting and uncertain provider outcomes remain preserved; they do not automatically approve a fresh design. Neither implementation prompt executes that restart.

Do not add a global file-write interceptor, universal query/storage/PDF framework, speculative production hosting framework, automatic upstream self-modification, telemetry/polling or mandatory new approval artifact. Routine engineering decisions inside accepted contracts remain the implementer's responsibility. Consequential missing product, data, security or architecture decisions return to their owning phase with a concrete diagnostic. Explicit pattern override does not change an accepted domain invariant or mandatory profile contract.

## Session checkpoints and inspectable fixtures

Implement F1 through F8 in separate human-led sessions, one item per session. Before implementing an item, investigate its actual implementation seams and grill only unresolved implementation choices; do not reopen the approved feature scope or decisions already settled. Confirm shared understanding at the end of the interview before implementing that item, and preserve the decisions and next-session handoff in this plan or its linked checkpoint notes. This session sequencing refines the existing implementation approval rather than asking for approval of the feature again.

Each item must have a runnable, inspectable fixture demonstrating its delivered behavior before its session checkpoint is closed. Define the scenario, inputs, expected output, meaningful negative cases and proof limits during that item's interview. Run and review the actual output with the human; do not defer all observable results until the complete implementation phase. A passing test summary alone does not supply the requested walkthrough. Human inspection and automated correctness evidence remain distinct.

Use both incremental fixtures and final integrated proof. Each session demonstrates its delivered behavior; the final integration demonstrates a connected journey through the completed system, supplemented by focused scenarios for contracts requiring distinct environments. Reuse maintained per-item scenarios and deterministic installed-command routes rather than build a separate final testing system. Keep the existing acceptance matrix and independent behavior tests; report the actual scope and any uncovered scenarios.

Fixture review mode retains the fictional disposable consumer, actual command output and named before/after snapshots. Provide a short review index with context: what the fixture represents, where to start, links to the exact files/output to inspect, what to look for, which differences matter, expected versus actual positive/negative outcomes, rerun commands and proof limits. Walk through those concrete outputs with the human, including anomalies and open questions. Keep the review material available across turns and sessions until the human confirms that review is finished; reaching the end of the test process is not review completion. Cleanup can then remove the owned disposable consumer and scratch snapshots while preserving the bounded actual results, invocation/source identities and findings used as checkpoint proof. Ordinary non-review automated runs can retain their normal cleanup behavior.

No fixture starts a coding agent, paid/provider operation or the stopped trial consumer. Do not claim unimplemented later items, real human product acceptance or complete feature acceptance from an earlier checkpoint.

### Workflow learning and future repository development skill

Use F1 through F8 to try and improve this contributor workflow: investigate and grill unresolved decisions, agree a plan, divide it into reviewable sections, implement and test each section with a guided output review, then run final integration and deliver the feature through the normal repository contribution route. Keep concise learning notes with each session handoff: what was tried, what the human could actually inspect, what worked, friction or failures, agreed adjustments and what to try in the next item. Preserve observed results and uncertainty; suggestions are not proven improvements. Reuse this section or linked checkpoint notes rather than introduce a campaign ledger or new consumer artifact.

After the workflow has been demonstrated to work in practice and the human agrees it is useful, create a repository-scoped Program Kit development skill from the observed lessons and working fixture conventions. The future skill should help subsequent contributor work follow the proven approach, with slice size and testing proportional to the change. It is not a consumer coding rule or a speculative skill to create before the trial has produced evidence. Reference maintained validation and contribution/publication procedures instead of duplicating them; feature delivery follows the authorization for that work. Continue refining the approach during this implementation plan.

## Functional contract and implementation sequence

The following sequence is implementation guidance, with one accountable feature owner. Filenames and representation are engineering choices made against current source; the behavioral contracts and proof below are required. Reuse native phase, profile, changed-input, managed-source and verification owners rather than introduce competing systems.

### F1 — discover knowledge and establish canonical ownership

Current local implementation: branch `codex/coding-system-f1` carries F1. Read the
[F1 checkpoint](coding-system-f1-checkpoint-2026-10-17.md) before continuing. The human
approved F1 conditional on retiring C# composition-preset projects and explicitly
authorized that correction. Preserve its validation/cost disclosures and retained
review output; do not restart F1 or automatically advance to F2.

**F1 implementation decisions accepted in the 17 October 2026 session:**

- Q8: retire the C# composition-preset role and its peer-reference exception. Shell/deployment
  configuration selects features; each owning feature registers services/lifecycle contributions.
  Retained graphs receive actionable diagnostics and explicit repair; history/captures and real
  shell/resource/host composition remain intact. Add visible direct-selection and rejection proof.

- Give a rule its own identity when its applicability, obligation level or evaluation differs. Group related rules for readable guidance and retain existing requirement identities as compatibility groupings.
- Keep the shipped `eng/architecture_rules.py` tables authoritative for their exact executable constraints. Catalog entries address the actual symbols; prose owns broader semantic principles. Guidance resolves table values when needed, and native consumer checks remain independent of toolkit Markdown.
- Use explicit source kinds and resolution contexts. Maintainer discovery can inspect repository sources; installed guidance resolves shipped sources and selected captures. Repository-only material keeps its discovery disposition. When active consumer guidance requires an unavailable source, report the missing dependency explicitly rather than silently substituting another source.

The accepted F1 review fixture uses a fictional API task and an unrelated browser task. Inspect discovered rules from marked prose, the actual executable architecture table and an exact publisher capture, with retained history explicitly classified. Show actual produced guidance and applicability/exclusion reasons, before/after output from changing a canonical rule in the disposable fixture, and clear failures for missing or ambiguous rule sources. Preserve relevant independent negatives. This establishes scoped F1 discovery and consumption proof, not later scaffolding, application behavior or whole-feature acceptance.

Discover technology, coding style, domain-modeling, architecture and engineering knowledge throughout the repository before restricting active support. Inspect normative references and accepted decisions; manifests, profiles and command/hook prompts; script and C# policy declarations; schemas, EditorConfig and build settings; templates, scaffolds and examples; tests and counterexamples; versioned publisher captures; and historical research, proposals and evidence. Separate reusable principles, provider/version facts, executable mechanisms and consumer-specific decisions. Discovery is broad; adoption into active coding support requires applicable authority and qualification. Retained history and merely mentioned technologies are not active support claims.

Extend the existing `phase-obligations.json` responsibility/source registry and its actual producers/checks rather than introduce a competing inventory. The earlier review found a Markdown-centered inventory and policy embedded in `phase_obligations.py`, shipped `architecture_rules.py`, registry guidance and prompts. Refresh those observations at the implementation base; counts and retired report assertions are not acceptance targets. Reuse `decision_knowledge.py` canonical rule resolution where suitable and follow the ownership principles in [consumer engineering](../consumer-engineering.md).

Produce a reviewable catalog grouped by purpose, with attributable rule-level entries and explicit source dispositions. Use the following discovery map as a coverage floor, not as a second set of normative rules. Below, governance, dotnet and building-blocks denote the respective `extensions/program-kit-*` directories; shipped `eng/` refers to the .NET consumer template.

| Knowledge family | Required discovery coverage | Existing source owners to inspect |
| --- | --- | --- |
| Domain language and modeling | Subdomains, bounded contexts, ownership, aggregates/value objects, invariants, lifecycle states, valid outcomes and proportional use of domain patterns | governance `references/software-language.md`, `modularity-and-contracts.md`; repository `docs/decisions/` |
| Modularity and collaboration | Core/runtime/API/provider/helper/bridge roles; retired C# composition-preset diagnostics, compile boundaries, semantic capabilities, dependency direction, accepted Core edges, inheritance and cross-context translation | governance `references/modularity-and-contracts.md`; dotnet `references/technology-profiles/dotnet.md`; shipped `eng/architecture_rules.py` and `repository_architecture.py` |
| Domain and integration events | Core-owned immutable facts, selected Foundation dispatcher and typed handler registration, awaited independent reactions, failures/cancellation, and separate durable integration/outbox requirements | governance modularity reference; repository ADR 0007; selected versioned Foundation DomainEvents capture |
| Vertical slices and endpoints | Actor-to-outcome slices, operation placement, transport admission/mapping, delegation to owned application capabilities, domain policy and provider effects | governance `references/vertical-slicing.md`, modularity reference; dotnet profile and qualified typed-operation example |
| Features, services and lifecycle | Activation identities, feature-owned registration, explicit dependencies, root/shell/request scopes, factories/disposal, provider preparation, application admission, startup/workers, cancellation/drain and actual resolution | dotnet profile, `references/dotnet-engineering.md`; selected CShells/Foundation Tasks and registration sources |
| Configuration and middleware | Exact owned keys, typed options, defaults, secret references, activation validation/reload; middleware ownership/order/scope, authentication, antiforgery, authorization, headers and failure boundaries | dotnet `references/foundation-compositions.md`, `secure-web-profiles.md`, engineering reference; native options validators and middleware capture |
| Construction, runtime and source style | SOLID, valid construction/variants, coherent method phases and extraction, member/file layout and documentation; async/concurrency, time/deadlines, resources/memory, queries, deferred initialization and measured performance | governance `references/programming-guardrails.md`; dotnet engineering reference; actual analyzer pin, EditorConfig and build policy |
| Persistence and contracts | Provider-private records/mappings, independent accepted schema, transactions/concurrency/migrations, controlled SQL, pagination, typed JSON admission, OpenAPI/compatibility and generated client/runtime validation | dotnet `references/persistence-profiles.md`, `implementation-boundaries.md`, `label-validation.md`; native contract/export/check routes |
| Browser product experience | Journey/global/page layouts, responsive compositions, branding/theme/tokens, typography/spacing/hierarchy, forms/components, icons/motion, focus/keyboard/accessibility, feedback/recovery, local state/disposal and session boundaries | governance `references/ui-design-model.md`, `ui-experience-v1.md`, `ui-feedback-and-recovery.md`, TypeScript profile; native/Tailwind/existing-system adapters and selected Forms/Localization |
| Security, diagnostics and effects | Deployment versus application authorization, parsing/path/URL/process boundaries, private diagnostics, observability, idempotency/replay, uncertain outcomes, physical resource ownership and fencing | governance guardrails; dotnet secure-web, retained-input, PDF and cross-resource references; qualified native examples |
| Technology and reusable capabilities | .NET/MSBuild/NuGet, Foundation/CShells/Nuplane, ASP.NET, EF PostgreSQL/SQL Server/SQLite, TypeScript/JavaScript/Vite, browser auth profiles/Keycloak, JSON Schema/OpenAPI, selected Foundation/Forms/Localization/MCP and conditional parser/OCR mechanisms | selected profiles, package/lock manifests, building-block catalog and publisher captures; no inferred framework-wide support |
| Testing, delivery and maintenance | Native tests and actual feature activation, architecture/contract checks, real providers, browser/Axe/human review, generated ownership, installation/update, toolchains, CI/security/provenance and dependency maintenance | native `eng/` recipes, tests and validation selectors; repository `maintenance-policy.json`, release policy and maintained procedures |

Each active rule needs stable identity, semantic purpose, authoritative location and owner, applicability/exclusions, mandatory/conditional/recommended level, required context, compatible technology/version/profile, recipe/scaffold/check/review links, evidence scope/freshness and limits. Preserve exact dependency pins in their existing manifests/locks and publisher identities in captures; the catalog references them. One discovery entry point resolves the applicable canonical sources and their execution/evaluation routes; it does not copy the whole corpus into one document or require consumers to maintain another catalog.

For each source, distinguish available, selected/routed, observed consultation and demonstrated application. Historical consultation without evidence stays unknown. Identify hidden policy, useful unrouted content, conflicting/obsolete duplicates, manual references, conditional material and retained history separately. Active completeness is relative to supported responsibilities; discovery findings outside that support retain an explicit disposition. Prepare the old-to-canonical mapping now, with replacement consumers and proof. Remove obsolete active routes only after F8 replacement proof; do not defer canonical ownership until final cleanup.

### F2 — prepare the task and compose applicable coding skills

**F2 interview decisions accepted on 17 October 2026:** prepare the current operation
and tasks while retaining feature constraints; compose actionable canonical-bound units
through the existing command/registry rather than independent static skill policy files.
The human explicitly confirmed that F2 includes the extensible application mechanism:
adding a declaration selects a new unit without changing the composer algorithm. F3
retains richer teaching, evidence qualification, local/shared alternatives and retirement.
Use the retained task baseline for actual-change reconciliation before progress/closure
and direct engineering/presentation admission. Missing mandatory context blocks affected
work with its owner/repair; unknown semantic findings stay honest. The agreed fixture is
a fictional private-notes HTTP/PostgreSQL task plus unrelated browser scope, extension
selection/exclusion, evaluated imports, manual changes, deliberate failures and explicit
proof limits. The human confirmed shared understanding and authorized implementation.
See the [F2 checkpoint](coding-system-f2-checkpoint-2026-10-17.md) for actual output,
validation, limitations and review status. Preserve all settled F1 decisions.
The human approved F2 on 18 October 2026, authorized its commit and requested F3
in a fresh session. Preserve the disclosed limits and retained review material.

Extend the actual plan/task-to-implementation route so its prepared context identifies the request and boundaries, accepted specification and decisions, model/contract/schema ownership, affected projects/operations, selected effective profiles/packages/toolchains, current verification ownership, local patterns and material uncertainties. Keep the ordinary agent view bounded and link attributable detailed context; do not embed repeated complete histories.

Compose skills by actual semantic responsibility across files and projects. Before code production, expose the selected obligations, chosen alternatives and why, required scaffold/edit route and evaluation. An endpoint may have no body or be small; a helper is not automatically a new composition library. Use evaluated project settings and selected native APIs, not guessed names or package documentation from another version. The preparation path should be reusable for a feature, repair and refactor; do not require a new human approval for every method or local choice.

After code production, inspect changed source, evaluated project roles and actual dependencies to reconcile new/removed responsibilities. Unmediated/manual edits must encounter this reconciliation before supported task completion/admission. Do not claim that all file writes outside Program Kit are intercepted. Missing mandatory support/context/checks stop the affected work, preserve progress and name the capability/owner/normal next action. Independent work may continue. Routing is a diagnostic/workflow result, not automatic task messaging, dispatch, installation or waiver.

### F3 — maintained shared and consumer-owned pattern inputs

**F3 interview decisions accepted on 18 October 2026:** the human answered yes to
all recommendations and confirmed the implementation frontier. A single qualified
applicable local pattern can join the existing composition route; replacement or
competing contextual alternatives require an explicit scoped choice. Precedence,
suitability and qualification remain separate, without weakening F1/F2 contracts.
Use actual maintained checks and ordinary semantic-review evidence with content-bound
freshness and declared expiry where needed. Selected stale/missing proof blocks the
affected scope without fallback; unrelated work remains independent. A single editable
draft assists prose/code submissions without executing them or inferring semantics.
The agreed inspectable private-notes fixture includes shared/local choices, later-task
use, unrelated exclusion, an independent invalid implementation, stale/incompatible
inputs, retirement and privacy limits. The human confirmed shared understanding before
implementation. See the [F3 checkpoint](coding-system-f3-checkpoint-2026-10-18.md).
The human approved F3 on 18 October 2026, authorized its commit and requested F4
in a fresh session. Preserve its proof limits, failures and retained review material.
This session does not start F4.

Implement a versioned pattern contract for semantic identity/invariants, applicability and exclusions, compatible alternatives, provenance/owner, required context, recipe or transformation if any, positive/counterexamples, actual checks/review, evidence/freshness and limits. Permit human-friendly plain-language/code submissions; tools help prepare the maintained fields and reveal missing proof rather than demand expert manual editing across scattered files. Keep executable scaffold/check code owned and reviewed through existing repository mechanisms; recording a submitted pattern does not authorize executing arbitrary supplied code.

Give each active rule one authoritative location. Registry entries hold routing and execution/evaluation bindings, not independent restatements of the rule. Generated briefs resolve relevant canonical text and observed version facts with provenance. Migrate policy hidden in script strings, hard-coded policy tables and prompts through the reviewed mapping; keep mechanism algorithms and version adapters in code with attributable rule bindings. Executable schemas, analyzer settings or native publisher contracts may already own a constraint: reference that authority rather than restating its values as a new rule. Do not build a universal prose interpreter or reimplement native frameworks. Rule/profile/source changes invalidate affected derived views and qualification; tests must still detect incorrect implementations independently of generated policy/scaffold data.

Select qualified consumer-repository patterns through the same actual route as shared patterns. Keep three separate decisions explainable: **precedence** for explicit specialization/replacement, **suitability** among compatible alternatives in this consumer context, and **qualification** of supporting evidence. No numeric ranking is required. Preserve mandatory contracts even when a local pattern is preferred; diagnose ambiguous/conflicting declarations with the real owner. Consumer semantics may specialize a recommendation but changes to accepted model/architecture invariants return to their owner.

Expose why a pattern applies, does not apply, is stale or lacks evidence, without copying private source into public diagnostics. Local qualification uses normal consumer review/testing. Local use does not require upstream publication. Shared promotion is an explicit, separately reviewed selection with privacy/provenance preserved. Pattern/code/profile/source changes identify affected stale qualification; immutable historical evidence remains history rather than being rewritten to current success.

### F4 — safe scaffolding and subsequent editing

**F4 approved on 18 October 2026; commit and a new-session F5 prompt authorized.**
The human confirmed all four recommendations: a finite label slice using
F2/F3, immediate consumer ownership, create/identical/conflict behavior, digest-bound
diffs through native transactions, and retained installed/native proof. The human
later explicitly prioritized correcting the stale Foundation default and authorized
retaining unchanged Forms browser evidence when the GitHub CLI token lacked package
scope. The current default is Foundation 0.3.6, Build 0.3.2 and Exporter 0.2.7, with
new lock/captures and explicit historical browser provenance. Read the
[F4 checkpoint](coding-system-f4-checkpoint-2026-10-18.md), both guided indices and
its native cost overrun. The final review also approved mandatory invocation
readability rules and their template/oracle follow-up. Approval preserves the
reported limitations and failed/over-budget statuses. Preserve review material,
the shared dirty checkout and earlier failures/budgets. F5's separately confirmed
implementation is now human approved; read its
[checkpoint](coding-system-f5-checkpoint-2026-10-18.md) and guided output.
The proposed development skill remains deferred.

Build or consolidate small scripts/recipes for supported structures where generation improves consistency. Inputs come from F2 accepted context and F3 selection. Qualify endpoint/DTO/operation boundaries, owned provider query/mapping/transaction responsibilities, typed options/native binding consumption, selected browser/UI integration and project/test ownership. Prefer extending existing native generators and typed-operation examples once their owner has qualified them.

An HTTP endpoint is a transport adapter. Its code admits the wire request, applies declared endpoint metadata/policy, passes cancellation and mapped input to an owned application/use-case capability, and maps the established result to HTTP. Business rules, workflow orchestration, persistence/transactions and domain-event dispatch belong to their semantic/application/provider owners. Moving those responsibilities into an API-local helper does not satisfy the boundary. Keep domain policy pure in Core and runtime orchestration/effects in the appropriate implementation; do not invent a generic Business layer, mediator or pass-through interface per endpoint. Review responsibilities and behavior, not line counts. Generate complete vertical slices across those owners and the actual client journey where applicable; an operation-folder layout alone is insufficient.

Mark source ownership accurately. Created application/business code belongs to the consumer. Subsequent edits/refactors use the same skills and evaluation. Regeneration or supported transformations need explicit managed boundaries, inspectable changes, preconditions, idempotence where applicable and conflict diagnostics preserving customizations. No framework update overwrites business logic because a scaffold originally created it. Missing supported scaffolding is distinguishable from a required missing invariant: a compatible manual coding route may satisfy a recommendation; it cannot silently waive a mandatory check.

### F5 — concrete initial pattern families and related repairs

**18 October 2026: human approved F5; commit and a new-session F6 prompt authorized.**
The human confirmed shared understanding before implementation, separately
authorized correcting stale active Foundation pins, and approved the delivered
work after the guided and inline happy-path review. Read the
[F5 checkpoint](coding-system-f5-checkpoint-2026-10-18.md), complete
[family table](../coding-seeds.md) and linked actual-output guide. Approval retains
all proof limits/failures/budgets. F6 has not started; retain every fixture/failure
and use its [separate session prompt](coding-system-f6-session-prompt-2026-10-18.md).

These are required investigations and qualified reusable outcomes, with proportional adapters for applicable supported profiles. They are not mandates to transplant the stopped consumer's domain model. Existing qualified examples should be reused and strengthened rather than replicated. Historical N/D/C/R finding IDs below retain traceability to the original investigation; they are not current maintenance-ledger gates. Recheck every claimed defect or missing mechanism against the implementation base before choosing work. Preserve qualified current native mechanisms and repair only actual remaining gaps.

| Family / evidence | Required implementation and evaluation outcome |
| --- | --- |
| Modular domain ownership and vertical slices; approved review refinement | Demonstrate a complete actor-to-outcome slice across the actual Core/application/API/provider boundaries, with domain policy, valid outcomes, semantic capabilities and dependency direction attributable to canonical rules. Seed mixed-role, peer-implementation, transport/provider-in-Core and cross-operation-helper negatives. Compilation, package, runtime feature and deployment boundaries remain distinct. Use actual scoped review where structural checks cannot prove ownership. |
| Thin transport endpoints; approved review refinement | Qualify a native endpoint delegating business work to an owned application capability, with endpoint-local HTTP admission/mapping and metadata. Prove business behavior independently of HTTP and exercise the real HTTP mapping. Negative implementations place a business decision, persistence access or workflow/event orchestration in the endpoint or an API-local helper; detect the misplaced responsibility through appropriate checks/review. Do not demand empty handlers or remove legitimate transport logic. |
| Domain events and independent reactions; approved review refinement | Select the exact Foundation DomainEvents mechanism for a scenario that needs an owner to announce an immutable fact to independent reactions. Prove actual feature registration, publication and awaited typed handler execution, payload ownership, cancellation/fault semantics and absence of peer implementation coupling. Include a task where events do not apply and negatives that misuse event order for a mandatory workflow or claim durability from in-process dispatch. Follow ADR 0007 and the canonical modularity rule; do not inject a dispatcher into an aggregate, force events into every mutation or implement an unapproved durable integration system. The user's lack of observed use is a discovery prompt, not proof that every prior agent omitted the mechanism. |
| Service registration, activation and middleware; approved review refinement | Prove actual selected feature activation and production service registration/resolution, intended root/shell/request lifetimes and disposal, nondefault options reaching their owner, invalid configuration rejection at that activation boundary, initialization/worker ownership and required middleware scope/order. Seed missing/wrong registrations, captive dependencies, root-only validation and incorrect middleware placement/order. Reuse native framework mechanisms and owner repairs; graph metadata or a direct test-only registration cannot establish runtime correctness. |
| Browser capability application and visual quality; approved review refinement | Inventory available page/component/form/feedback capabilities and show selected ones used in a coherent real product journey. Qualify responsive global/page composition, typography/spacing/hierarchy, brand/theme consistency, semantic actions, focus/keyboard, field errors and loading/empty/failure/unknown/success states where applicable. Preserve selected Forms/Localization, native session controls, privacy and recovery. Review rendered actual application screens at representative viewport sizes and existing human story handoff; neither a component gallery, generic CRUD shell, screenshots alone nor passing Axe/protocol checks establishes usability or human acceptance. Diagnose a missing adapter instead of claiming package-name support or replacing the accepted frontend. |
| Confirmation handling, Options and configuration; N9/N22, existing sign-out decisions | Preserve the user's exact confirmation request: examine explicit choices/defaults, when confirmation is required, immutable confirmed intent and consumption, as well as typed Options binding/validation. Respect existing never/when-unsaved/always and extensible unsaved detection. Use the current qualified native binding seam; do not create a competing binder. Prove actual selected values reach the actual owner, invalid/missing options fail clearly and configuration/credentials/paid grants remain distinct. Generated bindings carry nonsecret scalars and secret references; protect infrastructure policy and prevent secret literals/resolved-secret leakage in files, errors, evidence or low-entropy hashes. |
| Factories, valid construction and SOLID | Inspect real constructors/lifetimes and missing practices. The observed deployment constructor performs bounded private-file I/O/JSON despite existing no-I/O guidance; provide a qualified loader/factory or equivalent supported separation preserving scope, privacy, disposal, transport and no-grant/accounting rules. Existing unit-lease factories may already be correct. Demonstrate cohesion, compatible substitution, appropriate client interfaces and dependency direction in real consumers. Do not generate an interface/factory for every class or claim compliance by counts. |
| Independent relational conformance; N24/D79/D83 | Verify accepted ownership/schema authority against the actual activated provider/EF model independently of the implementation's own constants; then derive/provider-quote mapped identifiers and bind query values, with closed reviewed SQL structure. Prove actual runtime model, JSON/cache/immutability and query behavior. Preserve controlled raw SQL; runtime-created FormattableString is not proof of compiler-literal SQL provenance. Use semantic/source checks with honest limits where needed. No live-data migration tool, all-LINQ rewrite or consumer database operation. |
| Browser async identity/recovery; N21, N26 refinements | Demonstrate bounded FileReader abort, late crypto/result suppression, generation identity across selection/date/navigation/session and current-only failure clearing/reselection. Do not claim crypto itself is abortable. Bind confirmed immutable input before admission/allocation. Preserve and reconcile a known action after lost acknowledgment or edits without duplicate submission. Use fictional offline/native browser scenarios; the original unretained transient remains unknown. |
| Private failure diagnostics; N17 | Produce useful bounded authored case/location identity from trusted runner/source inventory, with honest setup/assertion/timeout/retry outcomes. Do not infer authenticated source or causes from a regex hint, emit raw exceptions/pages/DOM/dynamic titles/private paths or fabricate stacks. Qualify output, attachments and both streams with private canaries and actual failing cases; preserve counts and unknown locations. No canonical reporter defect was established. |
| Journey context and temporary UI; N26/D74–D77/D84/D86/D87/D92 | Existing plan/tasks must identify a temporary demo's actual limits, intended final product home and owned integration/relocation/removal including navigation/tests. Implementation consumes accepted actor/entry/outcome, temporal and meaningful-choice semantics. Review the normal entry journey; protocol/Axe success alone does not establish usability or human acceptance. Keep intermediate backend demos possible. No new approval artifact, insurance-specific framework or stopped-consumer US4/cleanup. |
| Protocol/native contract use; C3/C5/N7/N8/N10/N13/N14 | Route to actual selected APIs/types/overloads/analyzers, generated contract/client and supported copy/parser recipes. Distinguish compile/setup failures from behavioral reds, correct strict guards from defects and offline SDK proof from paid application continuation. Cover actual serialized JSON/HTTP envelope bounds, finite decoder formats, repeated-resource accounting and process/runtime limits. Reuse current parser/operation implementations; new patterns teach their qualified contracts and honest unsupported paths. |
| Resource/fixture ownership and recovery; R4/R6/R9/N15 | Teach deployment versus runtime authority, case-owned queues/fixtures, independent outcomes without insertion-order assumptions, physical publish/erase fencing, retained high-water marks, whole-operation deadlines and observed physical replay. Reuse qualified examples; do not claim a database lease alone fences physical writes, metadata proves a physical object or a universal storage framework is required. |
| Selected UI/build/dependency obligations; C2/C6/C10/N11/N18/N20/N23/N27/N28 | Carry selected profile, toolchain, native build/export order, generated input ownership, text/link roles and actual browser integration into coding tasks. Use current qualified native tools; do not build second selectors, snapshot policies or token compilers here. Provider branding uses the current native binding owner; historical D89 does not transfer that ownership. |

For every seed, state whether the historical cause is confirmed, a consumer error, a correct guard, missing capability, runtime limit or unresolved claim; make the new prevention claim narrower than its actual proof. Teach the principle where applicable across supported profiles and diagnose missing adapters instead of claiming a PostgreSQL example qualifies SQLite or SQL Server. Profile-wide scope concerns the applicable responsibility inventory, not every combination of every technology package.

### F6 — teaching, qualification, adoption and retirement

**18 October 2026: human approved F6; commit and a new-session F7 prompt authorized.**
The human confirmed all four recommendations before implementation and approved
the delivered guided/inline source/output review. Read the
[F6 checkpoint](coding-system-f6-checkpoint-2026-10-18.md) and
[F7 session prompt](coding-system-f7-session-prompt-2026-10-18.md). F7 requires its
own investigation/interview/confirmation in a fresh session; do not start it in
the F6 commit session. Earlier approvals, failures, cost disclosures and retained
consumers remain unchanged. The development skill remains deferred.

Provide an explicit teach/improve workflow taking a problem, supplied code/evidence or known gap and preparing one reviewable contribution: pattern, applicability, guidance, scaffold/check/example updates and missing proof. Support refining/replacing/retiring an existing pattern and preserving alternatives. Route proposed architectural changes through normal accepted artifacts. Ordinary maintained review/qualification/versioned adoption supplies authority; do not invent another approval ceremony per pattern or make learning automatic unreviewed self-modification.

Qualify a proposed performance improvement against identified workloads/runtime/resources with correctness, adverse tradeoffs and counterexamples. A local benchmark cannot create a universal rule. Demonstrate an end-to-end learning round: a supported task exposes a gap, a new local pattern is taught and qualified, a later fresh task selects and applies it, an incompatible task does not, a changed input marks proof stale, and an explicitly selected publishable lesson can follow normal shared promotion without exporting unrelated private material.

Use maintained extensions for new technologies/pattern adapters: same context, ownership, source/version, applicability, positive/negative installed proof and limits contract. Registration alone is not support. Unknown/incompatible/overlapping declarations are diagnosed. A small practical extension seam is sufficient; no production adopter or secret-store framework is required now. Existing selected capabilities must remain usable through existing qualified workflows during feature development.

### F7 — independent evaluation and completion

**18 October 2026: F7 human approved; commit and separate F8 prompt authorized.**
The human reviewed the actual output and explanation of F7's journey, foundations,
independent proof and limits. The human answered yes to all four recommendations
before implementation. Use
the [F7 checkpoint](coding-system-f7-checkpoint-2026-10-18.md) and
[review handoff](coding-system-f7-review-handoff-2026-10-18.md). Derive applicable
mandatory/conditional duties from existing canonical owners, bind ordinary scoped
review and actual native/toolkit evidence in existing task/delivery state, and
enforce them at completion. Preparation remains usable before execution. Reuse a
new fictional owner-report consumer, fixed compiled positive/negative oracles,
disposable canonical role-table mutation and unrelated browser scope. Preserve
strict qualification, source ownership and human review/waiting boundaries; an
explicit native execution observation supplies no reusable qualification.
The installed journey retains a 120s budget/240s timeout. Integrity retains 60s;
Affected uses approved F6 `f2cb90b8f6254cb61052d1b49e6e189e2206e652` as its base.
At the F7 checkpoint F8 had not started; its separately authorized session used the
[session prompt](coding-system-f8-session-prompt-2026-10-18.md). The development
skill remains deferred. Earlier approvals, raw failures, costs, qualification limits
and review material remain unchanged. F7 approval is not complete feature acceptance.

Evaluation combines appropriate compiler/schema/analyzer/tool checks, actual provider/browser/native behavior, source/semantic review and consumer human review where necessary. Keep each obligation's evidence source and scope visible. A satisfied structural checker does not prove semantic correctness. An agent report that it selected guidance is routing evidence; independent negative examples and actual consumer execution are application evidence. Unknown obligations cannot disappear because no check was listed.

For canonical ownership, change one rule in a disposable qualified fixture and show the affected task brief and linked scaffold/check expectations reflect that source without edits to duplicate policy strings. Unrelated tasks remain unaffected and prior affected proof becomes stale. Retain independent negative behavior oracles so a mistaken rule, generator or adapter cannot manufacture its own success. This qualification does not require executing every check for every task or treating every rule as mechanically decidable.

Use existing verification selectors and prerequisite closure. Do not run every deterministic test after each task or start coding agents from deterministic validators. Completion must reject an applicable mandatory duty that was omitted, incompatible/stale inputs, unsupported actual mechanisms and fabricated/replayed qualification. Report a concrete owner/repair route. Do not make human approval loops consume engineering time after an engineering task has handed off correctly.

### F8 — cleanup, installation, adoption and migration

F8 is the final planned implementation item. Its separate human-led session has
implemented cleanup and installed journeys; see the [F8 checkpoint](coding-system-f8-checkpoint-2026-10-18.md)
and [final acceptance handoff](coding-system-final-handoff-2026-10-18.md). Human
review, the requested observed agent session and fresh runtime disposition remain
pending. Final integrated review uses the existing matrix, maintained per-item
proof and actual installed routes. F1–F7 are approved; do not
reopen their settled decisions. See the
[F8 session prompt](coding-system-f8-session-prompt-2026-10-18.md). The F7 commit
session does not begin F8 or authorize review-material cleanup or the deferred skill.

After replacement routes have actual proof, consolidate/remove obsolete active guidance, duplicate rules/examples and stale routes. Keep a reviewed old-to-new/retire mapping with purpose and retained coverage. Useful but unrouted knowledge is wired into actual applicability; intentionally manual or conditional knowledge is honestly classified. Do not copy all unused text to an archive to claim cleanup, manufacture use or delete history. Preserve captures/profiles needed by existing consumer locks, diagnostics, approvals, decisions and accounting.

Qualify packaged installation and existing-consumer updates, preserving authored source, local patterns, managed ownership, locks and immutable witnesses. A new default is available, not silently adopted. Show bounded current diagnostics and discoverable next actions for legacy contexts, unsupported patterns and stale evidence. Existing authority and update rules govern migration; do not reset the stopped consumer or activate new production/private/provider behavior.

## Acceptance and proof matrix

| Scenario | Required observable proof |
| --- | --- |
| Endpoint plus owned provider query | Real prepared artifacts select composable skills; generated/edited code compiles and executes actual endpoint/provider behavior; an omitted model owner, incompatible API or unbound value is caught at the appropriate boundary. |
| Canonical rule discovery and consumption | Discovery includes scripts/schemas/build settings/templates/captures as well as Markdown. Every active discovered rule has one owner and actual applicability/execution/evaluation bindings; manual/conditional/history dispositions are explicit. A rule change reaches its applicable task and linked realization without maintaining duplicate policy text, marks affected proof stale and preserves independent negative oracles. |
| Modular vertical slice and thin endpoint | Actual API code owns transport admission/mapping and delegates business work to an owned capability. The business behavior executes independently of HTTP; real HTTP exercises the mapping. Mixed boundaries and business/persistence/workflow logic hidden in an endpoint or API helper are rejected or receive an explicit unresolved review finding. Folder naming alone cannot pass. |
| Selected domain events | A justified independent-reaction scenario uses the selected Foundation dispatcher and actual registered typed handlers with observed outcomes and failure/cancellation behavior. An inapplicable task does not select events. Ordering-as-workflow, aggregate dispatcher coupling and unsupported durability claims are detected. |
| Services, options and middleware | Actual activated registrations resolve at intended scopes and dispose correctly; nondefault values reach the owner; invalid options fail at the actual activation boundary. Required middleware executes in the proper shell scope/order across success, denial and faults. Wrong/missing registration, captive scope, root-only validation and ordering negatives cannot pass on metadata alone. |
| Browser product journey and rendered quality | Real application pages use applicable maintained capabilities, coherent responsive layout and owned visual inputs. Browser tests exercise actual controls, state/focus/recovery/session behavior and relevant viewport sizes; source/rendered review establishes visual consistency and the existing human handoff records acceptance. Unqualified adapters, missing applicable states and unused gallery-only patterns remain visible. |
| Later edit/refactor/manual change | Actual changed roles are reconciled; new duties cannot bypass completion; authored customizations survive regeneration and conflicts preserve both evidence and source. |
| Coverage of current supported profiles | Inventory every applicable role/adapter and test meaningful representative positive/negative paths per distinct supported contract. Version/profile mismatch and missing adapter fail actionably; no package-name coverage claims. |
| Consumer-local patterns | Explicit override, contextual alternative and qualification are separately observable. Private lesson reaches the next applicable task without upstream publication; conflicts, stale proof and unrelated private data stay controlled. |
| Learning round | A genuinely new supplied pattern becomes a reviewed/qualified improvement consumed by a later task; negative applicability and invalid implementation are detected. Performance claims retain reproducible scoped comparisons. |
| Seed semantic contracts | Actual native/provider/browser examples plus independent negatives establish F5 outcomes. Test fixtures do not merely repeat implementation constants, and emitted diagnostics remain private. |
| Installed fresh consumer | Packaged normal commands/hooks deliver the same context/skills/scaffold/check routes on a disposable deterministic consumer; source-only helper tests are insufficient. No agent/paid worker is launched by this test. |
| Installed update | Qualified old consumer with authored edits/local patterns updates through supported managed paths; conflicts are diagnosed, history remains intact and old/new routes have attributable parity. |
| Cleanup | Every active source has a maintained purpose/route/review disposition; obsolete material is removed only after replacement coverage. Historical captures/locks/accounting are unchanged. |

Run `./scripts/Test-ProgramKit.ps1` (Integrity), then `python scripts/run_validation.py --suite Affected --changed-from fc402ef784c025caced1770cd12f64af1a0bdf45` for actual changes. Use the single maintained `tests/validation-inventory.json` capability/check definition. Establish the representative Baseline once if this process has not been adopted; do not replay it or broad native/database/browser/Host matrices for every task. Expensive scenarios need a concrete affected contract and, where manualOnly, explicit `--check` and `--reason`. Unknown paths/history, missing prerequisites, timeouts, overruns and failures remain explicit gaps or failures, never implicit success or a full-suite fallback. Extend affected edges/checks where the new feature requires them. Do not start coding agents from deterministic validation or install device toolchains. Use Chromium/WebKit locally where appropriate; known Firefox spawn UNKNOWN remains a host limitation, and affected Firefox acceptance belongs to the relevant CI scenario. Preserve actual failure diagnostics and report concise outcomes and limits.

Dependency discovery, pin/lock updates and profile qualification are separate maintenance, not a mandatory release-preparation step. Retain existing consumer locks and exact captured profiles. PRs and explicitly selected exact-source candidates use current package CI: fast integrity, one archive build, clean Windows/Linux installation and installed-entrypoint smoke, and applicable security checks. CI verifies its package mechanics and does not attest local semantic execution; maintainer review accepts reported validation and concrete limitations. Publication requires the exact inspected artifacts and native `publication` environment approval before tagging/publishing, under [releasing](../releasing.md). Do not restore broad main-push/tagged acceptance, custom readiness receipts or remote evidence handoffs. This feature handoff authorizes no publication, tag, device installation, paid/provider execution or worker phase.

## Dependencies and completion report

The feature owns knowledge discovery/selection, pattern/scaffold/learning outcomes and the proof specified here. Current main already includes native and release repairs made since the original planning snapshot. Inspect the actual merged configuration, build/export, manifest, UI-input and token mechanisms before extending them; reuse their qualified contracts and do not create competing implementations. A real unresolved dependency needs an actionable current owner/repair route. Historical campaign IDs, source hashes and another branch's old passing receipts neither establish completion nor block ordinary work.

Implement in reviewable increments: F1/F2 context and coverage; F3/F4 selection and code lifecycle; F5 semantic seed families; F6/F7 learning and evaluation; F8 cleanup and installed adoption. Keep interim unsupported status honest. Each increment reports changes, source/profile identities, actual checks/results, open limits and next action. Final completion requires every functional acceptance row and every mapped feature obligation, not an arbitrary count of skills or files. Report dependencies still blocked, and preserve original failure/uncertainty history. No formal new owner ledger or intake route is inferred from this planning document.

## Prompt for the dedicated coding-system implementation agent

Use the [standalone implementation prompt](coding-system-agent-prompt-2026-10-17.md) with this complete plan. Approval is already granted, including the instruction to build on the fetched main commit. The implementation owner creates or reuses the isolated feature branch. This handoff does not dispatch or message an agent.

> Implement the approved coding-system feature on an isolated branch based on main `fc402ef784c025caced1770cd12f64af1a0bdf45` plus this documentation handoff. Read AGENTS.md, this complete F1–F8 plan and acceptance matrix, the standalone prompt, and current docs/validation.md, docs/releasing.md and docs/consumer-engineering.md. Approval is already granted. Preserve canonical ownership, all semantic families, independent negative proof and existing consumer/private/history boundaries. Follow Integrity plus affected validation and current package/publication policy; do not restore obsolete reports, ledger gates or broad Release/Development matrices. Do not dispatch paid workers or publish. Report actual changes, checks, gaps and reviewable results; feature completion requires the acceptance matrix.
