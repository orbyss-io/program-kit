# Backlog and delivery templates: research for design review

Research date: 2026-09-12. Status: product defaults and operating recommendations accepted in the design interview. The companion backlog-delivery-development-plan.md consolidates implementation sequencing and technical validation work. No connected customer platform was inspected or changed.

Development workflow: all phases use the single `codex/backlog-delivery` branch. Conduct a grilling interview with the user before each phase to resolve its uncertain technical decisions. This work does not use per-phase SpecKit specifications or subbranches. The development plan records the branch baseline and the separation from unrelated main-checkout work.

**Recommendation:** use a small set of native coordination fields, concise descriptions and acceptance criteria, native relationships, and revision-bound links to approved technical plans and delivery evidence. Generate an agent execution brief from these sources at the start of work. Avoid copying the complete architecture or implementation plan into every item.

The sources support these principles. They do not establish a universally optimal backlog schema or experimentally prove this exact template improves AI coordination. The template and enforcement rules below are Program Kit design recommendations to validate.

## Confirmed requirements and open boundaries

- Manage team delivery from business objectives through implementation and evidence.
- Default hierarchy: **Epic → Feature → Requirement → optional Tasks**. Business owners define epics either directly in the platform or through a Program Kit-led session using the same epic template and creation capabilities. Program Kit generates and reconciles the detail. Humans can comment, edit descriptions, and complete human-owned activities.
- Start with clean platforms and effective defaults. Define bounded GitHub and Azure DevOps profiles, with later organizational mappings. The delivery module defaults to disabled; enabling it selects and validates one authoritative backlog provider. There is no standalone local team-delivery backend in the first version. Core local architecture, roadmap, specification, plan, and task workflows remain available.
- Cloud business intent is authoritative when connected. Git owns technical specifications, architecture, plans, code, and tests.
- Detect human changes during reconciliation. A material conflict with architecture or implementation direction requires explicit intake, planning, or architecture revision. Do not silently adapt implementation or architectural decisions.
- Human owners retain business priority, staffing, delivery commitments, and business acceptance.
- Accepted Q8/Q9 models: mixed repository hosting with one delivery backlog authority, external dependency references, and evidence-based dependency gates.
- Accepted intake defaults: title, problem/outcome, and attributable owner suffice to capture an epic; guided refinement fills the remaining decision-relevant fields. Estimates are optional and team-calibrated, with assumptions; they do not create delivery commitments.
- Accepted Azure default: canonical Requirement maps to native Agile User Story. Program Kit's conceptual hierarchy retains the Requirement name.
- Accepted reconciliation operations: review one coherent change proposal per planning/revision session, then apply its approved changes without per-item approval. Routine links, evidence refresh, and justified progress updates follow configured rules; business commitments and architecture decisions retain human approval.
- Accepted work allocation: support assigned work and developer self-selection, with self-selection as the small-team default. Refresh ownership/readiness before claiming, use supported concurrency controls, preserve human accountability, and record agent execution separately. Do not silently take another person's work.
- Accepted cadence: continuous prioritization with explicit delivery milestones; iterations are optional. Milestones identify outcome, included requirements, owner, acceptance conditions, and target date where known. Humans approve commitment changes.
- Accepted outage behavior: connected authority remains on the platform. Permit local analysis, draft proposals, and bounded continuation of already claimed work against its recorded baseline, visibly stale. Defer new shared claims, commitments, and governed delivery completion until successful reconciliation. An outage never silently changes authority.
- Accepted module boundary: local snapshots, draft proposals, and execution evidence support connected operation without becoming another writable team backlog. Enabled-mode status writers and validators must respect cloud authority, with any required local delivery view explicitly derived. Disabling a connected module requires an explicit disconnect procedure that preserves history and accounts for active work and unresolved governance obligations.
- Accepted activation: support bootstrap and later enablement through the same preparation/validation workflow, without repeating onboarding. Review configuration and initial backlog changes; retain local roadmap identity/provenance when establishing provider records.
- Accepted profile ownership: consumer-controlled, versioned shared Git profile; explicit revision and repository/team bindings per repository. A single-repository consumer can keep both together. Profile upgrades are explicit and compatibility-checked across participating repositories.
- Accepted roles: business owner approves objectives, priority, scope, and commitments; technical owner approves architecture/implementation-direction revisions; acceptance owner confirms delivery. One human may fill all roles. Record person, decision, and covered revision.
- Accepted freshness boundary: synchronize at session start, claim, before implementation, between substantial execution phases, before publishing a PR/equivalent output, and before completion. Record revision/freshness and invalidate affected readiness on material change. Continuous monitoring is deferred.
- Accepted rollout: define the common contract, prove the complete Azure DevOps journey, then implement GitHub against that contract before declaring the initial capability complete. Include mixed hosting, external dependencies, parallel claims, human changes, interruption recovery, and stale evidence in acceptance.

## Evidence and what it supports

| Evidence | Supported principle | Program Kit recommendation |
|---|---|---|
| [GitHub agent task guidance](https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results) | Clear scope, problem definition, acceptance criteria, useful code context, and reproducible validation help an agent work effectively. | Requirements expose the outcome and acceptance conditions; execution briefs link the current approved plan and validation instructions. Do not invent file paths before planning. |
| [Scrum Guide: Product Owner and backlog](https://scrumguides.org/scrum-guide.html#product-owner) | Backlog management may be delegated while accountability remains with the Product Owner. Refinement progressively adds detail. | Lightweight epic intake; explicit business ownership; stronger requirements before work starts. The chosen hierarchy and readiness policy are Program Kit conventions, not Scrum mandates. |
| [INVEST and SMART, original author](https://xp123.com/invest-in-good-stories-and-smart-tasks/) | Stories should be small, valuable, testable slices; tasks describe specific contributions. | Requirements represent observable vertical outcomes. Optional tasks represent concrete outputs or handoffs. |
| [DORA: small batches](https://dora.dev/capabilities/working-in-small-batches/) | Small, independently testable batches improve feedback; oversized AI-generated changes remain a concern. | Split oversized requirements and keep implementation reviews bounded. These findings do not validate a specific field count or template wording. |
| [Cucumber: Gherkin](https://cucumber.io/docs/gherkin/reference/) | Behavioral examples distinguish context, action, and observable outcome. | Stable acceptance IDs; Given/When/Then where useful; tables or threshold statements for other criteria. Prose alone is not an executed test. |
| [DORA: test automation](https://dora.dev/capabilities/test-automation/) | Testing belongs throughout development, including validation of built and deployed software. | Link acceptance conditions to applicable tests and artifact evidence; do not create a universal final testing phase. |
| [DORA: loosely coupled teams](https://dora.dev/capabilities/loosely-coupled-teams/) | Contracts, test doubles, and independent testing reduce unnecessary coordination. | Require verification of material dependencies, but create separate integration items only for real coordination or delivery gates. |

## Where information belongs

These are proposed semantic fields. An adapter must discover native field availability, types, permissions, and workflow rules before mapping them. Required information is not synonymous with a new custom platform field.

| Information | Preferred location | Filling rule |
|---|---|---|
| Identity, kind, parent | Native item ID/type and parent relation | Persist stable identity; never match existing work by title alone. Profile maps Epic/Feature/Requirement/Task. |
| Title | Native title | Name the outcome or concrete contribution. Avoid titles such as “Backend changes.” |
| Intent, scope, exclusions | Description/body | Use the template for that level. Unknowns stay explicit; do not invent business targets. |
| Acceptance criteria | Native acceptance field where available; otherwise one named body section | Stable IDs such as AC-01, observable results, relevant failure/boundary cases. Do not maintain two authoritative copies. |
| Business owner, delivery team, assignee | Native identity/team fields where suitable; bounded custom mappings otherwise | Epic assignee can be the business owner; requirement/task assignee is the accountable execution owner. Record a separate acceptance owner when different. |
| Priority and order | Native priority plus authoritative backlog ordering | Human-owned business order; agents explain sequencing constraints and recommend changes. Severity, effort, priority, and readiness remain different concepts. |
| Estimate | Existing estimate field, optional | Team-calibrated estimate with assumptions and uncertainty. No default conversion of points into dates; no invented precision. |
| State | Native workflow state | Record actual workflow progress. A manually selected state does not establish verified readiness or delivery. |
| Readiness | Small derived field plus explanation link | Stage-specific verdict and basis: specification-ready, implementation-ready, blocked, revision required, or unknown. Exact vocabulary remains a profile design decision. |
| Iteration, target date, delivery milestone | Native scheduling fields where semantics match | Separate target/forecast from approved commitment. A shared milestone has a stable delivery-space identity; repository-local milestones may be projections. |
| Target repository and affected contracts | Structured repository reference; description/plan links for contract details | Do not infer implementation repository from the issue's location. Identify shared contract/resource conflicts before recommending parallel work. |
| Dependencies | Native relations plus a readable condition record | Prerequisite, blocked transition, satisfaction condition, owner, and evidence. Labels are not dependency edges. |
| Technical authority | Links to versioned spec, plan, ADRs and shared Definition of Done | Technical choices remain in governed repository artifacts. Show their approval/revision status. |
| Evidence | PR/build/test/release links plus artifact and acceptance IDs | Record what was checked, against which versions, and the result. A closed item or checked box is not sufficient proof. |
| Discussion | Native comments/history | Preserve human contributions; distinguish questions and proposals from accepted requirement changes. |
| Reconciliation bookkeeping | Generated record with a visible audit link | Source revisions, last observed content, approved baseline, actor, classified changes, decisions, and operation identity. Storage is a later design decision; it must not become an alternative business backlog. |

Prefer a few extra scalar fields, initially candidates such as Readiness, Delivery milestone, Target repository, and a separate acceptance owner where needed. Add fields only when necessary for filtering, validation, or clear ownership. Keep detailed dependency conditions and evidence in structured records with readable views rather than dozens of flat fields.

## Templates by hierarchy level

The following are original proposed templates, not vendor templates. Field names in bold identify native fields or logical sections; adapters choose the actual form placement. Display native parent, owner, status, and priority beside the description rather than requiring users to repeat them in prose.

### Epic: business objective and boundaries

**Title:** `<Business outcome for a named group>`

**Description:**

```text
Problem / opportunity
Who experiences what problem, and why it matters now.

Desired outcome
What should change for those people or the business.

Success measures
Measure | current baseline | target | measurement source | review window
Mark unknown values explicitly; identify who will resolve them.

Scope and exclusions
Included outcomes; explicit exclusions; fixed business constraints.

Timing and rationale
Any genuine deadline, its reason, and whether it is a target or commitment.

Open questions
Unresolved decisions and accountable decision owners.
```

At creation, require title, problem/outcome, and an attributable business owner. Other fields can be clarified during intake. Before accepting a delivery plan, establish success evidence and resolve the uncertainties that affect commitments. Completing all features does not automatically establish that the business outcome occurred.

### Feature: coherent capability contributing to the epic

**Title:** `<Capability and benefit>`

**Description:**

```text
Capability and contribution
What capability this provides and how it contributes to the epic outcome.

Covered journeys and boundaries
Actors, situations, included behavior, and exclusions.

Acceptance of the capability
Observable results across the participating requirements.

Affected systems and constraints
Repositories/teams involved; relevant approved architecture references.

Dependencies and open decisions
External prerequisites or decisions that affect decomposition or delivery.
```

Use native child relations for requirements. Do not copy child status tables into this description. Feature acceptance should describe the combined capability without repeating every requirement criterion.

### Requirement: primary unit of verifiable delivery

**Title:** `<Actor/system can achieve an observable outcome>`

**Description:**

```text
Outcome and context
Actor or trigger, present problem, expected outcome, and business reason.

Scope
Included behavior and explicit exclusions.

Constraints and approved references
Business constraints; links to the current approved spec, plan, and relevant ADRs.
Identify unresolved questions instead of silently making architecture choices.

Coordination
Target repository/team; affected public contracts or shared resources.
Dependency: prerequisite | blocked transition | satisfaction condition | owner.

Verification obligations
Acceptance ID | verification method/suite | environment/data | evidence owner.
Identify material integration obligations and whether a separate task is needed.
```

**Acceptance criteria:**

```text
AC-01: Given <context>, when <action>, then <observable result>.
AC-02: Given <material failure/boundary>, when <action>, then <safe result>.
AC-03: Under <stated conditions>, <quality measure> meets <agreed threshold>.
```

Only include criteria relevant to the outcome. Link shared quality rules instead of repeating a generic security/performance checklist. A requirement may contain several criteria, but should still form a reviewable vertical slice. Split it when ownership or size prevents that.

**Delivery evidence:** generated links from acceptance IDs to results, tested artifact versions, PRs, required delivery destination, and acceptance decision. Keep this separate from the requested acceptance criteria.

### Optional Task: concrete contribution or handoff

**Title:** `<Action and specific output>`

**Description:**

```text
Contribution
Which parent requirement and acceptance/verification obligation this satisfies.

Output and boundaries
Concrete artifact, decision, manual action, or bounded implementation contribution.

Prerequisites and handoff
What must be available; what this unblocks; who receives the output.

Completion check
Evidence or observable result required; approved plan reference if implementing.
```

Create a task for a separately owned contribution, real dependency gate, human action, investigation, or useful bounded implementation activity. Routine coding checklists can stay in the approved plan. An investigation task should identify the decision/output and its agreed bound; it must not quietly authorize implementation.

## Worked requirement example

Illustrative only; these are invented product details to demonstrate the template.

- **Epic:** Reduce failed checkout recovery effort.
- **Feature:** Recover safely from payment-provider timeouts.
- **Requirement title:** A shopper can retry an uncertain payment without a duplicate charge.
- **Outcome:** The shopper can determine and complete the original payment attempt after a network timeout.
- **Scope:** Existing card-payment flow. Excludes a new provider and refund redesign.
- **AC-01:** Given a payment attempt whose response timed out, when the shopper retries that attempt, the system reconciles or reuses the original attempt and does not create a second charge.
- **AC-02:** Given the provider still cannot establish the result, the shopper receives an explicit pending state and no false success confirmation.
- **AC-03:** Another shopper cannot inspect or resume the payment attempt.
- **Approved references:** Link the actual approved payment-recovery specification, authorization rules, and provider contract. Populate identifiers during planning; do not invent ADRs.
- **Coordination:** An accepted provider contract permits consumer implementation and contract-test preparation in parallel. Verification against the required provider artifact is a separate delivery condition.
- **Optional task:** Verify timeout/retry behavior against the required provider version, with named evidence owner and test-result links.

The requirement states business behavior. The approved plan decides the mechanism for correlating attempts, persistence, retries, and API details. A later business request to support multiple simultaneous payment attempts can invalidate that plan and requires explicit impact assessment.

## Provider mapping recommendations

**Accepted Azure DevOps default: Agile, with canonical Requirement mapped to native User Story.** Agile already supplies Epic/Feature/User Story/Task. Scrum uses Product Backlog Item, and CMMI uses Requirement. Choosing CMMI solely for the label is not a sufficient reason to adopt its broader process. Existing organizations can supply a different supported mapping through their profile. [Microsoft process comparison](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/choose-process?view=azure-devops), [portfolio hierarchy](https://learn.microsoft.com/en-us/azure/devops/boards/backlogs/define-features-epics?view=azure-devops).

Microsoft explicitly treats User Story as the Agile representation of a requirement. Its Agile guidance also distinguishes implementation resolution from product-owner acceptance. These are stronger reasons for the default than matching a display name. [Requirements management](https://learn.microsoft.com/en-us/azure/devops/cross-service/manage-requirements?tabs=agile-process&view=azure-devops), [Agile workflow](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process-workflow?view=azure-devops).

| Canonical content | Azure candidate mapping | GitHub candidate mapping |
|---|---|---|
| Kind and hierarchy | Work Item Type; Parent/Child relations | Organization issue types; parent/sub-issues; validate permitted type relationships |
| Title and narrative | `System.Title`; `System.Description` | Issue title; named Markdown body sections |
| Acceptance | `Microsoft.VSTS.Common.AcceptanceCriteria` where present; otherwise one designated description section | Named Acceptance criteria section in body |
| Accountable executor | `System.AssignedTo`; team mapping through Area Path where configured | Designated human assignee; separate team mapping when needed |
| Workflow progress | `System.State` and mapped state category | Authoritative Project Status plus issue state/close reason mapping |
| Priority and order | Native Priority; backlog order | One authoritative priority field and delivery Project ordering |
| Estimate | Story Points for Agile requirements; relevant task estimate fields only if used | Configured effort field, with explicit unit/scale |
| Iteration and dates | Iteration Path and supported target fields | Project iteration/date fields as configured |
| Blockers | Predecessor/Successor between appropriately bounded items | Native blocking/blocked-by relations |
| Evidence and external references | Artifact links; hyperlinks when native links unavailable | PR/issue relationships and evidence URLs |

Azure field reference names and rich-text support are documented in [Microsoft's field reference](https://learn.microsoft.com/en-us/azure/devops/boards/queries/titles-ids-descriptions?view=azure-devops). Native field applicability differs by work item type/process; intake must verify it. Apply needed custom fields through an isolated inherited process, with scope disclosed before installation. [Inherited-process model](https://learn.microsoft.com/en-us/azure/devops/organizations/settings/work/inheritance-process-model?view=azure-devops).

Azure inherited rules can require acceptance criteria upon entering Active. Use such rules for supported field checks, with Program Kit validating semantic completeness and dependency evidence. A nonempty field is not proof of a sound requirement. [Custom rules](https://learn.microsoft.com/en-us/azure/devops/organizations/settings/work/custom-rules?view=azure-devops).

GitHub supports [organization issue types](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-types-in-an-organization) and [sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues). For clean organizations, propose Epic, Feature, Requirement, and Task types. An issue's repository is not automatically the implementation target.

GitHub distinguishes organization-level issue fields from Project-specific fields. A value held on the issue can be reused across Projects; Project values can differ. Select one authoritative location for each concept and avoid duplicate Priority fields. Issue-field visibility also matters for public repositories. [GitHub issue fields](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization).

Prefer organization issue fields for intrinsic shared metadata where supported and appropriate; use the authoritative delivery Project for planning-specific metadata. Keep a Project-field fallback for unavailable capabilities. Confirm the actual cloud/server edition and API support rather than relying on static feature assumptions.

GitHub organization fields do not cover another organization's issues, draft items, or PRs. Preserve provider identity separately from Project-item identity; use persisted global IDs and field/option IDs where supplied. [Issue fields in Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-issue-fields), [global node IDs](https://docs.github.com/en/graphql/guides/using-global-node-ids).

Capability caveat: GitHub's May 2026 announcement describes organization issue fields as public preview; August announced generally available multi-select support while some reference documentation still lists fewer field types. Issue forms are also marked preview. Treat preview policy and deployed capabilities as intake inputs; do not assume GitHub Server parity or base essential coordination on an unverified feature. [May field announcement](https://github.blog/changelog/2026-05-21-issue-fields-are-now-in-public-preview-for-all-organizations/), [August update](https://github.blog/changelog/2026-08-07-connecting-issues-and-multi-select-field-support/).

Use an Epic creation form for business users and the same semantic contract for agent-created items. GitHub form responses become editable Markdown; a form does not enforce ongoing semantic correctness or populate arbitrary planning fields by itself. Reconciliation and API-created items must run the same validators. [GitHub issue-form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms).

## Strict reconciliation and execution context

Recommended sequence:

1. Read current platform revisions and changed comments/fields; compare with the prior observation and accepted baseline.
2. Record every detected human edit and classify its effect. Cosmetic edits need an audit classification, not a full architecture intake. Ambiguous semantic changes require clarification.
3. Identify affected requirements, dependencies, plans, acceptance evidence, and active work. Mark affected readiness as revision required when the approved basis is no longer valid.
4. Route business ambiguity to intake/refinement, implementation-direction changes to planning, and architecture-significant changes to architecture/ADR review. These may be one coordinated revision session.
5. Propose the linked changes to requirements, documents, and work items. A platform edit alone cannot ratify a new architecture decision. Preserve superseded decisions and work history.
6. After the relevant human decisions and validations, publish a new accepted baseline and refresh affected readiness. Keep unrelated work eligible where the impact assessment supports that conclusion.

Session-driven synchronization cannot promise instant detection between observations. Record the freshness of a verdict and recheck at the accepted checkpoints: session start, claim, before implementation, between substantial execution phases, before publishing a PR/equivalent output, and before completion. Deleted/inaccessible records, incomplete history, and unavailable providers must produce explicit uncertainty, not an assumed clean baseline. Continuous monitoring is deferred; reliable observation and history-gap handling remain implementation responsibilities.

This is a real agent-context concern: GitHub documents that an issue-assigned Copilot session receives existing issue content but does not automatically receive later issue comments. That behavior is specific to that workflow, not every coding agent. Program Kit must explicitly manage context refresh rather than assume all workers see changes. [GitHub agent assignment behavior](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github).

Generate a compact execution brief containing item identity, accepted business revision, current spec/plan/ADR references, target repository/base, scope, acceptance IDs, dependencies, shared-contract constraints, validation instructions, and required completion evidence. A worker reports findings against that basis. Runtime session identity belongs in execution records; human accountability remains visible on the backlog.

## How to establish a proven default

Start with deterministic template/schema/adapter tests and sandbox platform exercises that create no paid coding-agent sessions. Test missing fields, ambiguous acceptance, orphaned items, dependency cycles, changed requirements, stale evidence, duplicate claims, partial writes, and repeated reconciliation without duplication. Platform writes require their own explicit test scope.

Use the proposed mixed-hosting scenario to compare the templates with an ordinary prose-only backlog. Have reviewers assess whether they can identify the outcome, owner, ready parallel work, blocking condition, and delivery evidence without reading an entire repository. Measure missed changes, lost human edits, duplicate work, unnecessary blocks, review corrections, and unsupported completion claims. Do not optimize for item count, story points produced, or volume of generated documentation.

Any later live coding-agent evaluation is separately user-invoked and governed by the repository's live-acceptance rules. No such run is authorized or started by this research.

The product decision frontier is settled. Phase interviews will resolve technical choices with the user, supported by investigation of provider concurrency and recovery guarantees, compatible reconciliation-record storage and adapter transports, and precise schemas and validation rules. These are bounded engineering investigations in the companion development plan, not assumed existing capabilities. The label “proven” remains reserved for demonstrated acceptance results.
