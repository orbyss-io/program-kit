# Feature Specification: Claude Code Session Adapter

**Feature Branch**: `codex/003-claude-code-adapter`

**Created**: 2026-08-01

**Status**: Draft

**Input**: User description: "Add a Program Kit adapter for Claude Code and test it on a separate machine in an isolated consumer workspace. Reuse the provider-neutral session integration established by Feature 002 and update the implementation plan for this provider proof."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect Claude Code to Program Kit (Priority: P1)

A developer working on a separate consumer machine installs an exact Program
Kit CLI release and explicitly adds the supported Claude Code integration to an
isolated repository. The developer can see which Program Kit release, canonical
session contract, Claude Code adapter, provider version, workspace scope, and
files are involved before authorizing any change.

**Why this priority**: A real second-provider installation is the smallest proof
that Program Kit's session contract is portable rather than merely described as
provider-neutral.

**Independent Test**: From a clean consumer machine and repository containing
neither Program Kit source nor Spec Kit, install the exact CLI separately,
explain and authorize the Claude Code integration, start a fresh provider
session, and verify that the session can discover the exact Program Kit entry
point.

**Acceptance Scenarios**:

1. **Given** an isolated consumer repository and independently installed exact
   Program Kit CLI, **When** the developer requests an explanation for the
   selected Claude Code adapter, **Then** the result identifies the exact
   provider, adapter, canonical contract, CLI release, scope, planned effects,
   collisions, required authority, and fresh-session action without modifying
   the workspace.
2. **Given** a current successful explanation and exact human authorization,
   **When** the developer installs the adapter, **Then** the complete
   integration is admitted only after all provider-local projections and
   bindings verify against the canonical contract.
3. **Given** an admitted integration, **When** a fresh supported Claude Code
   session starts inside the repository, **Then** it can discover how to invoke
   the exact workspace-local Program Kit CLI without Program Kit source, Spec
   Kit, Codex, or ambient global Program Kit state.
4. **Given** a missing, unsupported, stale, ambiguous, or mismatched provider,
   adapter, CLI, or canonical-contract selection, **When** installation is
   requested, **Then** no effect occurs and the result identifies the exact
   blocked selection and bounded next action.

---

### User Story 2 - Build Safely Through Claude Code (Priority: P2)

A human-led Claude Code session uses Program Kit to explain, construct, and
evaluate ordinary software while treating structured Program Kit results as
authoritative. The session asks for missing human intent and exact current
authority instead of guessing or interpreting tool availability as permission.

**Why this priority**: Installation has product value only if a real session can
preserve Program Kit's human-governed workflow and meaning through the provider
surface.

**Independent Test**: Give a fresh verified Claude Code session the reference
consumer intent and only the installed provider capability. Confirm that it can
complete explain-to-construct-to-evaluate, pauses for missing meaning and
authority, and leaves the resulting application independent at runtime.

**Acceptance Scenarios**:

1. **Given** incomplete but supportable consumer intent, **When** Claude Code
   invokes Program Kit, **Then** it begins with read-only explanation and asks
   the human only for the bounded information identified by structured results.
2. **Given** an effect-bearing construction request without a current exact
   human grant, **When** the session is ready to construct, **Then** it does not
   perform the effect and asks for the required approval without creating,
   widening, or reusing authority itself.
3. **Given** a current request-bound grant, **When** Claude Code invokes
   construction, **Then** the exact public request is passed to Program Kit and
   the session reports the actual structured outcome without substituting its
   own success claim.
4. **Given** a constructed workspace with drift, **When** the session invokes
   evaluation, **Then** evaluation remains read-only and any remediation remains
   a proposal requiring a separate current request and authority.
5. **Given** a generated reference application, **When** Program Kit, Claude
   Code, the adapter, and session guidance are unavailable, **Then** the
   application can still be restored, built, tested, and run as ordinary
   consumer-owned software.

---

### User Story 3 - Prove Cross-Provider Contract Portability (Priority: P3)

A maintainer evaluates the Claude Code adapter against the same canonical
session meaning and conformance scenarios used for direct CLI invocation, the
neutral harness, and the first reference provider. Provider-specific mechanics
may differ, but Program Kit outcome, authority, effect, diagnostic, and
disclosure meaning cannot change.

**Why this priority**: A second real provider supplies concrete evidence that
provider neutrality is an enforceable contract rather than a Codex-shaped
abstraction.

**Independent Test**: Run the agreed conformance corpus through direct CLI
invocation, the provider-neutral harness, and the Claude Code adapter, then
compare the canonical operation, scope, arguments, effect, outcome,
disposition, diagnostics, and result fields.

**Acceptance Scenarios**:

1. **Given** an accepted canonical session integration revision, **When** the
   Claude Code adapter is evaluated, **Then** it consumes that revision without
   modifying Program Kit's factory operations, authority model, diagnostic
   meaning, or provider-neutral contract.
2. **Given** equivalent requests across direct CLI, neutral harness, and Claude
   Code paths, **When** results are compared, **Then** all mandatory Program Kit
   meanings are equivalent even when provider-local representation differs.
3. **Given** a Claude Code surface that cannot preserve a mandatory boundary,
   **When** conformance is evaluated, **Then** the adapter reports an exact
   incompatibility and cannot be installed as supported.
4. **Given** Claude-specific vocabulary or configuration, **When** canonical
   contracts are inspected, **Then** those details occur only in the adapter
   projection and do not become provider-neutral source truth.

---

### User Story 4 - Diagnose and Recover on the Isolated Machine (Priority: P4)

A developer or AI session receives stable, safe, actionable Program Kit results
when Claude Code registration, discovery, invocation, reload, compatibility, or
workspace state prevents progress. The result clearly distinguishes provider
availability from installation integrity.

**Why this priority**: Provider integration failures are inevitable; meaningful
diagnostics prevent an AI session from guessing, retrying effects blindly, or
masking a partial setup.

**Independent Test**: Exercise every supported malformed, unavailable,
incompatible, collision, interrupted, stale, invocation-failure, and
fresh-session case and verify its stable identity, actual effect, consequence,
and safest next-action class.

**Acceptance Scenarios**:

1. **Given** exact provider artifacts are installed but the current Claude Code
   session has not loaded them, **When** verification runs, **Then** installation
   is reported as valid while provider-session availability is separately
   reported as reload-required or not evaluated.
2. **Given** a Claude-specific discovery or invocation failure, **When** the
   operation returns, **Then** the result uses a stable provider diagnostic and
   preserves the underlying Program Kit outcome and actual effect state.
3. **Given** a recoverable integration failure, **When** structured output is
   requested, **Then** one clean result identifies the failed subject,
   expectation, consequence, safe observations, and bounded next action without
   exposing secrets, transcripts, protected paths, raw exceptions, or unsafe
   commands.
4. **Given** an interrupted or partial setup, **When** verification runs,
   **Then** the integration remains untrusted and the result never claims that
   Claude Code is ready.

---

### User Story 5 - Remove Only the Claude Integration (Priority: P5)

A developer can remove an exact admitted Claude Code integration without
removing the independently installed Program Kit CLI, Claude Code itself,
consumer-owned provider configuration, other provider integrations, or any
unrelated workspace content.

**Why this priority**: Safe reversibility is required before testing a provider
adapter on a real consumer machine.

**Independent Test**: Install an exact integration beside unrelated and
consumer-owned Claude Code material, verify it, remove it using a separate exact
grant, and compare every non-owned byte before and after.

**Acceptance Scenarios**:

1. **Given** an exact unchanged admitted integration and current removal
   authority, **When** removal is requested, **Then** only recorded unchanged
   integration-owned projections are removed and durable lifecycle evidence
   records the actual effect.
2. **Given** a missing, altered, adopted, or drifted integration-owned artifact,
   **When** removal is requested, **Then** uncertain material is preserved and a
   structured result explains why exact removal could not complete.
3. **Given** a removed Claude Code integration, **When** verification runs,
   **Then** it reports that integration as absent while leaving the independently
   installed CLI and all unrelated provider state outside its ownership.

### Edge Cases

- The target machine has Claude Code installed, but its exact version is not in
  the selected adapter's supported range.
- The target repository already contains provider configuration or a capability
  at a path the adapter would need to own.
- The independently installed Program Kit executable reports a version or digest
  different from the selected CLI release.
- Installation completes on disk but an already-running provider session cannot
  observe the new capability until a reload or fresh session.
- Provider invocation changes argument boundaries, current working directory,
  standard-output content, or exit-code meaning.
- Provider-local files are reformatted, normalized, or edited after admission.
- Installation or removal is interrupted after some artifacts changed but
  before the final receipt is committed.
- The provider produces extra commentary around structured Program Kit output.
- The session sees a successful prior result or conversational approval but has
  no current request-bound grant.
- The test machine is clean but network access or credentials needed for
  separately managed tool acquisition are unavailable.
- A path differs only by case or separator across supported target platforms.
- The target is the Program Kit source repository rather than an isolated
  consumer workspace.

## Requirements *(mandatory)*

### Functional Requirements

#### Dependency and Product Boundary

- **FR-001**: This feature MUST consume the accepted provider-neutral session
  integration contract and public Program Kit CLI lifecycle established by
  Feature 002; it MUST NOT redefine their meaning inside the Claude Code
  adapter.
- **FR-002**: The feature MUST add one explicitly selected first-party Claude
  Code adapter with its own exact identity, support claim, provider-specific
  diagnostic catalog, and conformance evidence.
- **FR-003**: The adapter MUST contain only Claude Code-specific projection,
  registration, invocation, discovery, reload, and lifecycle mechanics.
- **FR-004**: The feature MUST NOT change the public factory operation roles,
  infer consumer-domain semantics, introduce a planning system, require an AI
  runtime in generated software, or make Claude Code authoritative over Program
  Kit admission.
- **FR-005**: Program Kit source build, test, approval, and release workflows
  MUST remain independent of a live Claude Code installation, credentials,
  network availability, or provider session.

#### Exact Provider Selection and Projection

- **FR-006**: The developer MUST explicitly select an exact Program Kit CLI
  release, canonical session-contract revision, Claude Code adapter revision,
  supported Claude Code version, consumer workspace, and workspace-local scope.
- **FR-007**: Availability or discovery of Claude Code, a provider capability,
  or the Program Kit CLI MUST NOT imply selection, compatibility, activation,
  trust, or authority.
- **FR-008**: Before any effect, the integration MUST explain all planned
  provider-local projections, ownership, collisions, compatibility findings,
  session-reload implications, and required authority.
- **FR-009**: Every provider-local projection MUST identify the exact canonical
  session definition and adapter identity from which it was derived.
- **FR-010**: Installation MUST stage and validate the complete Claude Code
  projection set before publication and admit it only after the exact CLI,
  provider surface, adapter, binding, session guidance, and live artifacts all
  verify.
- **FR-011**: Existing provider files and directories MUST remain
  consumer-owned unless an exact prior installation record proves that the
  selected adapter owns the exact bytes.
- **FR-012**: The adapter MUST NOT modify user- or machine-global provider
  configuration, provider installation, credentials, unrelated capabilities,
  or shared governance files.

#### Session Behavior and Authority

- **FR-013**: A fresh verified Claude Code session MUST be able to discover the
  exact workspace-local Program Kit invocation path and supported public
  operations from provider-local guidance alone.
- **FR-014**: The provider capability MUST direct the session to consume typed
  Program Kit result fields and diagnostic identities rather than rendered
  prose or provider-generated summaries.
- **FR-015**: When intent, resolution, compatibility, or authority is incomplete,
  the session MUST use read-only explanation and request bounded human input
  rather than guess, silently select, or perform an effect.
- **FR-016**: Before construction or any other effect-bearing Program Kit
  invocation, the adapter MUST preserve an exact current human grant bound to
  the request, workspace, operation, and effects.
- **FR-017**: The adapter and session capability MUST NOT create, approve,
  widen, refresh, infer, or reuse human authority.
- **FR-018**: The Claude Code path MUST preserve Program Kit's operation,
  working scope, argument boundaries, outcome, furthest phase, effect state,
  disposition, diagnostics, artifacts, evidence, receipts, and continuation
  meaning.
- **FR-019**: Evaluation through Claude Code MUST remain read-only; remediation
  MUST remain a bounded proposal whose preconditions and authority are
  revalidated in a separate invocation.

#### Provider Conformance and Isolated-Machine Proof

- **FR-020**: The same canonical conformance scenarios MUST be executable through
  direct CLI invocation, the provider-neutral harness, and the Claude Code
  adapter.
- **FR-021**: Conformance MUST verify operation identity, exact arguments,
  workspace scope, effect classification, authority preservation, structured
  result transport, diagnostic handling, disclosure safety, and fresh-session
  discoverability.
- **FR-022**: Any provider limitation or normalization that changes mandatory
  Program Kit meaning MUST produce an exact incompatibility and prevent the
  adapter from claiming support.
- **FR-023**: Deterministic adapter conformance MUST be independently testable
  without launching a live model; actual Claude Code session behavior MUST be
  recorded separately as provider observation and human-review evidence.
- **FR-024**: The end-to-end consumer proof MUST run on a separate clean machine
  or equivalent isolated machine environment containing neither Program Kit
  source, Spec Kit, the Codex adapter, nor prior Program Kit session state.
- **FR-025**: The isolated-machine record MUST bind the exact consumer workspace,
  operating environment, Program Kit CLI release, canonical definition,
  adapter, Claude Code release, inputs, observations, effects, results, review
  status, and known limitations without storing credentials or transcripts.
- **FR-026**: A missing, interrupted, or inconclusive live-provider review MUST
  remain visibly pending or not evaluated and MUST NOT be reported as passed.

#### Diagnostics, Runtime Isolation, and Removal

- **FR-027**: Every recoverable Claude Code setup, verification, discovery,
  invocation-transport, reload, conformance, and removal failure MUST return a
  meaningful structured Program Kit result with a stable neutral or
  provider-specific diagnostic identity.
- **FR-028**: Results and evidence MUST distinguish installation integrity from
  provider-session availability and MUST report whether a reload, fresh session,
  human input, different exact selection, repair request, or stop is appropriate.
- **FR-029**: Provider projections, results, diagnostics, records, and review
  evidence MUST NOT disclose secrets, secret-derived values, credentials,
  transcripts, protected paths, unsafe raw exceptions, or executable diagnostic
  prose.
- **FR-030**: Registration, verification, deterministic conformance, and removal
  MUST be local-first and MUST NOT add telemetry, source upload, or undeclared
  network access.
- **FR-031**: Generated consumer software MUST restore, build, test, and run
  without Program Kit, Spec Kit, Claude Code, the adapter, session guidance, or
  authoring repository state at runtime.
- **FR-032**: Removal MUST require a separate exact human grant and an admitted
  installation record, and MUST delete only unchanged adapter-owned projections
  from that record.
- **FR-033**: Removal MUST preserve the independently managed Program Kit CLI,
  Claude Code installation, consumer-owned provider configuration, other
  integrations, and all missing, drifted, adopted, or unproven material.
- **FR-034**: Program Kit MUST refuse Claude Code session lifecycle operations
  when the target is the Program Kit source-authoring repository.

### Key Entities

- **Claude Code Adapter Identity**: The exact supported mapping from one
  canonical Program Kit session definition to one exact Claude Code provider
  surface.
- **Claude Code Provider Surface**: The exact provider release and workspace
  integration behavior against which support and discovery are evaluated.
- **Provider Projection Set**: The complete immutable adapter-owned set that
  makes Program Kit discoverable and callable through Claude Code without
  becoming canonical product meaning.
- **Provider Conformance Result**: The structured determination of whether the
  adapter preserves each mandatory canonical operation, authority, effect,
  result, diagnostic, disclosure, and lifecycle rule.
- **Isolated Consumer Environment**: The clean external machine or equivalent
  machine boundary in which Program Kit is consumed without source, Spec Kit,
  Codex integration state, or prior Program Kit session state.
- **Isolated-Machine Review Record**: Safe evidence binding exact releases,
  workspace identity, trials, observations, actual effects, reviewer status,
  limitations, and no transcript or credential content.
- **Claude Integration Installation Record**: The admitted exact relationship
  among CLI, canonical contract, adapter, provider surface, workspace scope,
  owned projections, publication evidence, and current session availability.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer unfamiliar with the adapter can install the exact
  Program Kit CLI separately, explain and install the Claude Code integration,
  verify it, start a fresh session, and reach the first governed Program Kit
  explanation within 10 minutes using only published instructions.
- **SC-002**: Ten consecutive clean-workspace installation trials admit the
  complete exact adapter in all 10 cases, with zero partial installations
  reported as ready.
- **SC-003**: Ten consecutive fresh Claude Code session trials discover the
  workspace integration and preserve the required explain-before-effect and
  human-authority behavior in all 10 cases, or each nonconforming trial remains
  explicitly failed, incompatible, or not evaluated.
- **SC-004**: Across the agreed conformance corpus, direct CLI, neutral harness,
  and Claude Code paths preserve the same canonical operation, effect, outcome,
  and primary-disposition meaning in 100% of comparable cases.
- **SC-005**: Every agreed malformed, missing-authority, unavailable,
  incompatible, collision, interruption, stale, drifted, invocation-failure,
  reload, and removal scenario produces its expected stable diagnostic and zero
  unauthorized effects.
- **SC-006**: Exact removal preserves 100% of unrelated and consumer-owned bytes,
  leaves the separately managed CLI and provider installed, and never deletes
  drifted or unproven content.
- **SC-007**: The isolated-machine evidence identifies every exact release,
  governed input, observation, effect, and limitation required to reproduce the
  proof, with zero credentials, secrets, or transcripts retained.
- **SC-008**: The generated reference application restores, builds, tests, and
  runs after all development-session tooling and provider integrations are
  unavailable, with zero runtime references to them.
- **SC-009**: An independent human reviewer can determine from the evidence
  whether the adapter is supported, incompatible, failed, or not evaluated
  without inspecting Program Kit source or provider transcripts.

## Assumptions

- Feature 002's canonical session integration contracts and lifecycle commands
  are accepted dependencies and will be implemented before this adapter is
  considered complete.
- "Isolated machine" means a separate physical machine, virtual machine, or
  equivalently clean machine boundary; it does not mean permanently air-gapped.
- Program Kit CLI acquisition and Claude Code installation/authentication are
  separate, explicit bootstrap responsibilities and are not owned or removed by
  this adapter.
- Workspace-local provider integration is required. User- and machine-global
  provider configuration remain outside this feature.
- The exact supported Claude Code release and provider-local projection surface
  will be selected during planning from current official provider documentation
  and recorded as a bounded compatibility claim.
- Live-model behavior is observational and human-reviewed; deterministic
  provider projection and conformance remain independently testable without
  provider credentials or network access.
- If Claude Code cannot preserve a mandatory canonical boundary through an
  officially supported workspace-local surface, the correct result is a precise
  incompatibility rather than weakening Program Kit or adding an undeclared
  global/MCP/runtime dependency.

## Out of Scope

- Redesigning Feature 002's provider-neutral contracts merely to resemble Claude
  Code configuration.
- Supporting Anthropic APIs, Claude Desktop, or other Anthropic products as
  though they were the same provider surface as Claude Code.
- Installing, authenticating, updating, or globally configuring Claude Code.
- Publishing a provider marketplace package, MCP server, remote service, or
  user-global Program Kit capability.
- Capturing provider transcripts, prompts, credentials, or model reasoning as
  governed evidence.
- Adding Program Kit planning, migration, runtime-hosting, deployment, or
  operational-state responsibilities.
