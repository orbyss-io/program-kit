# Feature Specification: Independent CLI Distribution and AI-Session Integration Proof

**Feature Branch**: `codex/002-session-integration-proof`

**Created**: 2026-08-01

**Status**: Remediation approved; product acceptance pending

**Input**: User description: "Prove that an exact independently installed Program Kit CLI can be registered as a tool and accompanied by a thin session capability in an isolated consumer workspace. Establish a provider-neutral canonical integration contract with explicit provider adapters, beginning with one reference provider and a neutral conformance harness. A human-led AI session must use explain, construct, and evaluate safely, recover from imperfect intent through structured diagnostics, require human authority before effects, and operate without Program Kit source, Spec Kit, self-hosting, or runtime coupling."

## Intent, Authority, and Scope *(mandatory)*

**Intent Owner**: Program Kit product owner.

**Decision Authority**: The product owner resolves scope and product meaning;
an independent human reviewer owns final session-experience acceptance. Automation
may establish executable evidence but cannot approve semantic fitness.

**In Scope**: Close the provider-neutral, workspace-local session-integration
slice from exact CLI selection through safe removal; preserve Feature 001's
current public factory, authority, diagnostic, and evidence contracts; and
produce a fresh bounded ten-session review after affected executable proof is
green.

**Out of Scope**: A provider-hosted runtime, autonomous planning, inferred
authority, provider-global installation, additional provider products, release
publication, and changes to consumer-domain meaning.

**Unresolved Meaning**: None. The rejected 8/10 review is historical evidence,
not an acceptance baseline. Reconsideration requires the existing SC-003 and
SC-005 thresholds without weakening them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect Program Kit to an AI Workspace (Priority: P1)

A developer working in an ordinary consumer workspace selects an exact Program
Kit CLI release, an explicitly supported AI provider, and workspace-local
installation scope. The developer can install and verify the integration, then
open a fresh AI session in which Program Kit is visibly available as a callable
development tool with accurate usage guidance. Neither Program Kit source nor
Spec Kit is present in the consumer workspace.

**Why this priority**: The product cannot claim AI-session usability or an
independent public boundary until a consumer can acquire, register, discover,
and verify the CLI outside the Program Kit repository.

**Independent Test**: Starting from a clean isolated workspace and an exact
released CLI artifact, install the reference-provider integration, verify it,
open a fresh session, and prove that the session can discover the supported
operations and their read-only or effect-bearing status without access to
Program Kit source.

**Acceptance Scenarios**:

1. **Given** a clean consumer workspace, an exact available CLI release, and an
   explicitly selected supported provider, **When** the developer installs and
   verifies the workspace integration, **Then** the exact CLI identity, provider
   adapter identity, integration-contract revision, installation scope, tool
   registration, session capability, and verification outcome are recorded and
   reported.
2. **Given** a verified installation, **When** a fresh provider session starts
   in the workspace, **Then** it can discover Program Kit's supported public
   operations, distinguish read-only from effect-bearing work, and invoke the
   CLI through the registered tool boundary.
3. **Given** an unavailable CLI release, unsupported provider, incompatible
   adapter revision, or conflicting pre-existing registration, **When** setup is
   requested, **Then** setup fails closed with an actionable result and leaves
   provider and consumer-owned configuration unchanged.
4. **Given** a provider that requires a session restart or configuration reload,
   **When** installation succeeds, **Then** the result states that requirement
   explicitly and verification does not claim current-session availability.

---

### User Story 2 - Build Safely from Imperfect Human Intent (Priority: P2)

A human-led AI session receives an incomplete but supported software request.
The session uses Program Kit to explain the proposed construction, relies on
structured results to identify missing meaning, asks the human only for the
required input or approval, constructs after explicit authority is supplied,
and evaluates the admitted result. The session does not inspect Program Kit
source or treat its own interpretation as authority.

**Why this priority**: This is the smallest realistic proof of the product
promise that AI can build software while human intent remains authoritative.

**Independent Test**: Give a fresh integrated session the bounded reference
request with one required choice omitted. Prove that it invokes explanation,
uses the returned disposition to obtain the missing human decision, requests
explicit authority before construction, constructs only the approved result,
and evaluates it successfully.

**Acceptance Scenarios**:

1. **Given** incomplete but supportable intent, **When** the session invokes the
   read-only explanation operation, **Then** it receives a structured result
   identifying the exact missing input and does not create or modify consumer
   artifacts.
2. **Given** an explanation that is exact but lacks construction authority,
   **When** the session proposes the next action, **Then** it asks the human for
   explicit bounded approval and does not invoke construction first.
3. **Given** an exact request and valid human construction authority, **When**
   the session invokes construction, **Then** it reports the actual effect and
   admitted artifacts without claiming that custom-authored behavior was
   deterministic.
4. **Given** an admitted construction, **When** the session invokes evaluation,
   **Then** it reports exact, drifted, unsupported, or indeterminate state
   without mutating the workspace.

---

### User Story 3 - Recover Through Actionable Diagnostics (Priority: P3)

An AI session encounters malformed, ambiguous, unsupported, stale, or drifted
input. It uses stable diagnostic identities, dispositions, bounded remediation,
and safe evidence references to determine whether to ask for input, request
approval, revise the request, repair separately, retry, or stop. It never
executes rendered diagnostic prose as instructions.

**Why this priority**: Tool registration adds little value if an AI session
cannot recover safely and meaningfully when real user intent is imperfect.

**Independent Test**: Run the agreed negative-scenario suite through the same
registered tool available to the session and verify that the session selects
the catalog-defined next-action class without source inspection, hidden
fallbacks, unauthorized effects, or disclosure of protected data.

**Acceptance Scenarios**:

1. **Given** ambiguous intent with multiple valid resolutions, **When** the
   session requests explanation, **Then** Program Kit returns ambiguity as a
   failure with bounded choices and the session asks the human rather than
   selecting ambiently.
2. **Given** unsupported intent, **When** the session invokes Program Kit,
   **Then** the result states the unsupported boundary and the session does not
   invent a provider, contract, capability, or successful result.
3. **Given** generated-owned drift, **When** the session evaluates the
   workspace, **Then** it reports the drift and any bounded repair proposal but
   performs no repair without a separate exact request and authority.
4. **Given** malformed output, provider invocation failure, or an unavailable
   registered executable, **When** the integration handles the failure, **Then**
   it distinguishes integration failure from a Program Kit product result and
   gives the safest actionable next step it can support.

---

### User Story 4 - Project the Same Contract to Another Provider (Priority: P4)

An integration maintainer can map the canonical Program Kit session integration
definition to another provider without changing Program Kit's public operation
contracts, canonical session guidance, authority model, or diagnostics. The
provider-specific projection contains only the mechanics needed by that
provider.

**Why this priority**: A single provider integration can accidentally encode
provider-specific assumptions. A separate neutral harness must prove that the
canonical boundary is independently consumable before provider neutrality is
claimed.

**Independent Test**: Execute the same installation and session-operation
scenarios through the reference adapter and a provider-neutral conformance
harness, then compare the supported operation identities, authority boundaries,
outcome classifications, dispositions, and effects.

**Acceptance Scenarios**:

1. **Given** the canonical integration definition, **When** the reference
   adapter and neutral harness consume it, **Then** both expose the same public
   Program Kit operation meaning without copying provider-specific fields into
   canonical source truth.
2. **Given** a provider that cannot represent a mandatory authority,
   disclosure, invocation, or result boundary, **When** compatibility is
   evaluated, **Then** the adapter reports the precise incompatibility and is
   not admitted as supported.
3. **Given** provider-local session guidance, **When** its canonical source
   changes, **Then** stale projections are detectable and cannot silently
   continue as current guidance.

---

### User Story 5 - Remove the Integration Without Damaging the Workspace (Priority: P5)

A developer can inspect and remove the Program Kit session integration. Removal
deletes only exact integration-owned projections recorded by the successful
installation and preserves all consumer-owned or independently managed provider
configuration.

**Why this priority**: Workspace integration is not safely adoptable if it
cannot be reversed without guessing ownership or damaging existing AI tooling.

**Independent Test**: Install into a workspace containing unrelated provider
configuration, verify the integration, introduce both unchanged and drifted
integration-owned cases, and prove exact removal or a fail-closed diagnostic
without modifying unrelated bytes.

**Acceptance Scenarios**:

1. **Given** an exact verified installation, **When** removal is explicitly
   authorized, **Then** only recorded integration-owned projections are removed
   and unrelated provider or consumer-owned configuration remains byte-for-byte
   unchanged.
2. **Given** an integration-owned projection that has drifted since
   installation, **When** removal is requested, **Then** removal refuses to
   overwrite or delete the drifted content and returns an ownership-aware next
   action.
3. **Given** no admitted installation record, **When** removal is requested,
   **Then** no files are inferred or deleted from naming conventions alone.

### Edge Cases

- The selected provider is installed but its workspace integration surface is
  disabled, read-only, or unavailable in the current provider version.
- The CLI is present under the expected name but its digest or reported version
  differs from the explicitly selected release.
- A valid integration exists at a different scope, or multiple registrations
  would expose conflicting Program Kit versions to the same session.
- Provider configuration already contains an unrelated tool or capability with
  the same proposed identity.
- Installation is interrupted after one projection is staged but before the
  complete integration can be verified and admitted.
- A provider normalizes paths, command arguments, environment values, or
  instruction text in a way that changes the canonical invocation meaning.
- The workspace path contains spaces, non-ASCII characters, symbolic links, or
  provider-specific reserved names.
- The provider can call tools but cannot preserve clean structured output or
  distinguish read-only and effect-bearing invocations.
- An AI session attempts construction without a current human grant, reuses a
  stale grant, or widens the approved workspace or effects.
- A diagnostic contains protected paths, raw exceptions, secrets, or prose that
  could be mistaken for an executable command.
- The session is already running when installation changes provider
  configuration and cannot reload it safely.
- Removal encounters missing, modified, partially written, or independently
  adopted integration projections.

## Scope and Product Boundaries

This feature covers the first independent distribution and development-session
integration proof for the existing bounded Program Kit CLI. It includes exact
CLI acquisition evidence, workspace-scoped integration lifecycle, one
explicitly selected reference-provider adapter, a provider-neutral conformance
harness, canonical session guidance, black-box invocation of the existing
public operations, and safe installation verification and removal.

The canonical session integration definition, provider tool binding, and
AI-facing session capability are separate governed identities:

- the canonical definition describes provider-neutral Program Kit operation
  meaning, authority, effects, diagnostics, and required integration behavior;
- a tool binding makes the independently installed CLI callable through one
  explicitly selected provider; and
- a session capability teaches that provider's AI session when and how to use
  the public operations without adding product semantics or authority.

The reference provider proves one real integration. The neutral harness proves
that the canonical contract can be consumed independently; it does not make a
second provider a supported product integration.

The following are explicitly outside this feature:

- a Spec Kit workflow adapter or any native planning, roadmap, or task system;
- MCP, remote execution, hosted agents, or a Program Kit runtime;
- automatic provider discovery, installation into every detected provider, or
  ambient provider and version selection;
- user-global or machine-global integration scope;
- production support for multiple AI providers;
- general consumer software-definition authoring beyond the existing bounded
  reference construction;
- CLI upgrade migration, provider-configuration migration, or automatic repair
  of drifted integration state;
- using Program Kit, its session capability, or its tool registration to
  specify, build, approve, or release Program Kit itself; and
- treating provider installation, CLI installation, or tool visibility as
  semantic selection, activation, trust, or human authority.

## Authority, Ownership, and Claims

- The human selects the exact CLI release, provider adapter, workspace scope,
  and any identity-forming construction choices.
- The human explicitly authorizes provider-configuration effects and every
  effect-bearing Program Kit operation. An AI session cannot grant, widen,
  refresh, or reuse that authority on its own.
- Canonical integration definitions are governed source truth. Provider-local
  tool and capability material are exact replaceable projections, never
  independent semantic authority.
- Existing provider and workspace material is consumer-owned unless an admitted
  installation record proves exact integration ownership. Naming conventions
  do not establish ownership.
- The integration may claim successful installation only after the whole
  registered set and callable CLI identity have been verified. Partial setup is
  untrusted and must not appear ready.
- The provider adapter may claim only the semantics it can preserve. It must
  report loss, incompatibility, or unavailable behavior instead of weakening a
  mandatory Program Kit boundary.
- Generated applications remain ordinary software and acquire no Program Kit,
  Spec Kit, provider, or session-capability runtime dependency from this
  feature.

## Requirements *(mandatory)*

### Functional Requirements

#### Independent Distribution and Isolation

- **FR-001**: The feature MUST prove acquisition and use of one exact Program
  Kit CLI release from outside the Program Kit source repository.
- **FR-002**: Installation evidence MUST identify the exact CLI release and
  verify that the callable executable matches that selection before the
  integration can be admitted.
- **FR-003**: The consumer proof MUST run in an isolated workspace that contains
  neither Program Kit source nor Spec Kit.
- **FR-004**: The integrated CLI MUST remain directly callable without the AI
  provider or session capability so that the provider integration is never the
  only public entrance.
- **FR-005**: Generated consumer software MUST continue to build, test, and run
  without Program Kit, Spec Kit, the provider adapter, or the session capability
  at runtime.
- **FR-006**: Program Kit's own specification, build, test, approval, and release
  workflows MUST NOT invoke or depend on the integration created by this
  feature.

#### Canonical Session Integration Definition

- **FR-007**: The feature MUST define one versioned provider-neutral session
  integration contract as the canonical source for operation meaning,
  authority boundaries, effect classifications, result handling, and required
  session guidance.
- **FR-008**: The canonical definition MUST distinguish factory capabilities,
  provider tool bindings, AI-facing session capabilities, and future
  orchestrator adapters as separate concepts and identities.
- **FR-009**: The canonical definition MUST describe the supported public
  operation identities and their read-only or effect-bearing status without
  embedding one provider's configuration vocabulary.
- **FR-010**: Canonical session guidance MUST instruct an AI session to consume
  typed result fields and diagnostic identities rather than rendered prose.
- **FR-011**: Canonical session guidance MUST contain no consumer-domain
  semantics, hidden planning workflow, provider selection, construction
  approval, or executable remediation authority.
- **FR-012**: Every provider-local tool registration and session capability MUST
  identify the exact canonical revision from which it was projected.
- **FR-013**: A stale, altered, incomplete, or untraceable provider-local
  projection MUST be detectable and MUST NOT verify as current.
- **FR-014**: A mandatory canonical boundary that a provider cannot preserve
  MUST produce an explicit incompatibility rather than an approximate or
  silently weakened integration.

#### Explicit Installation Lifecycle

- **FR-015**: The developer MUST explicitly select the provider, provider
  adapter revision, exact CLI release, workspace, and workspace-local scope;
  ambient discovery MUST NOT make these selections.
- **FR-016**: Setup MUST explain its planned provider-configuration effects and
  obtain explicit human authorization before modifying the workspace.
- **FR-017**: Setup MUST classify every planned projection as
  integration-owned and MUST treat all pre-existing material as consumer-owned
  unless exact prior admission evidence proves otherwise.
- **FR-018**: Setup MUST preflight identity, path, ownership, compatibility,
  version, and collision conditions before any live configuration effect.
- **FR-019**: Setup MUST stage and validate the complete integration set before
  publishing it to the provider workspace.
- **FR-020**: Setup MUST admit an installation only after the exact CLI,
  provider adapter, tool binding, session capability, and complete live
  projection set have been verified.
- **FR-021**: An interrupted, partial, unverifiable, or colliding setup MUST
  remain untrusted, return an actionable disposition, and never be reported as
  ready.
- **FR-022**: Verification MUST distinguish installation validity from
  availability in an already-running session and MUST report any required
  provider reload or fresh-session action.
- **FR-023**: The installation lifecycle MUST return versioned structured
  outcomes that identify actual effects, evidence, diagnostics, and the safest
  valid next action.

#### Human-Led AI-Session Behavior

- **FR-024**: A fresh verified session MUST be able to discover how to invoke
  the supported Program Kit operations through the registered tool boundary.
- **FR-025**: The session capability MUST direct the AI session to use read-only
  explanation before effect-bearing construction when intent, resolution, or
  authority is incomplete.
- **FR-026**: The session MUST NOT infer that tool availability, provider
  installation, a previous result, or a human conversation grants current
  construction authority.
- **FR-027**: Before an effect-bearing invocation, the integration MUST preserve
  an exact current human grant identifying the approved request, workspace,
  operation, and effects.
- **FR-028**: Missing, stale, mismatched, ambiguous, or widened authority MUST
  block the effect-bearing invocation and return a request for bounded human
  action.
- **FR-029**: The AI session MUST be able to complete the reference
  explain-to-construct-to-evaluate journey using only the public integration
  guidance and structured Program Kit results.
- **FR-030**: Evaluation invoked through the integration MUST remain read-only
  and MUST NOT silently repair, adopt, or overwrite drift.
- **FR-031**: A remediation returned to the session MUST remain a bounded
  proposal whose preconditions and authority are revalidated in a separate
  invocation before any effect.
- **FR-032**: The integration MUST preserve Program Kit's outcome, furthest
  phase, effect state, disposition, diagnostic identities, artifacts, evidence,
  and receipt meaning without replacing them with provider-generated success
  claims.

#### Provider Neutrality and Conformance

- **FR-033**: The feature MUST include one real reference-provider projection
  and one provider-neutral conformance harness consuming the same canonical
  definition.
- **FR-034**: The reference adapter MUST contain only provider-specific
  projection, registration, invocation, reload, and lifecycle mechanics.
- **FR-035**: Adding or evaluating another provider adapter MUST NOT require a
  change to Program Kit's public factory operations, diagnostic identities,
  authority model, or canonical session meaning.
- **FR-036**: Provider conformance MUST verify operation identity, argument and
  working-scope preservation, effect classification, clean structured-result
  transport, diagnostic handling, and fresh-session discoverability.
- **FR-037**: Equivalent scenarios through direct CLI invocation, the reference
  provider, and the neutral harness MUST preserve the same Program Kit outcome,
  effect, and primary-disposition meaning.
- **FR-038**: Provider capability gaps, normalization that changes meaning, or
  inability to preserve disclosure and authority boundaries MUST be reported as
  exact incompatibilities.

#### Diagnostics, Disclosure, and Removal

- **FR-039**: Every recoverable setup, verification, invocation-transport, and
  removal path MUST return a meaningful structured result or an explicitly
  classified integration-layer failure.
- **FR-040**: Integration diagnostics MUST have stable identities and MUST state
  the failed subject, violated expectation, consequence, safe observed and
  expected data, and bounded next-action class.
- **FR-041**: Malformed requests, ambiguous intent, unsupported intent,
  unavailable versions, provider incompatibility, collisions, stale
  projections, invocation failure, drift, and missing authority MUST each be
  independently distinguishable.
- **FR-042**: Results, provider projections, installation evidence, and session
  guidance MUST NOT disclose secrets, secret-derived values, unsafe raw
  exceptions, protected paths, transcripts, or executable diagnostic prose.
- **FR-043**: Registration and verification MUST be local-first and MUST NOT add
  telemetry, source upload, or undeclared network access.
- **FR-044**: Removal MUST require explicit human authorization and an exact
  admitted installation record.
- **FR-045**: Removal MUST delete only unchanged integration-owned projections
  from that record and MUST preserve consumer-owned, independently managed,
  missing, adopted, or drifted material.
- **FR-046**: After exact removal, verification MUST report the integration as
  absent without treating independently installed CLI artifacts or unrelated
  provider configuration as owned by the removed integration.

### Requirement Classification

The acceptance boundary names the observable claim; it does not grant release
or publication authority. `Human-review` rows may also use executable evidence,
but only the named reviewer can decide fitness.

| Requirement | Class | Authority | Acceptance Boundary | Proof Class |
|-------------|-------|-----------|---------------------|-------------|
| FR-001 | contract | Maintainer | Exact external CLI acquisition is attributable | evidence-backed |
| FR-002 | safety | Kernel | Callable bytes match the selected release before admission | executable-invariant |
| FR-003 | safety | Maintainer | Consumer proof contains no Program Kit source or Spec Kit | evidence-backed |
| FR-004 | behavior | CLI | CLI remains independently callable | executable-invariant |
| FR-005 | safety | Consumer | Generated runtime has no factory/session dependency | evidence-backed |
| FR-006 | governance | Maintainer | Repository delivery never self-hosts through this integration | executable-invariant |
| FR-007 | contract | Product owner | One versioned canonical session definition governs meaning | executable-invariant |
| FR-008 | contract | Product owner | Factory, binding, capability, and adapter identities remain distinct | executable-invariant |
| FR-009 | contract | Product owner | Public operation/effect meaning remains provider-neutral | executable-invariant |
| FR-010 | behavior | Product owner | Guidance consumes typed result fields and diagnostic identities | executable-invariant |
| FR-011 | governance | Product owner | Guidance grants no domain meaning, selection, or effect authority | executable-invariant |
| FR-012 | contract | Adapter owner | Every projection binds the exact canonical revision | executable-invariant |
| FR-013 | safety | Kernel | Non-exact projections never verify as current | executable-invariant |
| FR-014 | safety | Kernel | Mandatory meaning loss is an explicit incompatibility | executable-invariant |
| FR-015 | safety | Human operator | All installation selections are explicit and exact | executable-invariant |
| FR-016 | safety | Human operator | Configuration effects are explained and authorized first | executable-invariant |
| FR-017 | safety | Consumer | Ownership is explicit and pre-existing material is protected | executable-invariant |
| FR-018 | safety | Kernel | Complete preflight precedes live effects | executable-invariant |
| FR-019 | safety | Kernel | Complete candidate set is staged and validated atomically | executable-invariant |
| FR-020 | safety | Kernel | Admission follows exact live verification only | executable-invariant |
| FR-021 | safety | Kernel | Partial, interrupted, colliding, or unverifiable setup stays untrusted | executable-invariant |
| FR-022 | behavior | CLI | Installation validity and fresh-session availability are distinct | executable-invariant |
| FR-023 | contract | CLI | Lifecycle results preserve effects, evidence, diagnostics, and next action | executable-invariant |
| FR-024 | behavior | Human reviewer | A fresh verified session discovers the supported tool boundary | human-review |
| FR-025 | behavior | Product owner | Guidance requires explanation before incomplete effect-bearing work | human-review |
| FR-026 | safety | Human operator | Availability or conversation never implies current authority | executable-invariant |
| FR-027 | safety | Human operator | Effect invocation carries an exact current scoped grant | executable-invariant |
| FR-028 | safety | Kernel | Invalid or incomplete authority blocks with bounded human action | executable-invariant |
| FR-029 | behavior | Human reviewer | Fresh sessions complete explain, authorize, construct, and evaluate | human-review |
| FR-030 | safety | Kernel | Evaluation remains read-only under drift | executable-invariant |
| FR-031 | safety | Kernel | Remediation is bounded and revalidated separately | executable-invariant |
| FR-032 | contract | CLI | Provider transport preserves the complete Program Kit result meaning | executable-invariant |
| FR-033 | contract | Product owner | Real and neutral adapters consume one canonical definition | evidence-backed |
| FR-034 | architecture | Adapter owner | Provider code contains projection/lifecycle mechanics only | executable-invariant |
| FR-035 | contract | Product owner | Another adapter does not redefine public factory/session meaning | evidence-backed |
| FR-036 | contract | Adapter owner | Conformance proves all mandatory preservation boundaries | executable-invariant |
| FR-037 | contract | Kernel | Direct, neutral, and provider paths preserve normalized meaning | executable-invariant |
| FR-038 | safety | Kernel | Capability or normalization loss fails as exact incompatibility | executable-invariant |
| FR-039 | contract | CLI | Every recoverable path returns a structured result or classified transport failure | executable-invariant |
| FR-040 | contract | Kernel | Every integration diagnostic is complete, safe, evidenced, and actionable | executable-invariant |
| FR-041 | behavior | Kernel | Required negative scenarios remain independently distinguishable | executable-invariant |
| FR-042 | safety | Kernel | Governed outputs withhold protected and unsafe material | executable-invariant |
| FR-043 | safety | Maintainer | Registration and verification stay local-first without hidden effects | evidence-backed |
| FR-044 | safety | Human operator | Removal requires exact record and explicit authority | executable-invariant |
| FR-045 | safety | Consumer | Removal touches only unchanged integration-owned bytes | executable-invariant |
| FR-046 | behavior | CLI | Removed state is reported without claiming unrelated ownership | executable-invariant |

### Key Entities

- **CLI Release Identity**: The exact independently acquired Program Kit CLI
  release selected for the workspace, including the evidence needed to verify
  the callable executable.
- **Canonical Session Integration Definition**: The provider-neutral governed
  meaning of supported operations, authority boundaries, effects, structured
  results, diagnostics, and AI-session guidance.
- **Provider Adapter Identity**: An exact supported mapping from one canonical
  integration revision to one provider integration surface, including its
  declared support and incompatibilities.
- **Tool Binding Projection**: The provider-local material that makes the exact
  CLI callable in the selected workspace without becoming semantic source
  truth.
- **Session Capability Projection**: Provider-local guidance teaching an AI
  session when and how to call Program Kit while preserving human authority and
  typed result handling.
- **Integration Candidate Set**: The complete immutable proposed set of
  provider-local projections and records evaluated before live setup.
- **Installation Record**: The admitted evidence binding the selected CLI,
  canonical revision, adapter, provider, workspace scope, owned projections,
  verification observations, and actual effects.
- **Integration Verification Result**: The current structured determination of
  whether the installation is exact, stale, drifted, incompatible, partial,
  absent, or requires a fresh session.
- **Human Effect Grant**: The exact current authority for provider-configuration
  changes or an effect-bearing Program Kit invocation, scoped to the approved
  request, workspace, operation, and effects.
- **Provider Conformance Evidence**: Evidence that a provider projection and
  invocation channel preserve mandatory canonical meaning without loss or
  hidden authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer unfamiliar with the integration can install and
  verify the exact CLI in a clean isolated workspace, follow any reload
  instruction, and make Program Kit discoverable in a fresh reference-provider
  session within 10 minutes using repository documentation alone.
- **SC-002**: In 10 consecutive fresh-workspace trials, all 10 installations
  either admit the complete exact integration or fail with no trusted partial
  state; none report ready when the CLI or a mandatory projection is missing,
  stale, incompatible, or altered.
- **SC-003**: In 10 consecutive fresh-session happy-path trials, all 10 sessions
  select explanation before construction, obtain explicit human authority
  before effects, complete the bounded construction, and evaluate the admitted
  result without Program Kit source or Spec Kit.
- **SC-004**: Across the agreed malformed, ambiguous, unsupported, unavailable,
  collision, stale, drift, and missing-authority scenarios, 100% produce the
  expected distinct next-action class and 0 create unauthorized consumer or
  provider-configuration effects.
- **SC-005**: For every supportable missing-input scenario in the acceptance
  suite, the AI session identifies and asks for the required human input within
  two interaction turns using structured results alone.
- **SC-006**: Direct invocation, the reference-provider integration, and the
  neutral conformance harness preserve the same outcome, effect-state, and
  primary-disposition meaning for 100% of the shared scenario suite.
- **SC-007**: Every admitted installation records one exact CLI release,
  canonical revision, provider adapter, provider, workspace scope, owned
  projection set, and verification result; no audited record relies on ambient
  discovery or a floating version.
- **SC-008**: Exact removal preserves 100% of unrelated and consumer-owned bytes;
  every drifted or unproven removal target is left unchanged and reported
  explicitly.
- **SC-009**: Security review of the acceptance results, projections, evidence,
  and guidance finds zero secrets, raw stack traces, protected-path disclosure,
  source uploads, telemetry, or executable remediation prose.
- **SC-010**: The generated reference application restores, builds, starts, and
  serves its accepted behavior after the AI provider and Program Kit session
  integration are absent, proving zero added runtime dependency.

## Assumptions

- Codex is the initial real reference provider because this repository already
  uses it, but Codex-specific configuration is not canonical product meaning.
- The first supported installation scope is one explicitly selected workspace;
  user-global and machine-global scopes are deferred.
- An exact Program Kit CLI artifact can be acquired through an ordinary
  distribution mechanism before session registration begins. Failures before
  the Program Kit process can start remain outside its operation-result
  guarantee, but must not be misreported as Program Kit results.
- The current bounded `explain`, `construct`, and `evaluate` operation contracts
  from Feature 001 are the factory behavior exercised by this proof; this
  feature does not generalize consumer authoring semantics.
- A provider may require a fresh session to load workspace registration. Hot
  reload is not assumed or required.
- The neutral conformance harness is independent test evidence, not a second
  supported provider product.
- CLI and provider-adapter upgrades are fresh explicit selections in this
  feature. Automated migration of existing integration state is deferred.
- Network access is permitted only for explicitly authorized acquisition of
  exact distribution inputs. Registration, verification, invocation against
  local workspaces, and removal are otherwise local-first.
- Independent human review remains required to approve whether the session
  experience, authority prompts, diagnostics, and provider-neutral boundary are
  understandable and fit for broader use.

## Dependencies

- The merged Feature 001 CLI proof and its versioned public operation, result,
  diagnostic, construction, admission, and evaluation contracts.
- An exact independently consumable CLI distribution with attributable release
  evidence.
- A reference AI provider that supports workspace-local tool registration,
  session guidance, local invocation, and fresh-session verification.
- A human reviewer who did not author the integration proof and can evaluate
  the end-to-end developer and AI-session experience.
