# Conversational bootstrap intake

## Outcome

Produce a user-confirmed project intent, a canonical C4-aligned architecture map, a reviewable
Structurizr DSL projection, and a validated bootstrap intake contract. Intake is complete when every
bootstrap-relevant uncertainty is answered, defaulted, assigned, or deferred; it does not require
every future product decision to be made.

Keep the intake proportional to the request. Do not inventory the repository or implementation
internals to compensate for an already complete description. At authoring time use
[intake-artifacts.md](intake-artifacts.md) instead of opening schemas or validator source.

## Question policy

Begin with the user's natural description. Reflect the understood intent before asking questions.
Use the round and answer-handling contract in the shipped Program Kit grilling command loaded by
the front-door skill. This reference defines which branches matter to intake, not a second
interview algorithm. Do not run a fixed questionnaire or ask about excluded capability categories.

Prioritize observable value, actors, scope, domain language and invariants, trust and data
boundaries, external integrations, operational constraints, material Program Kit deviations, and
the thinnest meaningful proving journey. Preserve every named source journey independently.

Apply a clearly applicable Program Kit default automatically when user intent neither contradicts
it nor leaves its applicability ambiguous. Do not ask users to select or re-approve obvious tools,
packages, versions, or profiles. Record the default's source, rationale, and material consequences
for the final synthesis, where the user can revisit it. Technical importance alone is not a reason
to spend an interview question on an unambiguous default.

Ask when intent is unclear, conflicts with a default, or leaves materially different candidates
plausible. Clarify the product need first, then derive the technical consequence where evidence
permits. Explain alternatives and consequences when an actual user choice remains. Preserve an
explicit consumer package or provider choice, including non-Orbyss packages; assess its role and
compatibility without silently replacing it with a managed default. Look up technical facts;
ask the user about constraints, intent, and acceptable trade-offs.

For a need with no declared Program Kit capability, say exactly that; do not claim incompatibility.
Classify it as external, research-required, or project-owned design and ask only for information the
project must supply. Defer questions that become material only at a named lifecycle trigger.

Completion accounts for every bootstrap-relevant branch, not every future implementation choice.
Business outcomes, semantic ownership, and architecture-significant trust, data, or consistency
boundaries need enough evidence now to prepare a coherent map and founding candidates. Feature
fields, detailed business rules, and implementation choices can remain assigned to the first
feature specification when they do not change those boundaries. Record the closing artifact or
owner/next action and trigger. Unanswered human decisions that block intake remain open; assigning
them to someone does not make the intake ready to confirm.

## Conversation evidence and final review

Maintain a compact record in `project-intent.md` during the interview: stable Q IDs, prerequisite
IDs, answers or pending state, recommendations accepted, rationale, source evidence, and any
superseding correction. Retain the user's meaning without copying the entire conversation. Reuse
this record on re-entry and reopen only affected branches when intent changes. Do not replace a
previously confirmed artifact merely to log a new answer; follow the re-analysis procedure below
and stage revisions for review first.

Keep explicit answers, Program Kit defaults, derived conclusions, and architectural proposals
distinct in the synthesis and JSON evidence. Accepting recommendations does not turn applied
defaults into explicit user intent or turn founding candidates into Accepted ADRs.

Once the interview converges, author and validate the four draft artifacts. Present one final
review covering the product intent, journeys, domain and context analysis, founding candidates and
alternatives, applied defaults, and assigned/deferred items. Explain that defaults can be revised
here. This review also satisfies grilling's shared-understanding gate. Confirmation attests to the
accuracy of the provisional intake; the later architecture approval remains separate.

## Architecture map

The Program Kit JSON map is canonical. It preserves the portable semantics needed for C4 and
Structurizr models: static, dynamic, deployment, filtered, custom and image views; deployment
elements and instances; groups, archetypes, properties, perspectives and URLs; view filters,
ordering, layout and animation; styles, themes, terminology and branding; documentation; and
hash-bound architecture decisions. Features not yet understood by a registered importer remain
typed extensions rather than being discarded.

Its C4 System Context view contains only the system in scope, people, and directly connected external
systems. Strategic custom views show the classified domain/subdomain landscape, bounded contexts,
owned modules and bridges, and a typed Context Map. One dynamic view preserves each named journey in
source order. Do not represent a bounded context or capability as a peer software system, and do not
invent container/component/deployment views until evidence supports those C4 levels.

Classify subdomains as Core, Supporting, or Generic from evidence. Derive candidate bounded contexts
from differences in model, ubiquitous language, ownership, lifecycle, and consistency—not nouns,
screens, or cross-cutting concerns. Each context records responsibilities, non-responsibilities,
language, data, invariants, lifecycle, rationale, and split triggers. Every cross-context dependency
records direction, Context Map patterns, interaction mode, owned contract, translation/ACL bridge,
data owner, consistency owner, failure owner, and atomicity. Every module belongs to one context.

Keep Program Kit mechanism coverage separate from the consumer semantic profile, provider choice,
and adapter/integration ownership. Managed Forms mechanisms never absorb consumer-owned item,
pricing, VAT, quantification, publication, or workflow meaning.

Founding decision candidates accompany the map with a question, recommendation, alternatives,
trade-offs, evidence, confidence, and affected map IDs. They stay `proposed` or `unresolved` during
intake. Confirmation attests that the provisional synthesis is accurate; it does not create or
accept ADRs. The architecture phase uses the candidates to narrow research, creates real Proposed
ADRs, and submits the exact founding ADR bundle at the existing post-architecture approval pause.

Every architecture decision records its ID, repository-relative path, SHA-256, title, date, status,
scope, owner and supersession links. Elements, relationships, views and constraints carry typed
`decision_refs`. Reject missing decisions, stale hashes, broken supersession chains, and accepted
architecture facts governed only by a non-Accepted decision. Export attached decisions with
Structurizr `!adrs` while retaining the provider-neutral canonical links.

Generate `docs/architecture/workspace.dsl` as the review projection. Treat it as importable user
input when its recorded hash changes. Import through `scripts/architecture_map.py`; never implement
ad hoc parsing inside the skill. Unsupported DSL must produce a diagnostic and leave the canonical
map unchanged. Preserve unrecognized portable statements as extensions. Classify `!script`,
`!plugin`, remote includes, remote images and remote themes as `blocked-executable`; importing or
rendering never executes or fetches them without a separate explicit policy decision and
authorization.

## Re-analysis

On every invocation, inspect the canonical artifact paths and compare their current hashes with
`docs/architecture/bootstrap-intake.json`. When nothing changed, continue the unfinished questions
or summarize the confirmed intake. When an artifact changed:

1. validate or import the changed artifact;
2. identify affected elements, relationships, capability assessments, open items, and slice signals;
3. mark only affected derived conclusions stale;
4. preserve unaffected explicit answers;
5. surface conflicts instead of choosing a winner;
6. reopen only affected questions; and
7. regenerate and reconfirm all bound artifacts.

A changed projection never silently supersedes an explicit user decision or confirmed Program Kit
default. The user must resolve the conflict.

## Completion command

After confirmation and deterministic validation, output exactly one physical command line in its own
fenced block. Use repository-relative forward-slash paths, double-quote each `name=value` argument,
fully substitute every value, and include no placeholders, backticks, backslashes, environment
variables, command substitutions, or shell-specific operators:

`specify workflow run program-kit-bootstrap --input "bootstrap_intake=docs/architecture/bootstrap-intake.json" --input "integration=auto"`

Do not run the outer workflow from an agent. Do not append automatic approval unless the user
explicitly requests it.
