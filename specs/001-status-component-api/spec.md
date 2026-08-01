# Feature Specification: Status Component and API Vertical Slice

**Feature Identity**: `001-status-component-api`

**Origin Branch**: `codex/initialize-spec-kit` (historical creation context;
not the current implementation or closure status)

**Created**: 2026-08-01

**Status**: Approved for implementation

**Input**: User description: "Specify the first Program Kit vertical slice that
proves a contract-governed Status component and API integration, deterministic
factory plumbing, actionable AI diagnostics, safe drift handling, and an
architect-readable workspace explanation without making generated software
depend on Program Kit at runtime."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand Integration Before Construction (Priority: P1)

As a software architect working with an AI session, I want Program Kit to
explain exactly how the proposed Status component and API will integrate before
it writes live artifacts, so I can verify that the selected contracts,
implementations, ownership boundaries, and contribution seams reflect my
approved intent.

**Why this priority**: The product promise is governed integration resolution.
If the architect cannot understand the resolution before code appears, the
factory has not delivered its primary value even when generated code later
builds.

**Independent Test**: Submit the valid reference definitions through the public
factory interface and inspect the pre-construction explanation. The story is
complete when the explanation is deterministic, traces every claim to an
authoritative input, and identifies the exact integration result without
creating live consumer artifacts.

**Acceptance Scenarios**:

1. **Given** approved component and API definitions with complete pinned inputs,
   **When** the architect requests integration resolution, **Then** the result
   identifies the declared meaning, owners, exact contract, selected
   implementation, relationship, contribution seam, intended artifacts,
   evidence obligations, and every blocker before construction.
2. **Given** two compatible definitions processed more than once,
   **When** their integration explanations are compared, **Then** the canonical
   content is identical and contains no time-, machine-, locale-, path-, or
   execution-order-dependent meaning.
3. **Given** a missing, ambiguous, conflicting, or unsupported selection,
   **When** resolution is requested, **Then** no trusted integration result is
   issued and the architect receives a precise structured incompatibility or
   needs-input result.

---

### User Story 2 - Construct an Independently Usable Component and API (Priority: P2)

As a software developer, I want one public Program Kit flow to construct a
reusable Status component and a separate API that consumes its exact package,
so I can prove that independently identified Program Kit-built products
integrate through governed contracts and remain ordinary consumer-owned
software.

**Why this priority**: This is the smallest tangible proof that Program Kit is
a software factory rather than a document model or planning system.

**Independent Test**: Run the accepted valid reference request in a clean
workspace. The story is complete when both outputs are published as a complete
set, the component package is consumed through an isolated local source, the
API's declared status operation is externally observable, and the resulting
software runs without Program Kit, Spec Kit, or an AI session.

**Acceptance Scenarios**:

1. **Given** complete approved Status and API definitions,
   **When** the public construction flow completes, **Then** it produces two
   independently identified bundles, an exact resolution lock, a complete
   artifact manifest, evidence, and admission/publication receipts.
2. **Given** the constructed component package and API,
   **When** the API is exercised as an ordinary consumer,
   **Then** its status operation returns the behavior declared by the
   consumer-owned Status contract and implementation.
3. **Given** the generated API is moved outside the authoring session,
   **When** it is built, tested, and run using only its declared consumer
   prerequisites, **Then** it has no runtime dependency on Program Kit,
   Spec Kit, AI guidance, prompts, transcripts, or repository authoring state.
4. **Given** the same accepted construction identity in clean workspaces with
   different supported paths and cultures,
   **When** construction is repeated, **Then** all Program Kit-owned canonical
   outputs have identical bytes and all custom-owned outputs retain their
   explicitly weaker claim.

---

### User Story 3 - Recover Safely from Invalid Input and Drift (Priority: P3)

As a developer or AI session, I want every refused, failed, or drifted operation
to return a safe structured explanation and bounded next action, so I can
correct the problem without guessing, losing consumer work, or granting the
tool authority it does not have.

**Why this priority**: Diagnostics and ownership safety determine whether the
factory can be used reliably by humans and AI after the happy path.

**Independent Test**: Exercise the invalid-definition, ambiguous-composition,
generated-drift, collision, and interrupted-publication fixtures. The story is
complete when each case has a stable result and diagnostic identity, an honest
effect state, actionable remediation, and no unauthorized mutation.

**Acceptance Scenarios**:

1. **Given** an invalid or incomplete definition,
   **When** it is submitted, **Then** validation returns all independently known
   missing or invalid fields together, records no live artifact changes, and
   provides a stateless continuation when additional input can resolve the
   request.
2. **Given** a duplicate status route, incompatible contract, missing owning
   assembler, or ambiguous meaningful order,
   **When** composition is evaluated, **Then** the operation is blocked with a
   stable diagnostic that identifies the violated seam rule, affected subjects,
   consequence, and safe corrective choices.
3. **Given** a generated-owned artifact has changed,
   **When** evaluation runs, **Then** it reports drift without changing the
   artifact and distinguishes evaluation from any separately authorized repair.
4. **Given** an explicit repair request whose ownership and freshness
   preconditions remain valid,
   **When** repair completes, **Then** only the authorized generated-owned set is
   replaced and new evidence and receipts describe the resulting state.
5. **Given** a recoverable internal or provider failure,
   **When** the normal diagnostic pipeline cannot finish, **Then** the caller
   still receives the safest available structured fault result without raw
   exceptions, secrets, protected paths, or guessed effect claims.

---

### User Story 4 - Resume with a Trustworthy Workspace View (Priority: P4)

As a new contributor or a new AI session, I want one canonical scoped workspace
view that explains the current governed construction, so I can orient myself
without treating source code or prior chat history as the only map of the
system.

**Why this priority**: Program Kit should reduce application-specific AI
instruction clutter and make governed software understandable across sessions.

**Independent Test**: Open only the workspace view and the authoritative
records it references. The story is complete when a fresh contributor can
identify the current integration, artifact ownership, evidence state, blockers,
and safe next action, while stale or drifted information is visibly marked.

**Acceptance Scenarios**:

1. **Given** a completed valid construction,
   **When** a new session reads the workspace view,
   **Then** it can trace identities, semantics, selections, relationships,
   seams, artifacts, ownership, provenance, evidence, gates, receipts, support,
   and diagnostics to their authoritative sources.
2. **Given** an identity-forming input, generated artifact, resolution, or
   applicable evidence has changed,
   **When** the existing workspace view is inspected,
   **Then** its stale state is detectable and it is not presented as current
   truth.
3. **Given** the view omits source-level custom behavior,
   **When** a session needs to debug that behavior,
   **Then** the view directs the session to the owned source rather than
   claiming complete runtime or implementation understanding.

### Edge Cases

- The same identity and revision are supplied with different content.
- An exact referenced provider, contract, package, tool, or evidence item is
  unavailable even though a historical receipt exists.
- Provider discovery finds zero candidates or more than one plausible
  candidate, but no exact selection has been approved.
- A contribution is valid by itself but conflicts with another contribution's
  identity key, route, cardinality, or meaningful order.
- Candidate construction succeeds but live publication preconditions change
  before commit.
- Publication is interrupted after some physical writes but before a complete
  set can be admitted.
- A consumer-owned or seeded-handoff artifact exists where a generated-owned
  artifact was requested.
- A result contains more diagnostics than a selected view can return at once.
- External tool output contains secrets, absolute protected paths, malformed
  data, or untrusted prose.
- The result channel cannot be written, or the process is terminated before the
  public command path can return an envelope.
- Two supported clean workspaces differ by path, culture, clock, or scheduling
  order.
- A workspace view remains present after its closure or evidence has become
  stale, unavailable, or drifted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST accept an explicitly approved reference intent
  describing one Status component bundle, one separate API bundle, their
  identities, the consumer-owned status behavior, and their intended
  relationship.
- **FR-002**: The feature MUST preserve traceability from familiar intake terms
  through normalized semantic records to the exact public contracts used for
  resolution and evaluation.
- **FR-003**: The feature MUST validate request structure, semantic completeness,
  identity integrity, authority, ownership, and applicability before any live
  consumer artifact is written.
- **FR-004**: The feature MUST resolve every identity-forming input to one exact
  accepted revision, including an explicitly approved evaluation context for
  any validity decision, and record the complete finite operation closure in a
  resolution lock without using the ambient clock as semantic authority.
- **FR-005**: Discovery MAY report available support, but the feature MUST
  require an explicit accepted selection and MUST refuse zero, multiple,
  floating, ambient, or implicit best-match results.
- **FR-006**: Before construction, the feature MUST produce a deterministic
  Integration Resolution Explanation covering declared meaning and ownership,
  exact contract and implementation selection, direct/adapted/incompatible
  status, provider and seam decisions, planned artifact ownership, semantic
  coverage, evidence, gates, waivers, and blockers.
- **FR-007**: The Integration Resolution Explanation MUST trace each claim to an
  authoritative source and MUST NOT claim generalized impact, migration,
  source-level custom behavior, runtime behavior, or global-system
  understanding.
- **FR-008**: The feature MUST exercise the public intake-mapping, construction,
  and evaluation roles without requiring callers to use private kernel or
  provider interfaces.
- **FR-009**: The feature MUST construct two independently identified,
  consumer-owned bundles: a reusable component that owns the Status contract
  and custom behavior, and a separate API that consumes the exact component and
  exposes the declared status operation.
- **FR-010**: The component-to-API relationship MUST use an exact local package
  identity and content digest; source-tree proximity or an undeclared direct
  source reference MUST NOT establish integration.
- **FR-011**: The feature MUST preserve the reference Status behavior as
  consumer-owned custom implementation and MUST NOT hard-code Status semantics
  into the kernel, CLI, generic contracts, or reusable provider logic.
- **FR-012**: Contract-declared endpoint contributions MUST be immutable inputs
  to one exact owning assembler whose rules make route identity, cardinality,
  collision, compatibility, and meaningful ordering explicit.
- **FR-013**: Generated projects, references, activation plumbing, contribution
  assembly, manifests, locks, canonical workspace views, and evidence MUST have
  explicit generated ownership; custom behavior MUST be seeded-handoff or
  consumer-owned.
- **FR-014**: Construction MUST stage a complete immutable candidate set,
  validate all mandatory applicable gates, recheck live publication
  preconditions, and admit the set only after complete publication.
- **FR-015**: Partial, interrupted, colliding, stale, or drifted output MUST NOT
  receive a trusted admission or success result.
- **FR-016**: Evaluation MUST report exact, missing, modified, stale, colliding,
  interrupted, unsupported, and unavailable states without mutating live
  artifacts.
- **FR-017**: Repair MUST require a separate explicit request, revalidated
  authority and freshness, and exact ownership preconditions; it MUST NOT
  silently overwrite consumer-owned work or adopt drift as canonical intent.
- **FR-018**: Equal complete construction identities under the selected
  reproducibility profile MUST produce byte-identical Program Kit-owned
  canonical outputs across repeated clean executions within the profile.
- **FR-019**: Every running public command path, including pre-admission refusal,
  MUST return one versioned machine-readable operation result with command,
  exact operation contract, available request/construction identities, outcome,
  furthest phase, proven effect state, primary disposition, artifacts, receipts,
  evidence, diagnostics, and any command-specific inline result.
- **FR-020**: Human-readable output MUST faithfully project the authoritative
  machine result, and machine-output mode MUST contain one clean document with
  logs and progress kept separate.
- **FR-021**: Every diagnostic MUST have a stable authority-qualified identity,
  exact catalog revision, category, severity, subject, violated rule or
  contract, bounded cause and consequence, safe expected/observed data,
  evidence, remediation, and next-action information.
- **FR-022**: Remediation MUST be typed, bounded, preconditioned, and
  non-authorizing; identity, selection, ownership, policy, dependency, widened
  effect, and publication changes MUST require applicable independent approval.
- **FR-023**: A needs-input result MUST return a stateless continuation that
  groups independently known missing inputs inline without requiring a live
  write and is fully revalidated on resume.
- **FR-024**: Diagnostic data and rendering MUST exclude secrets, reversible
  secret fingerprints, protected paths, unsafe commands, raw external output,
  exceptions, and stack traces, including in verbose or fallback modes.
- **FR-025**: A recoverable failure in the normal result pipeline MUST use an
  independent fallback to return the most specific safe fault result and honest
  effect state that can still be proven.
- **FR-026**: A successful construction MUST create
  `.program-kit/workspace.snapshot.json` as a generated-owned canonical view of
  one exact root bundle and finite resolved operation closure.
- **FR-027**: The workspace view MUST trace identities, semantics, coverage,
  bindings, selections, relationships, seams, artifacts, ownership, provenance,
  construction identity, gates, reviews, waivers, evidence, receipts, support,
  retention, and unresolved or unsafe diagnostic state to authoritative
  records without copying or inferring new meaning.
- **FR-028**: Closure and evidence identity in the workspace view MUST make
  stale, drifted, unsupported, unavailable, incomplete, and redacted state
  visible.
- **FR-029**: Constructed consumer software MUST build, test, and run without a
  Program Kit, Spec Kit, AI-provider, prompt, transcript, session-capability, or
  authoring-workspace runtime dependency.
- **FR-030**: The feature MUST use only exact explicitly registered first-party
  providers in the selected distribution and MUST NOT claim sandboxed or
  untrusted third-party execution.
- **FR-031**: The feature MUST operate locally without telemetry, source upload,
  external publication, or network access beyond explicitly declared local
  tooling and package-source effects.
- **FR-032**: The feature MUST preserve Program Kit's independent standard build,
  test, repair, and release path and MUST NOT execute Program Kit against itself
  as a prerequisite or source of authority.
- **FR-033**: The feature MUST keep planning, roadmaps, work units, automated
  migration, deployment control, runtime semantic interpretation, identity
  providers, persistence, telemetry integration, infrastructure generation,
  marketplaces, and additional ecosystems outside this slice.
- **FR-034**: The valid, invalid, repeatability, drift, and repair walkthroughs
  MUST be executable from pinned prerequisites without undocumented manual
  edits or ambient setup.

### Key Entities

- **Software-definition bundle**: A versioned portable unit with one canonical
  root manifest and references to separately owned semantic, implementation,
  configuration, and evidence records.
- **Factory request**: The approved operation intent, exact root, requested
  effect, selections, authority, and preconditions submitted through a public
  Program Kit contract.
- **Resolution lock**: The immutable exact closure of identities, revisions,
  contracts, profiles, providers, dependencies, policies, tools, and other
  output-affecting selections used by one operation.
- **Integration Resolution Explanation**: The architect-facing deterministic
  account of how two definitions can or cannot integrate and why.
- **Contribution seam**: The contract-owned boundary through which immutable
  endpoint contributions reach the one owner of the final composed artifact.
- **Candidate artifact set**: A complete isolated proposed output with declared
  ownership, digests, and validation state that is not yet live or trusted.
- **Operation result**: The authoritative structured account of outcome, phase,
  effect, disposition, artifacts, evidence, diagnostics, receipts, and
  continuation.
- **Diagnostic**: A stable typed finding explaining the violated rule, affected
  subject, consequence, and safe corrective path without granting authority.
- **Admission/publication receipt**: Evidence binding a completely evaluated and
  published artifact set to its exact construction identity and claims.
- **Workspace snapshot**: A deterministic scoped view of the current resolved
  construction and its evidence, with trace links and detectable staleness; it
  is not an independent source of semantic truth.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every valid reference request, an architect can inspect one
  complete Integration Resolution Explanation before any live consumer artifact
  is written.
- **SC-002**: A developer can complete the valid end-to-end walkthrough from
  pinned prerequisites with one documented public flow and no undocumented
  edits or selections.
- **SC-003**: The constructed API demonstrably consumes the exact constructed
  component package and exposes the consumer-declared Status behavior in 100% of
  valid reference runs.
- **SC-004**: Two clean executions with the same construction identity but
  different supported workspace paths and cultures produce identical bytes for
  100% of Program Kit-owned canonical outputs.
- **SC-005**: Every required invalid, ambiguity, collision, drift, interrupted
  publication, provider-failure, and stale-view fixture returns the expected
  stable outcome, effect state, disposition, and diagnostic identity without an
  unauthorized live write.
- **SC-006**: A fresh contributor can complete the valid, invalid,
  repeatability, drift, and authorized-repair walkthrough in no more than one
  hour from the documented pinned prerequisites.
- **SC-007**: In all reference diagnostic fixtures, a human or AI session can
  determine whether to provide input, request approval, retry, repair, revise,
  or stop using only the structured result and its offline-resolvable
  references.
- **SC-008**: The generated consumer software builds, tests, and runs in a clean
  consumer environment with zero Program Kit, Spec Kit, or AI-session runtime
  dependencies.
- **SC-009**: Every governed claim in the workspace snapshot traces to an
  authoritative source, and every tested source/evidence change makes the prior
  snapshot detectably stale.
- **SC-010**: The Program Kit repository retains a clean standard build and test
  path that does not invoke Program Kit itself.

## Assumptions

- The accepted root convergence record and Constitution v1.0.0 are authoritative
  for scope; this specification narrows them to the first delivery slice and
  does not reopen accepted product identity.
- The selected initial construction profile and its exact dependency versions
  are governed project constraints; implementation planning will pin the exact
  tool and package closure without changing this feature's user outcomes.
- The reference consumer intent owns the Status contract and expected behavior.
  Program Kit supplies no built-in business interpretation of "status."
- The custom Status behavior is intentionally minimal and may be seeded for the
  reference fixture, but it remains custom-bounded rather than deterministically
  generated.
- All proof is repository-local: the component is packed to an isolated local
  package source, and no external publication or deployed environment is
  required.
- The first slice demonstrates direct contract-conformant integration. It must
  explain incompatible and ambiguous cases, but it does not implement automated
  adaptation or migration.
- Availability limits before process startup, after forced or unrecoverable
  termination/resource failure, or when the selected result channel cannot be
  written remain outside the operation-result guarantee.
- Human product review remains necessary for semantic adequacy, comprehensibility,
  and accepted risk even when all automated evidence passes.
