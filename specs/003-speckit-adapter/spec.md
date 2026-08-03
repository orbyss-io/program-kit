# Feature Specification: Program Kit Adapter for Spec Kit

**Feature Branch**: `codex/003-speckit-adapter`

**Created**: 2026-08-02

**Status**: Approved — human-approved after accepted-design trace hardening

**Input**: User description: "Create the separately installed Program Kit
Adapter for Spec Kit from the fully reviewed and approved design recorded by
DEC-046 and DESIGN-SPECKIT-ADAPTER.md."

## Intent, Authority, and Scope *(mandatory)*

**Intent Owner**: `joey-orbyss`, Program Kit product owner

**Decision Authority**: `joey-orbyss` resolves product ambiguity, accepts scope
changes, approves the specification and plan, and separately authorizes any
later implementation or release decision.

**In Scope**:

- an exact workspace-local Program Kit consumer setup with neutral
  initialization, local capability discovery, explicit profile selection, and
  reviewable resolution locks;
- a separately installed Spec Kit extension that guides approved Spec Kit work
  into Program Kit exclusively through stable public contracts;
- explicit per-feature applicability, workspace activation defaults, exact
  profile inheritance and overrides, and harmless non-factory behavior;
- a small reviewed handoff and deterministic translation into supported Program
  Kit definitions and requests;
- effect-free public preparation, separately recorded repository authority,
  explicit construction, evaluation, diagnostics, and evidence;
- safe installation, upgrade, disable, re-enable, removal, and adapter-owned
  candidate cleanup; and
- executable, cross-platform, package-only, negative, adversarial, and bounded
  human proof of the complete guided workflow.

**Out of Scope**:

- making Program Kit depend on Spec Kit or introducing Spec Kit concepts into
  Program Kit's kernel or public factory semantics;
- installing or executing the adapter inside the Program Kit repository, using
  Program Kit factory operations to build Program Kit itself, or weakening the
  repository's independent Spec Kit and standard-toolchain bootstrap;
- a native Program Kit planning, roadmap, work-unit, or task system;
- a global Program Kit installation, ambient machine-level semantic defaults,
  or global fallback when the workspace-local distribution is unavailable;
- remote provider marketplaces, version-range solving, best-match selection,
  automatic upgrades, dynamic or untrusted provider loading, sandbox claims,
  trust stores, or signing infrastructure;
- automatic construction from a hook, adapter-issued authority, or treating a
  Spec Kit approval as Program Kit construction authority;
- automated migration, runtime plugin hosting, deployment control, operational
  state management, or a Program Kit runtime in generated products;
- deterministic interpretation of natural language or deterministic custom
  business implementation;
- support for every provider, profile, vocabulary, Spec Kit release, Program
  Kit release, or operating system; and
- a Claude adapter or any additional AI-session provider integration.

**Unresolved Meaning**: None. The human-approved `DEC-046` design is the
authority source for this specification. Exact public schema and command grammar
are planning decisions constrained by the observable requirements below, not
unresolved product meaning.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initialize an exact consumer workspace (Priority: P1)

A developer starts in a clean Spec Kit workspace, acquires one exact
workspace-local Program Kit distribution, initializes neutral Program Kit
state, restores a base lock with no factory profile, installs the adapter, and
uses a base health check to understand what is installed and what is not yet
selected or authorized.

**Why this priority**: Every guided factory workflow depends on an understandable
and non-ambient installation boundary. Initialization must be safe even when the
workspace will initially perform only documentation work.

**Independent Test**: In a clean consumer workspace, complete initialization,
base restore, adapter installation, and base health checking with zero selected
profiles; verify exact local provenance, no global fallback, and no factory
invocation.

**Acceptance Scenarios**:

1. **Given** an empty Spec Kit consumer with an exact workspace-local Program
   Kit distribution, **When** the developer initializes and restores the
   workspace, **Then** the result contains an exact base lock with zero selected
   profiles and clearly distinguishes installed, available, selected,
   activated, and authorized state.
2. **Given** the exact initialization outputs already exist unchanged, **When**
   initialization is repeated, **Then** it completes idempotently without
   rewriting state or selecting a profile.
3. **Given** conflicting, drifted, colliding, unsafe, or globally shadowed
   bootstrap state, **When** initialization, restore, installation, or health
   checking runs, **Then** it fails with a structured actionable result and no
   partial trusted state.
4. **Given** a one-entry local provider/profile inventory, **When** the developer
   lists it, **Then** the entry remains merely available and no selection,
   restore, activation, or authority is inferred.
5. **Given** the exact supported Spec Kit release and a compatible workspace,
   **When** the developer runs
   `specify extension add orbyss-program-kit-adapter`, **Then** the versioned
   extension and its adapter executable are installed without modifying Spec
   Kit managed core.

---

### User Story 2 - Turn approved planning into an authorizable factory proposal (Priority: P1)

A developer uses Spec Kit to specify and plan a supported software feature. The
adapter helps create a small explicit handoff, the human reviews its semantic
choices and ownership, and the adapter deterministically produces exact public
Program Kit inputs. Program Kit then explains and prepares the proposed
construction without changing product files.

**Why this priority**: This is the adapter's primary value: connect guided human
planning to an independently callable factory without manual dense request
authoring or private implementation coupling.

**Independent Test**: Starting from approved Spec Kit artifacts and an exact
selected profile, create and review a handoff, translate it twice, invoke public
preparation and explanation, and verify byte-identical adapter inputs, complete
trace, an exact ungranted construction proposal, and zero product publication.

**Acceptance Scenarios**:

1. **Given** complete approved Spec Kit artifacts and an exact compatible
   profile, **When** the adapter creates and validates a reviewed handoff,
   **Then** every identity-forming value has one authoritative trace and every
   generated versus custom ownership choice is visible.
2. **Given** identical reviewed semantic inputs in different non-semantic order,
   **When** translation is repeated, **Then** adapter-owned definitions and
   requests are byte-identical.
3. **Given** missing, conflicting, ambiguous, unsupported, unreviewed, or stale
   meaning, **When** handoff validation or preparation runs, **Then** the
   adapter returns the exact bounded problem and continuation without guessing,
   repairing prose, or publishing product files.
4. **Given** a valid reviewed handoff, **When** public preparation completes,
   **Then** any human or orchestrator receives the same exact ungranted proposal,
   request binding, closure, live-state preconditions, explanation, and
   authority requirements through Program Kit's public contract.

---

### User Story 3 - Authorize and complete construction without authority confusion (Priority: P1)

After reviewing the prepared proposal, a human records an exact decision through
the configured repository authority provider. The adapter may use the selected
exact grant to invoke construction and evaluation, but it never creates,
broadens, or chooses authority itself.

**Why this priority**: A planning integration is incomplete if users must bypass
the public authority model to construct, while allowing the adapter to approve
itself would violate Program Kit's central governance promise.

**Independent Test**: Record an exact human decision for one prepared proposal,
construct and evaluate the supported output, then repeat with absent, stale,
ambiguous, revoked, and wrong-subject grants and verify no unauthorized writes.

**Acceptance Scenarios**:

1. **Given** a current prepared proposal and a separate exact human decision,
   **When** the repository authority provider records it, **Then** the resulting
   grant and revocation record bind the exact request, subject, effect,
   conditions, provenance, and validity without the adapter acting as issuer.
2. **Given** one selected current matching grant and unchanged preconditions,
   **When** construction and evaluation are explicitly invoked, **Then** Program
   Kit performs only the bounded authorized effect and returns its exact public
   results, receipts, diagnostics, and evidence.
3. **Given** no grant or a stale, ambiguous, revoked, widened, or mismatched
   grant, **When** construction is requested, **Then** the operation performs no
   construction and returns a structured request for input, approval, revision,
   or repair as applicable.
4. **Given** a Spec Kit review or hook completion without a Program Kit grant,
   **When** the adapter advances, **Then** it cannot reinterpret that event as
   authority or automatically invoke construction.

---

### User Story 4 - Apply workspace defaults safely to code and non-code work (Priority: P1)

A team configures the adapter once for the workspace using `off`, `assist`, or
`required` behavior and may select an exact default factory profile. Features
inherit the policy unless they carry an exact override. Documentation-only and
other non-factory features remain harmless, while factory features avoid
repeating the same profile choice.

**Why this priority**: Requiring repetitive selection makes the workflow
unpleasant, but ambient or retroactive defaults could silently change software
meaning or make an accidentally enabled adapter destructive.

**Independent Test**: Exercise all workspace modes, a default profile,
feature-specific enable/disable and profile overrides, a documentation-only
feature, a mixed workspace, a default change, and disable/re-enable behavior.

**Acceptance Scenarios**:

1. **Given** an installed adapter and a documentation-only feature with no
   requested factory output, **When** applicable hooks are dispatched, **Then**
   the feature resolves as disabled or not applicable without a Program Kit
   child process, profile resolution, feature-local Program Kit artifacts, or
   workflow blockage.
2. **Given** an applicable feature and an exact locked workspace default
   profile, **When** the feature is activated, **Then** it inherits the profile
   without repeated selection and its reviewed handoff records the exact
   effective value and inheritance source.
3. **Given** an existing reviewed handoff, **When** the workspace default later
   changes, **Then** the handoff remains pinned to its prior exact selection and
   the difference is reported without silent rebinding or regeneration.
4. **Given** a feature that was mistakenly enabled, **When** it is disabled and
   later re-enabled, **Then** no consumer work, Program Kit product, lock,
   receipt, snapshot, evidence, handoff, or result is deleted or silently
   resumed; stale state is revalidated visibly.
5. **Given** unresolved applicability under `required`, **When** the workflow
   reaches its configured gate, **Then** it may block for an explicit
   applicable, disabled, or not-applicable decision but performs no factory
   effect.

---

### User Story 5 - Diagnose changes and recover without unnecessary proof (Priority: P2)

A developer can understand incompatible versions, stale reviews, changed
implementation, changed traced meaning, unrelated documentation edits, unsafe
paths, interrupted adapter writes, malformed child output, and disclosure-safe
failures. The workflow reruns only evidence invalidated by the actual change.

**Why this priority**: The adapter must remain reliable for humans and AI
sessions without recreating Feature 001's convergence churn or repeating slow
proof after every edit.

**Independent Test**: Run the negative and adversarial matrix, inspect the exact
structured results, and demonstrate that untraced documentation changes reuse
factory evidence while traced semantic changes invalidate only their affected
handoff and downstream artifacts.

**Acceptance Scenarios**:

1. **Given** an edit outside all declared semantic and implementation inputs,
   **When** staleness is evaluated, **Then** existing factory evidence remains
   reusable and no repository-wide rehash or reconstruction is required.
2. **Given** a changed or missing traced value, changed custom implementation,
   or changed exact profile input, **When** staleness is evaluated, **Then** only
   the evidence and adapter artifacts whose declared inputs changed become
   stale.
3. **Given** secret-shaped data, exception-derived data, unsafe paths, malformed
   output, or an interrupted write, **When** the adapter reports failure,
   **Then** it returns a stable disclosure-safe result with honest effect state
   and no partial trusted artifact set.
4. **Given** Program Kit returns structured diagnostics, **When** the adapter
   reports them, **Then** the exact Program Kit result remains intact and
   authoritative rather than being replaced by adapter prose.

---

### User Story 6 - Upgrade or remove the integration without losing work (Priority: P2)

A developer can update, disable, re-enable, or remove the Spec Kit adapter while
each product manager retains ownership of its files and all consumer work and
Program Kit history remain available.

**Why this priority**: The adapter must survive routine Spec Kit upgrades and be
optional. Installation must not become irreversible ownership of the consumer's
workspace.

**Independent Test**: Install, disable, re-enable, update from the previous
compatible adapter fixture, attempt an incompatible update, and remove the
extension on supported platforms while verifying exact ownership and preserved
artifacts.

**Acceptance Scenarios**:

1. **Given** a compatible installed adapter and existing consumer work, **When**
   it is updated, **Then** only adapter-owned installation files change and
   project configuration, handoffs, custom implementation, Program Kit state,
   and Spec Kit managed core remain intact.
2. **Given** an incompatible or interrupted update, **When** installation
   validation fails, **Then** the prior working adapter remains selectable and
   no partial activation is trusted.
3. **Given** an installed adapter, **When** it is removed, **Then** only unchanged
   extension-owned installation files and registration are removed; the local
   Program Kit declaration, manifest, locks, specifications, handoffs, source,
   products, receipts, and evidence remain.
4. **Given** a cleanup request, **When** an adapter-owned candidate is unchanged
   and proven regenerable, **Then** it may be removed explicitly; drifted,
   consumer-owned, Program Kit-owned, or unproven artifacts are preserved with
   an actionable refusal.
5. **Given** a compatible manifest-aware Spec Kit upgrade, **When** the upgrade
   completes, **Then** adapter registration and project-owned layers remain
   intact without requiring a force option.

### Edge Cases

- The exact workspace-local Program Kit executable is absent while a global
  executable with the same command name is available.
- Initialization is repeated over valid state, conflicting state, a
  case-colliding path, or a symlink/junction escaping the workspace.
- The local distribution exposes zero, one, or several entries, but no entry is
  implicitly selected and v1 accepts no version range or best match.
- A neutral manifest and base lock contain zero profiles; a factory feature is
  later activated without an exact compatible profile.
- `assist` is inherited without explicit activation, while `required` reaches a
  feature whose applicability has not been decided.
- A documentation edit changes only prose order versus changing an exact traced
  contract value expressed in Markdown.
- A handoff is absent, unreviewed, reviewed then edited, references moved or
  ambiguous source meaning, or contains an unknown property.
- Custom implementation changes after preparation, or live workspace state
  changes after a grant is issued.
- Zero, multiple, expired, revoked, stale, wrong-subject, wrong-effect, or
  widened authority grants are available.
- Adapter inputs contain duplicate or case-colliding logical paths, unsafe
  paths, shell-shaped values, secret-derived fingerprints, or exception data.
- The Program Kit child process cannot start, returns malformed or
  prose-contaminated output, is interrupted, or reports an indeterminate effect.
- Construction is requested from a lifecycle hook or without fresh matching
  preparation and explanation.
- A workspace default changes after multiple reviewed handoffs already pin the
  earlier default.
- Disable, remove, or cleanup encounters drifted or differently owned files.
- Spec Kit, Program Kit, adapter, schema, contract, provider, profile, runtime,
  or operating-system compatibility is unsupported or stale.

## Requirements *(mandatory)*

### Functional Requirements

#### Workspace acquisition, initialization, and resolution

- **FR-001**: The product MUST use one exact workspace-local Program Kit
  distribution and MUST NOT fall back to an ambient global executable or global
  semantic configuration.
- **FR-002**: Program Kit initialization MUST create only absent neutral
  workspace bootstrap state, bind the exact local distribution, begin with zero
  profile selections, be idempotent and atomic, and grant no factory authority.
- **FR-003**: Initialization MUST perform no profile selection, provider
  activation, package restore, catalog refresh, adapter installation, network
  access, or factory invocation, and MUST refuse conflicting or unsafe existing
  state without partial trusted writes; its result and evidence MUST bind the
  bounded bootstrap effect class and the explicit human-or-authorized-agent
  invocation that requested it.
- **FR-004**: The public local catalog MUST provide a read-only offline inventory
  of exact provider/profile identities, support, contracts, and evidence from
  the invoked distribution without installing, selecting, restoring,
  activating, authorizing, or contacting remote sources.
- **FR-005**: The consumer workspace manifest MUST support zero or more exact
  named provider/profile selections and an optional exact default, MUST reject
  ranges and implicit best matches, and MUST keep the default in repository-owned
  reviewable state.
- **FR-006**: Restore MUST create an exact reviewable base or factory lock for
  the requested composition, distinguish unresolved and unsupported items, and
  invalidate the lock only when its declared distribution, manifest, selection,
  dependency, contract, or evidence inputs change.
- **FR-007**: Public behavior MUST keep installed, available, selected,
  activated, and authorized states distinct; no earlier state, including a
  one-item catalog, may imply a later state.

#### Adapter installation, activation, and lifecycle

- **FR-008**: The adapter MUST be a separately versioned Spec Kit extension
  installable through the exact V1 interface
  `specify extension add orbyss-program-kit-adapter`, MUST ship its executable
  within that extension, MUST be managed through Spec Kit's supported extension
  lifecycle, and MUST NOT modify Spec Kit manifest-managed core templates,
  scripts, or skills.
- **FR-009**: The adapter executable MUST invoke only documented public Program
  Kit CLI contracts and MUST NOT reference Program Kit kernel/provider
  implementation surfaces, test fixture generators, repository engineering
  scripts, or private Spec Kit implementation modules.
- **FR-010**: Base health checking MUST validate exact installation, release,
  manifest/base-lock, extension, and configuration compatibility with zero
  selected profiles; feature health checking MUST additionally validate exact
  applicability, profile, lock, handoff, review, and public contracts.
- **FR-011**: Workspace policy MUST support exact `off`, `assist`, and `required`
  modes with resolution precedence of feature override, workspace default, then
  `off`, and MUST give no authority to machine-global, environment, path-glob,
  or installation-order defaults.
- **FR-012**: Feature applicability MUST resolve before any profile; a disabled
  or non-factory feature MUST require no profile or authority and MUST launch no
  Program Kit child process or create feature-local Program Kit artifacts.
- **FR-013**: An applicable feature MUST resolve an exact locked feature profile
  override or workspace default without fallback, and the reviewed handoff MUST
  record the effective value and whether it was explicit or inherited.
- **FR-014**: Changing a workspace mode or default profile MUST NOT silently
  rebind, migrate, regenerate, or invalidate an existing reviewed handoff whose
  traced inputs remain unchanged; divergence MUST be reported for explicit
  re-handoff.
- **FR-015**: Lifecycle hooks MAY propose and validate adapter work according to
  resolved applicability, but MUST perform no automatic initialization,
  authority recording, grant selection, construction, or non-applicable feature
  write; inherited `assist` alone MUST NOT block implementation.
- **FR-016**: Feature or extension disable, re-enable, update, and removal MUST
  preserve consumer-owned work, Program Kit products and state, reviewed
  handoffs and results, profile selection, and other managers' files; cleanup
  MUST be separate and limited to unchanged proven adapter-owned candidates;
  manifest-aware Spec Kit upgrades MUST preserve extension registration and
  project-owned layers without a force option, and a failed update MUST leave
  the prior working adapter selectable.

#### Handoff, public preparation, and authority

- **FR-017**: The feature handoff MUST be a small explicit factory projection
  containing its exact schema and feature identity, intent owner and review
  state, applicability and decision source, effective profile/provider-family
  binding and inheritance source, explicit provider-specific definition fields,
  requested operation/effect ceiling, ownership, implementation references,
  unresolved, unsupported, deferred, and excluded meaning, and field-level
  trace to approved Spec Kit artifacts or explicit human decisions; it MUST
  contain no authority grant.
- **FR-018**: Candidate handoff generation MUST NOT treat free-form Markdown,
  filename conventions, project names, file extensions, ordering, timestamps,
  agent transcripts, or LLM inference as approved semantic authority.
- **FR-019**: Handoff review MUST bind the exact handoff and named reviewer,
  remain separate from construction authority, and become stale when an
  identity-forming or output-affecting traced value changes.
- **FR-020**: Trace validation MUST distinguish changed traced meaning from
  unrelated source-document edits so unchanged traced values retain applicable
  evidence while missing, ambiguous, or changed values stale only their
  affected downstream closure.
- **FR-021**: Given identical reviewed handoff meaning, referenced implementation
  bytes, adapter release, compatibility declarations, public contracts, and
  canonicalization inputs, translation MUST emit byte-identical adapter-owned
  definitions and requests independent of irrelevant input ordering.
- **FR-022**: Program Kit MUST expose an orchestrator-neutral, effect-free public
  preparation contract that returns an exact ungranted construction proposal,
  request binding, closure, live-state preconditions, explanation, and authority
  requirements without candidate or live publication.
- **FR-023**: Program Kit MUST expose a separately invoked repository-authority
  recording path that consumes the exact preparation output and a separately
  reviewed human decision, binds exact subject/operation/effect/conditions/
  provenance/validity/revocation, and creates no broadened or partial grant.
- **FR-024**: The adapter MUST never issue, populate, broaden, infer, or silently
  select a Program Kit grant and MUST never reinterpret a Spec Kit review or
  lifecycle event as construction authority.
- **FR-025**: Construction MUST be an explicit operation after applicable
  profile resolution, reviewed handoff, successful fresh preparation and
  explanation, human artifact-set review, one exact selected current grant, and
  fresh live-state preflight; any failed precondition MUST produce no
  unauthorized construction.

#### Results, safety, ownership, and proof

- **FR-026**: Every adapter operation MUST return a versioned structured result
  with exact operation/release, outcome, furthest stage, effect state, primary
  disposition, compatibility/staleness, diagnostics, and artifact references,
  and MUST preserve any unmodified Program Kit public result as authoritative.
- **FR-027**: Adapter diagnostics MUST use stable authority-qualified identities,
  exact catalogs, typed subjects/rules, safe expected and observed values,
  bounded causes/consequences, evidence, and actionable continuation without
  requiring automation to parse rendered prose.
- **FR-028**: Adapter file publication MUST be atomic and ownership-aware, MUST
  never mix generated and editable regions, and MUST refuse path escape,
  symlink/junction escape, duplicate/case-colliding paths, unsafe shell
  evaluation, unproven overwrite, or partial trusted publication.
- **FR-029**: Ordinary results, logs, handoffs, evidence, and diagnostics MUST
  exclude secrets, secret-derived fingerprints, protected paths, raw external
  output, exceptions, stack traces, and unsafe commands, with disclosure-safe
  fallback after recoverable pipeline failure.
- **FR-030**: Generated consumer products MUST remain ordinary inspectable
  software with no runtime dependency on Program Kit, Spec Kit, the adapter, AI
  providers, prompts, transcripts, or authoring configuration.
- **FR-031**: V1 MUST remain bounded to the exact supported Spec Kit,
  Program Kit, provider/profile, runtime, contract, canonicalization, and
  operating-system matrix; its initial compatibility envelope MUST bind Spec
  Kit `0.15.1`, the exact Program Kit release chosen in planning, and target
  profile `dotnet10-cshells-0.0.28` representing .NET 10 with CShells `0.0.28`,
  and MUST NOT incidentally add planning, migration, marketplace,
  dynamic-provider, global-graph, or additional-session-provider capabilities.
- **FR-032**: Release proof MUST include two distinct clean factory scenarios,
  documentation-only and mixed-workspace scenarios, exact installation and
  lifecycle proof, deterministic translation, the complete declared negative
  and adversarial matrix, public-contract-only dependency proof, consumer
  runtime-independence proof, and named human product validation; the clean
  scenarios MUST NOT pre-seed Program Kit bootstrap state, selections, adapter
  registration, handoffs, definitions, bundles, requests, or products, and at
  least one package-only acceptance journey plus the human journey MUST use the
  production repository-authority recording path while any test authority is
  separately identified and disclosed.
- **FR-033**: Verification MUST use edit, story, pre-PR, protected-CI, and human
  tiers with declared invalidation sets; equivalent evidence MUST be reused
  while inputs remain unchanged, and a full local gate MUST NOT be required
  merely to duplicate the authoritative merge-candidate platform matrix.
- **FR-034**: The adapter MUST remain a consumer-only product, MUST NOT be
  installed or executed by the Program Kit repository to construct itself, and
  MUST be proven only through separately acquired packaged consumer workspaces
  for downstream adapter behavior.
- **FR-035**: V1 factory execution MUST admit only exact explicitly registered
  first-party providers shipped in the selected Program Kit distribution and
  MUST NOT dynamically discover or execute downloaded provider assemblies.
- **FR-036**: For the initial supported profile, translation MUST emit one
  provider-specific semantic definition, one software-definition bundle,
  consumer-owned implementation references, exact selections and trace, and one
  preparation request followed only by the explain, construct, and evaluate
  requests permitted by public preparation; provider, profile, media-type, and
  schema identities MUST come only from the tested adapter compatibility
  manifest or a public Program Kit preparation result, never from guessing or
  inspecting private installed-file conventions.
- **FR-037**: After declared package acquisition, ordinary adapter operation
  MUST perform no telemetry, source upload, or network access and MUST invoke
  child processes with exact argument arrays rather than generated shell command
  strings.

### Requirement Classification

| Requirement | Class | Authority | Acceptance Boundary | Proof Class |
|-------------|-------|-----------|---------------------|-------------|
| FR-001 | safety | Program Kit CLI | Exact workspace executable used; global shadow rejected | executable-invariant |
| FR-002 | behavior | Program Kit CLI | Neutral idempotent atomic initialization with zero selections | executable-invariant |
| FR-003 | safety | Program Kit CLI | Forbidden bootstrap effects absent; conflicts produce no partial trust | executable-invariant |
| FR-004 | contract | Program Kit CLI | Offline exact inventory with zero selection/acquisition effects | executable-invariant |
| FR-005 | contract | Program Kit kernel | Exact zero-or-more selections and optional repository default | executable-invariant |
| FR-006 | contract | Program Kit kernel | Exact base/factory lock and semantic invalidation behavior | executable-invariant |
| FR-007 | governance | Program Kit kernel | Five states remain observably distinct | executable-invariant |
| FR-008 | safety | Spec Kit extension manager | Supported extension lifecycle leaves managed core unchanged | evidence-backed |
| FR-009 | safety | Adapter | Public-contract-only dependency and invocation closure | executable-invariant |
| FR-010 | behavior | Adapter | Base and feature health checks enforce different readiness floors | executable-invariant |
| FR-011 | governance | Adapter configuration | Exact precedence and no ambient semantic default | executable-invariant |
| FR-012 | safety | Adapter | Non-factory path has no profile, process, artifact, authority, or block | executable-invariant |
| FR-013 | contract | Adapter | Applicable feature pins exact effective profile and source | executable-invariant |
| FR-014 | safety | Adapter | Default change cannot silently rebind reviewed handoff | executable-invariant |
| FR-015 | safety | Adapter hooks | Hooks remain conditional and non-authorizing/non-constructing | executable-invariant |
| FR-016 | safety | Adapter lifecycle | Disable/update/remove preserve all differently owned work | executable-invariant |
| FR-017 | contract | Adapter handoff | Complete bounded projection, ownership, trace, and no grant | executable-invariant |
| FR-018 | governance | Human reviewer and adapter | Heuristic or inferred meaning cannot be admitted | executable-invariant |
| FR-019 | governance | Human reviewer and adapter | Exact review is separate and stales on traced semantic change | executable-invariant |
| FR-020 | quality | Adapter trace validator | Field-level invalidation excludes unrelated prose edits | executable-invariant |
| FR-021 | quality | Adapter translator | Equal relevant inputs produce byte-identical adapter outputs | evidence-backed |
| FR-022 | contract | Program Kit kernel/CLI | Public preparation exposes exact proposal with no publication | executable-invariant |
| FR-023 | governance | Repository authority provider | Exact human decision recorded without broadened/partial grant | executable-invariant |
| FR-024 | governance | Adapter | No adapter-issued, inferred, broadened, or selected authority | executable-invariant |
| FR-025 | safety | Program Kit kernel | Construction requires every fresh exact precondition | executable-invariant |
| FR-026 | contract | Adapter | Versioned exact result preserves Program Kit result | executable-invariant |
| FR-027 | contract | Adapter diagnostics | Stable typed actionable diagnostics, no prose automation | executable-invariant |
| FR-028 | safety | Adapter publisher | Atomic owned writes and hostile-filesystem refusal | executable-invariant |
| FR-029 | safety | Adapter disclosure layer | Sensitive/unsafe values absent from all ordinary channels | executable-invariant |
| FR-030 | quality | Generated product owner | Consumer runtime closure excludes development tooling | evidence-backed |
| FR-031 | governance | Product owner | Exact support envelope and deferred boundaries remain honest | evidence-backed |
| FR-032 | quality | Feature proof owner | Complete claim-driven automated and human evidence set | evidence-backed |
| FR-033 | governance | Repository verification workflow | Proportional tiers and semantic evidence reuse are enforced | evidence-backed |
| FR-034 | safety | Program Kit repository owner | Self-construction is absent; adapter proof runs only in separate packaged consumers | evidence-backed |
| FR-035 | governance | Program Kit CLI composition | Only exact shipped and explicitly registered first-party providers can execute | executable-invariant |
| FR-036 | contract | Adapter translator | Required public artifact set is complete and identities come only from approved sources | executable-invariant |
| FR-037 | safety | Adapter process boundary | Ordinary operation has zero network/upload/telemetry and uses exact argument arrays | executable-invariant |

### Key Entities *(include if feature involves data)*

- **Workspace Distribution Binding**: Exact identity and invocation location of
  the workspace-local Program Kit release; never an ambient global lookup.
- **Workspace Manifest**: Consumer-owned requested composition containing zero
  or more exact named selections and optional workspace default.
- **Resolution Lock**: Program Kit-owned exact base or factory closure containing
  resolved identities, contracts, catalogs, dependencies, support, and evidence.
- **Local Catalog Entry**: Read-only declaration of an exact provider/profile
  available in the invoked distribution; availability is not selection.
- **Adapter Activation Policy**: Repository-owned `off`, `assist`, or `required`
  default plus exact feature overrides.
- **Feature Applicability Decision**: Explicit applicable, disabled,
  not-applicable, or unresolved state resolved before any target profile.
- **Feature Handoff**: Small seeded-then-consumer-owned reviewed projection from
  approved Spec Kit meaning to one supported Program Kit definition family.
- **Handoff Review**: Human evidence binding one exact handoff; never a Program
  Kit construction grant.
- **Preparation Proposal**: Effect-free Program Kit result containing the exact
  prospective construction and authority requirements.
- **Authority Decision and Grant**: Separately reviewed human decision and the
  repository authority provider's exact scoped record and revocation state.
- **Adapter Result**: Versioned adapter operation outcome that preserves the
  unmodified Program Kit result whenever a factory command was invoked.
- **Artifact Ownership Record**: Classification and digest evidence identifying
  adapter-generated, seeded-handoff, Program Kit-owned, or consumer-owned files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Two clean consumer factory journeys with different feature names,
  contracts, routes, namespaces, and custom behavior complete from natural
  language planning through explicit authority, construction, and evaluation
  without pre-seeded Program Kit manifest, lock, profile selection, adapter
  registration, handoff, provider definition, software bundle, factory request,
  or product file.
- **SC-002**: In every documentation-only and explicitly disabled scenario, the
  observed count of Program Kit child-process invocations and feature-local
  Program Kit artifacts is exactly zero.
- **SC-003**: At least five repeated and meaning-preserving permuted translations
  of each supported handoff produce byte-identical adapter-owned definitions and
  request artifacts.
- **SC-004**: Every declared negative and adversarial scenario produces the
  expected structured outcome, effect state, disposition, diagnostic identity,
  safe expected/observed data, and zero unauthorized writes.
- **SC-005**: Clean installation, neutral initialization, base restore, adapter
  installation, exact selection, feature restore, update, disable/re-enable,
  removal, and ownership preservation pass on both supported operating systems
  from packaged consumer releases, with compatible manifest-aware Spec Kit
  upgrades preserving registration without a force option.
- **SC-006**: Changing a workspace default silently rebinds zero existing
  reviewed handoffs, and disable/re-enable/remove deletes or rewrites zero
  consumer-owned or Program Kit-owned artifacts.
- **SC-007**: Generated consumer products build, test, start, and perform their
  demonstrated behavior with zero runtime references to Program Kit, Spec Kit,
  the adapter, AI-provider tooling, or authoring configuration.
- **SC-008**: Three fresh human-guided consumer journeys complete without
  terminal coaching outside shipped instructions; all three reviewers can
  locate the tool declaration, manifest, lock, adapter registration, handoff,
  generated inputs, product files, and evidence; distinguish installation,
  availability, selection, activation, authority, custom/generated ownership,
  workspace defaults, feature overrides, and non-factory behavior; find missing
  input and authority requests actionable; and identify the product responsible
  for each decision.
- **SC-009**: The exact merge candidate receives one authoritative protected
  cross-platform proof run; routine edit and story work requires no duplicate
  full local matrix when its declared invalidation set does not require one.
- **SC-010**: An unrelated documentation, formatting, timestamp, or branch-head
  change invalidates zero factory claims unless it changes an explicitly traced
  semantic value, implementation artifact, compatibility declaration, or
  retained evidence byte named by that claim.
- **SC-011**: After declared package acquisition, every normal, negative, and
  adversarial adapter scenario observes exactly zero telemetry, source-upload,
  or network attempts and zero shell evaluation of handoff-derived values.

## Assumptions and Dependencies

- **Assumption**: Broader compatibility beyond the exact V1 release and profile
  envelope requires separately enumerated executable evidence before it can be
  advertised or selected.
- **Assumption**: Workspace defaults are convenience policies committed to the
  repository, not machine-global configuration or authority.
- **Assumption**: A human or authorized agent may explicitly invoke neutral
  workspace bootstrap, but bootstrap itself grants no later factory authority.
- **Assumption**: Natural-language discovery and handoff proposals remain
  human-reviewed and are not deterministic product claims.
- **Assumption**: The v1 repository authority provider records presence, scope,
  and asserted provenance of a human decision without claiming cryptographic
  proof of human identity.
- **Dependency**: Spec Kit provides its supported extension installation,
  configuration, command, hook, enable/disable/update/removal, and
  manifest-aware upgrade lifecycle.
- **Dependency**: Program Kit's current public result contract advances as one
  surface for `explain`, `construct`, `evaluate`, session, and newly added
  commands. Historical contract evidence remains immutable, but no parallel
  legacy runtime surface or automated consumer migration is required in this
  feature.
- **Dependency**: The selected Program Kit distribution contains only exact
  explicitly registered first-party executable providers and their complete
  manifests, contracts, catalogs, support, provenance, and conformance evidence.
- **Dependency**: Package acquisition may use declared external sources during
  installation/restore; ordinary adapter operation is local-first and offline.
- **Invalidation trigger**: A change to the accepted adapter design, public
  operation boundaries, authority model, ownership model, supported compatibility
  matrix, or constitutional principles requires renewed specification review.
- **Invalidation trigger**: Planning that cannot assign an owner and proof to
  every applicable MUST, negative path, and success criterion must return to
  specification rather than entering implementation.
