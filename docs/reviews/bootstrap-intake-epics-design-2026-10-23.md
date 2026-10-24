# Bootstrap epics and seeded feature specifications

The agreed direction is to make bootstrap establish the architecture and roadmap across the supplied product vision. Roadmap items group intended capabilities as epics; one epic can be delivered through several feature specifications. Detailed user input survives as feature seeds. Specification intake reuses that work and settles the selected feature's exact commission.

This design consolidates the user's accepted recommendations from the [analysis and grilling discussion](bootstrap-intake-architecture-analysis-2026-10-23.md#design-discussion). All three implementation sections were subsequently authorized together and implemented on `codex/bootstrap-intake-analysis`, based on `969ccf04d90e9a539df402836c810dc54349bd7b`. See the [implementation and consumer comparison report](bootstrap-intake-implementation-2026-10-23.md) for actual results and remaining limits. The design below retains the agreed acceptance contract.

## Product contract

| Concept | Responsibility | Completion or evolution |
| --- | --- | --- |
| Application vision | Intended value, actors, broad journeys and possible evolution | Evolves with the product |
| Architectural domain | Owns concepts, identity, rules, state and contracts | Evolves through deliberate architecture review |
| Roadmap epic | An agreed scope of capability or outcomes, priority and dependencies | Delivered when its agreed outcomes are satisfied |
| Feature seed | Preserves a proposed boundary and supplied detail for a potential specification | Can be outline-level or highly developed |
| Feature specification | Defines one coherent useful delivery toward its epic | Independently scoped, confirmed, implemented and reviewed |

A domain can support several epics over time. A feature can involve several architectural owners. Neither a source journey, page, entity nor architectural boundary mechanically defines a specification boundary.

For the user's example, Policy management can be a domain, while an epic establishes an agreed policy-management capability. Features might cover maintaining policies, analyzing evidence, renewal and safe retirement. Those names remain examples until discovery establishes useful boundaries. Claim calculation can depend on policy revision and terms contracts without waiting for every policy-management feature.

## Bootstrap intake

Start with the user's supplied description at its actual depth. Capture existing proposed feature boundaries, detailed behavior, examples and reasoning. Grilling tests those boundaries and their relationships with the rest of the vision; it does not force well-developed input back into a vague summary or repeat already answered questions.

Architectural convergence accounts for the supplied concepts and consequential relationships: identity continuity, ownership, independently evolving lifecycles, shared invariants, historical meaning, authorization, consistency, external authorities and irreversible effects. Investigate an uncertainty now when plausible answers would invalidate that understanding or prevent defining the roadmap. Leave detailed feature behavior at its receiving trigger when the architecture can account for it honestly.

Preserve both intended work and exploratory ideas, with the user's degree of commitment explicit. A highly detailed proposal can remain exploratory. Detail is evidence of developed thinking, not evidence of a delivery commitment. Intended epics receive agreed delivery priority; options retain their relevant architectural consequences and a decision trigger.

Intake confirmation still confirms the accuracy of the provisional synthesis. Existing assessment, constitution and architecture review retain their authority. Bootstrap completion supplies an agreed architectural baseline and roadmap, with a recommended starting outcome. It does not bind the complete scope of specification one.

## Roadmap and feature boundaries

Each epic records its intended outcome, scope, non-goals, completion conditions, priority rationale, architectural relationships and known feature seeds. It need not enumerate every eventual specification in advance. Distinguish a real prerequisite from preferred sequencing and from an unresolved architecture question. Make unknown relationships visible rather than inventing a complete graph.

Generate graph/navigation views from the existing roadmap owner. Preserve source-journey and canonical architecture references, while allowing one broad journey to contribute to several features and several supporting journeys to contribute to one feature.

Refining an epic into child specifications is normal elaboration within the agreed scope. Specification intake settles the selected feature's exact boundary and explicit exclusions, challenging both oversized bundles and fragments that provide no useful outcome. Present substantive changes to the epic's promised scope, priority or dependencies in the same affected intake review. Shared architecture changes retain scoped architecture review. Unaffected roadmap work and settled product answers stay available.

An epic's completion is assessed against its agreed outcomes. Completing one child specification is progress; merely completing the currently listed children does not prove the epic complete if a required outcome remains uncovered. Future extensions can become new roadmap work rather than silently extending a delivered commitment.

## Preserve and consume feature seeds

A seed retains the user's proposed boundary and rationale, supplied rules and examples, architectural owners and neighboring contracts, relevant lifecycle/identity decisions, source evidence, unresolved questions and intended-versus-exploratory meaning. Keep supplied facts, derived proposals and unresolved assumptions distinguishable. Record why a proposed boundary was changed.

Use the existing project intent and canonical candidate-slice semantics as the authoring owners, with explicit links to the relevant seed detail. Extend those owners only where the required relationship is currently missing. Preserve rich source sections rather than duplicating them into a new product-model registry. The roadmap links the epic to its feature seeds; generated views supply navigation.

When a feature is selected, the existing specification-intake entrypoint initializes or resumes its draft from that seed and current relevant architecture. Supplied detail remains usable even if other parts are incomplete. Unknown feature details are legitimate draft state. Seed capture does not confirm an unseen feature brief, create future feature branches, or require every future specification to exist.

Independent feature identity is required in addition to the parent epic ID. Each selected feature owns its own brief, review, confirmation and specification reference under the existing specification-intake evidence mechanism. Two features of one epic must not overwrite or invalidate each other's unchanged product intent. Preserve existing confirmed inputs and human answers when resuming.

## Existing implementation owners

| Responsibility | Existing owners to extend | Required behavior |
| --- | --- | --- |
| Intake guidance and synthesis | Governance bootstrap command; intake-method, functional-discovery and intake-artifacts references | Whole-vision architecture, variable input depth, boundary challenge, rich seed preservation and commitment distinction |
| Canonical source and draft authoring | architecture-map schema and validator; bootstrap-intake schema and validator; intake_authoring | Stable source/feature/epic relationships and seed references; staged validation and preservation remain intact |
| First-outcome handling | Assessment command; bootstrap-decisions schema; bootstrap_handoff, bootstrap_context and bootstrap_stages; bootstrap workflow and review packets | Recommended start replaces binding new first-specification scope throughout the producer/consumer chain |
| Epic roadmap and graph | Roadmap command; governance_state roadmap parser, validation and generated views | One epic can reference several features; dependencies express their actual scope; progress and completion follow outcomes |
| Independent feature intake | specification-intake command, reference and script | Feature-owned draft/review/confirmation, parent epic relationship and seed-aware resume |
| Receiving architecture scope | feature_context, feature_knowledge and phase_obligations; applicable bootstrap_lifecycle and consumer-upgrade callers | Resolve the selected feature's brief directly, preserve relevant future/discovery neighbors, avoid reconstructing a brief path from only the epic ID |
| Installed representation and compatibility | Existing installation, managed ownership and upgrade mechanisms; affected fixtures | New commands and schemas install coherently; historical accepted inputs remain readable and unchanged |

This scope must include actual consumers of the old identity assumptions. For example, phase_obligations and feature_context currently reconstruct the intake path from a roadmap entry, while capability_adoption uses a roadmap entry when identifying future work. Adapting specification_intake alone would leave adjacent contracts inconsistent. Historical audits remain read-only compatibility concerns, not routine gates to restore.

## Compatibility and implementation boundaries

Keep existing one-entry/one-feature consumers working without rewriting their confirmed briefs, accepted architecture, completed bootstrap history or locks. Introduce an explicit new identity/relationship contract for new work and a bounded legacy reader for existing shapes. Do not silently reinterpret a historical confirmed first selection as a newly decomposed epic or enlarge previously accepted scope.

Scope migrations to the actual affected active work, retaining history and reporting conflicts for a deliberate revision. No mandatory global rebootstrap, renewed whole-roadmap approval, duplicate approval ledger or second specification lifecycle is required. Unchanged product confirmation remains valid when toolkit metadata or unrelated architecture changes; affected semantic architecture review is separate.

Exact field spellings and CLI switches can be settled through the existing owners during implementation. The observable contracts above, preservation behavior and review boundaries govern those choices.

## Reviewable implementation sections

| Section | Concrete outcome to inspect | Focused verification |
| --- | --- | --- |
| 1 Independent features within an epic | Two specifications have one parent roadmap epic and distinct durable intake scopes; current consumers still resolve their original brief | Confirm both features, alter one, and verify the other survives; reject mismatched feature/epic/path references; exercise feature-context and phase callers |
| 2 Whole-vision bootstrap and seeds | Detailed supplied feature proposals survive authoring; new bootstrap recommends a start without binding the first specification; epic roadmap and dependencies are inspectable | Repeat the coarse-selection counterexample with the new contract; preserve supporting journeys and rich seeds; reject broken references without replacing existing outputs |
| 3 Seeded feature intake and end-to-end review | Selecting a feature reuses its seed, asks the consequential gaps, preserves settled answers and delivers coherent architecture/specification context | Installed deterministic path from draft intake through stage handoff projections and independent feature intake; disclosed same-session rehearsal of question quality and delivery cohesion |

Keep each section coherent across its callers and installed contract. The normal review boundary is after the current section; the user can authorize several sections together. Product design agreement alone does not claim implementation completion.

## Acceptance cases

1. One intended epic has several feature specifications with independent briefs and confirmations. Changing feature B does not reopen unchanged feature A.
2. A broad source journey produces several potential features; selecting one does not silently commission its siblings. A deliberately cohesive feature can still retain supporting journeys.
3. A user supplies a carefully reasoned feature boundary with detailed examples. Bootstrap preserves the detail and rationale, challenges only consequential uncertainties, and later intake reuses the supplied answers.
4. A sparse vision and a detailed vision can both converge. Neither uniform seed completeness nor a fixed question count is required.
5. A detailed exploratory feature remains an option until the user intends it as roadmap work. Its architectural consequences remain visible.
6. Renewal creates a new policy revision, a calculator depends on applicable terms, and deletion must preserve required historical meaning. Bootstrap identifies those seams; later specifications deepen their exact behavior.
7. Domain ownership, epic membership and feature dependency are separately represented. A claim-calculation feature can depend on the relevant policy contract without acquiring an unsupported dependency on the entire policy-management epic.
8. Feature decomposition changes without changing the epic's agreed outcome. Review stays scoped; an actual change to shared architecture surfaces separately.
9. Parent completion checks its agreed outcomes. Delivered child counts or a green structural validator alone do not establish human acceptance.
10. Existing accepted consumers retain their evidence, original scope and runnable ordinary feature intake. Unknown scope and missing prerequisites remain explicit limits.

Run Integrity and mapped Affected checks under the repository validation inventory for actual implementation changes. Add narrow regression coverage through the existing authoring, handoff/context, roadmap, feature-intake and feature-knowledge test owners. Choose installed/bootstrap checks for the affected contract with an explicit reason; do not infer a need for unrelated runtime or browser matrices. Same-session rehearsals remain labeled simulations, and deterministic tests make no independent-agent behavior claim.

## Current handoff

All three sections are implemented and independently reviewed. Earlier analysis checks still describe the original source only. The [implementation report](bootstrap-intake-implementation-2026-10-23.md) records new source validation, installed behavior, matched disposable outputs and the outstanding Windows execution limitation. Human product acceptance remains separate from implementation and automated checks.
