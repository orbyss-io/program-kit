# Functional discovery

## Purpose and depth

Use this guide during bootstrap intake and when deepening an affected feature. Relevant knowledge
guides questions, examples and consequences before it guides implementation. Explain the discovery
areas to the human and name the subject of each question group. Reuse supplied answers; explore
gaps and contradictions. Question count and speed are not completion criteria.

Establish a coherent functional baseline for the first useful outcome. Keep later journeys as
actor/outcome summaries with consequential dependencies; deepen their details when commissioned.
The areas below are a coverage lens, not a fixed questionnaire or a new approval sequence.

## Discovery areas

| Area | Explore with the human | Preserve for the handoff |
| --- | --- | --- |
| Purpose and actors | What problem is solved, who initiates and benefits, where work happens, and what success looks like | Goals, actor meaning, context of use and scope |
| Concepts and identity | What important terms mean, what distinguishes instances, what can change, and how concepts relate | A small vocabulary, identity and ownership rules, relationships |
| Lifecycles and policies | Meaningful states and transitions, who can act, preconditions, decisions and rules that must remain true | Lifecycle, permissions, invariants and relevant rejection cases |
| User journeys | Trigger, steps, decisions, information needed, observable outcome, interruptions and recovery | Coherent success and material alternative paths |
| Experience and presentation | Information hierarchy, navigation, interaction, feedback, layout, existing branding and visual preferences | Product-specific experience decisions and provisional proposals |
| First delivery outcome | Which journey creates useful value first and which other journeys it needs | Candidate slices, dependencies and acceptance examples |

Start from a real or proposed situation in the user's language. Walk through it with the human,
then use the emerging concepts and rules to ask dependent questions. Iterate between journeys and
the model; do not demand a complete entity inventory before discussing work. A concept is not
automatically a database entity, bounded context, service or specification. Distinguish entities
with enduring identity from values, actors, policies and technical mechanisms where relevant.

## Knowledge-informed questions

Before forming each frontier, consult only the relevant sections of routed knowledge that supply
the missing reasoning. Reuse sections already current in context. The capability index is a
navigation aid, not a keyword-only limit: derive needs from the described behavior. Persistent
records imply durability questions even when the user never says "database". Explain the product
consequence behind a question or recommendation; avoid asking users to choose implementation jargon.

| Knowledge | Product questions and examples it can reveal |
| --- | --- |
| Domain modelling and modularity | Is a name a label or identity? Who owns a record? Which rules relate several operations? Which words have different meanings for different actors? |
| Lifecycles and policies | What must be true before an action? Which transitions are legal? What happens to existing records when a policy changes? |
| Persistence and consistency | What must survive a later session or interruption? Is current state enough, or does someone need history? What should happen when edits overlap? |
| UI/UX and accessibility | What information supports a decision? How does someone move through the journey, learn its result and recover? Which input/device or assistive needs affect interaction? |
| Security and privacy | Who may perform the operation on this particular subject? What may other people discover? Which information must remain private? |
| Failure and recovery | What does an interrupted action mean to the person? What can they safely do next, and what must not happen twice? |

Use the relevant `Identity`, `Policies and decisions`, `Transition path` and `Lifecycle` sections
of software-language.md, `Proportional domain-driven design` in modularity-and-contracts.md, and
`Slice contract` in vertical-slicing.md. For included UI, use `Independent choices` and applicable
interaction/accessibility guidance in ui-experience-v1.md. Consult provider-specific persistence
guidance only after its stack/provider is relevant; translate its guarantees and limits into
product questions. Do not make the whole reference library required reading for each round.

These are examples, not questions to ask verbatim. Preserve explicit exclusions: a history question
does not add history, and lifecycle discovery does not reopen deletion already excluded. Use supplied
examples first. Ask an open walkthrough question before offering alternatives when the goal or
meaning is still unknown; recommend options once that understanding supports a reasoned recommendation.
Invite the functional architect to challenge the proposed model and identify a missing situation.

Clearly applicable technical defaults still settle tools, packages and mechanisms. They do not
settle consumer policies, workflow meaning or a person's taste. Label absent preferences as
unspecified, never as affirmative preferences. Respect an explicit request to use a design baseline.

## UI and experience discovery

When a human-facing UI is included, invite existing brand/design-system constraints, reference
applications, visual character and theme preferences. Ask this in a coherent experience group,
reusing answers already supplied. Derive information hierarchy and navigation from the first journey
before recommending an archetype or layout. Explain alternatives through use: list/detail versus
separate screens, for example, rather than requiring the user to select internal profile enums.

Explore creation/edit entry, feedback, empty/error states and recovery when they change usability
or product meaning. A brief screen sequence or textual layout sketch can expose assumptions; use
a wireframe when it resolves a consequential choice. Do not generate artwork or high-fidelity screens
merely to complete intake. If no visual preference is supplied, offer a disclosed provisional design
baseline with its workflow rationale in the existing synthesis. Retain accessibility, privacy and
reduced-motion obligations regardless of visual taste. Detailed styling can wait for the feature;
layout and interaction questions that change the first journey cannot all be deferred as styling.

Use the relevant UI guidance in `ui-experience-v1.md`. Keep its technical adapter defaults separate
from proposed navigation/brand choices. Never apply UI discovery to an explicitly headless product.

## Functional handoff

Keep a compact functional model in the existing `project-intent.md`. Give important concepts,
lifecycles, policies/conditions and flows stable product references, and connect them:

**Concept -> lifecycle -> policy/condition -> journey step -> candidate slice -> acceptance example.**

For a rename journey, identify the subject and actor, the naming policy, ownership and revision
conditions, the changed state, visible success, duplicate/conflict rejection and safe recovery.
Preserve the agreed meaning and evidence; do not invent an operation because an example mentions it.

Record each fact once and cross-reference it. These product references belong in prose; use existing
journey/slice IDs and answer evidence when projecting the canonical map and intake. Do not add new
JSON fields, duplicate evidence registries, separate model dossiers or confirmation receipts.
Map existing language, ownership, invariants and lifecycle fields to this model. The specification
deepens exact fields, edge cases and acceptance criteria while preserving the established meaning.

A journey can produce several independently useful slices; one useful slice can need supporting
journeys. Preserve their identities. Screens, endpoints and CRUD verbs do not automatically become
specification boundaries. Architecture chooses physical boundaries from the functional evidence.

## Convergence and receiving work

Before synthesis, walk through the first useful journey and its material alternative paths using
the current model. For each relevant discovery area, identify established evidence, an unresolved
product decision, an exclusion or a legitimate later trigger. Do not count a filled heading, an
empty frontier or a generated architecture map as demonstrated functional understanding.

Ask when describing the journey still requires inventing consequential product behavior. Unknown
production commitments and detailed future features remain at their actual triggers. Present the
functional model, journey/experience proposals and functional gaps in the existing final synthesis;
reuse its single confirmation gate. Do not add approval after each discovery area.

Assessment and architecture carry the confirmed functional references into ownership and decisions.
Feature intake reads the relevant model and journeys, reuses settled answers, and deepens only the
chosen outcome. Package defaults never prove that a business rule or user experience is correct.
