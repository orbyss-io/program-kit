# Feature Specification: Program Kit Engineering Quality Gates

**Feature Branch**: `codex/004-engineering-quality-gates`

**Created**: 2026-08-01

**Status**: Draft

**Input**: User description: "Establish repository-wide quality gates for
per-project unit testing, complete line and branch coverage, warning-free builds,
and namespace-to-folder alignment while preserving and clarifying the distinct
proof supplied by contract, integration, acceptance, conformance, and other
higher-level tests. Prepare the constitution amendment and remediation feature
on an isolated branch for implementation after the currently active work."

## Clarifications

### Session 2026-08-01

- Q: Should each production project's 100% line-and-branch threshold be satisfied by its paired unit-test project alone, or may higher-level suites contribute? → A: Paired unit tests alone must provide 100 percent line and branch coverage; broader suites remain separately mandatory.
- Q: Which executable code should count toward each production project's 100% unit line-and-branch coverage denominator? → A: Include all first-party source compiled into Program Kit production assemblies; exclude tests, external dependencies, compiler-generated code without a first-party source location, and materialized consumer outputs.
- Q: How should the repository handle a genuinely infeasible first-party line or branch after reasonable refactoring and test-design attempts have been exhausted? → A: Allow an exact finite line or branch exception with attempted alternatives, rationale, broader proof, owner, review date, expiry, and visible raw coverage.
- Q: Should contract, integration, and acceptance tests each have a distinct repository-level test project, while only unit-test projects are paired one-to-one with production projects? → A: Use distinct repository-level contract, integration, and acceptance test projects; specialized suites may remain separate when their boundary requires it.
- Q: Should every governed proof claim have exactly one primary proof layer, even when one executable test supports several claims or provides secondary evidence elsewhere? → A: Give each claim exactly one primary proof layer and allow any number of explicitly mapped supporting proofs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prove Every Production Project Locally (Priority: P1)

A Program Kit maintainer can identify one unit-test project for every first-party
production project and can navigate from a production directory to the matching
test directory. Running the unit gate proves every executable first-party line
and branch in each production project without allowing coverage in one project
to hide a deficit in another.

**Why this priority**: Complete, project-owned unit proof is the requested
minimum engineering floor and makes missing local behavior visible before
broader workflows obscure it.

**Independent Test**: From a clean checkout, enumerate all first-party production
projects, locate their paired unit-test projects and mirrored directories, run
only those unit projects, and verify separate 100 percent line and branch
coverage results for every production project.

**Acceptance Scenarios**:

1. **Given** the complete set of production projects, **When** repository
   topology validation runs, **Then** every production project has exactly one
   unambiguous paired unit-test project and no unit-test project acts as the
   omnibus owner for multiple production projects.
2. **Given** a production source directory at any depth, **When** its tests are
   inspected, **Then** the paired unit-test project contains the corresponding
   directory path and traceable tests for the executable behavior owned there.
3. **Given** one uncovered executable line or branch in one production project,
   **When** the unit gate runs, **Then** that project fails even if aggregate
   repository coverage would otherwise meet the threshold.
4. **Given** a new first-party production project without a paired unit-test
   project, **When** normal repository verification runs, **Then** verification
   fails before the project can be merged.
5. **Given** an exact first-party line or branch that remains infeasible to
   exercise after reasonable testability and refactoring attempts, **When** a
   coverage exception is reviewed, **Then** raw coverage remains visible and the
   gate can pass only with exact finite approval and alternative evidence.

---

### User Story 2 - Preserve Boundary-Appropriate Product Proof (Priority: P2)

A maintainer can see what every non-unit suite is intended to prove and can keep
complex cross-project or end-to-end tests at the boundary where their claims are
observable. Contract, integration, acceptance, conformance, repeatability,
runtime-isolation, fault-injection, security, and human-review evidence remain
available even when their production paths are already covered by unit tests.

**Why this priority**: Unit coverage cannot prove stable public meaning, real
component collaboration, public CLI workflows, external tool behavior, or
consumer outcomes. Losing those suites would make the percentage stronger while
the product evidence became weaker.

**Independent Test**: Inventory the existing test portfolio and feature proof
obligations, assign each claim to a primary proof layer, migrate the repository
structure, and demonstrate that every pre-existing claim still has equivalent
or stronger evidence at the required boundary.

**Acceptance Scenarios**:

1. **Given** a claim about an isolated decision or local failure path, **When**
   its primary proof is classified, **Then** it is owned by the paired unit-test
   project for that production project.
2. **Given** a claim about stable public schemas, APIs, serialization,
   diagnostics, compatibility, or forbidden dependencies, **When** its proof is
   classified, **Then** it remains a contract proof even when it spans multiple
   production assemblies.
3. **Given** a claim requiring collaboration across real components,
   filesystems, processes, packages, or tools, **When** its proof is classified,
   **Then** it remains an integration or specialized proof and is not flattened
   into a unit test.
4. **Given** a claim about a public CLI workflow or independently observable
   consumer outcome, **When** its proof is classified, **Then** it remains a
   black-box acceptance proof using the public entry point.
5. **Given** a proposed deletion, relocation, or consolidation of a broader
   test, **When** the change is reviewed, **Then** it cannot proceed until the
   same claim is traceable to equivalent or stronger boundary-appropriate
   evidence.
6. **Given** the repository-level higher-order test portfolio, **When** project
   topology is validated, **Then** contract, integration, and acceptance tests
   each have a distinct project and none is paired to one production project.
7. **Given** one executable test that supports several governed claims, **When**
   the requirement-to-proof map is validated, **Then** each claim has exactly
   one primary proof layer and any other evidence is identified as supporting.

---

### User Story 3 - Build with Zero Diagnostic Debt (Priority: P3)

A contributor receives one failing result instead of a successful build whenever
Program Kit emits a compiler, analyzer, code-style, test-framework, package,
restore, or build-system warning. Required diagnostics that default to
informational severity are promoted deliberately, including cancellation flow
inside tests and namespace-to-folder alignment.

**Why this priority**: A green build that hides diagnostics normalizes debt and
allows correctness and structure rules to decay invisibly.

**Independent Test**: Seed one representative diagnostic at each governed build
layer, run the same documented verification used by contributors and automation,
and confirm that every diagnostic fails with an actionable identity and that a
clean repository emits none.

**Acceptance Scenarios**:

1. **Given** a compiler, analyzer, code-style, test-framework, package, restore,
   or build warning, **When** the repository is built or tested through its
   supported commands, **Then** the command fails rather than producing a
   successful result with warnings.
2. **Given** a test call that can accept the current test cancellation token,
   **When** the token is not flowed, **Then** command-line analysis reports a
   build-blocking diagnostic.
3. **Given** a source namespace that differs from the project root namespace
   plus its containing directory path, **When** command-line analysis runs,
   **Then** the build fails without depending on an editor session.
4. **Given** an existing broad suppression, **When** the remediation is
   completed, **Then** it is removed or replaced by an exact local suppression
   whose adjacent rationale proves the diagnostic inapplicable or incorrect.

---

### User Story 4 - Get Fast, Honest Contributor Feedback (Priority: P4)

A contributor can run a documented fast verification path while developing and
a complete path before merge. The fast path covers unit, topology, namespace,
and diagnostic gates; the complete path additionally runs every applicable
contract, integration, acceptance, conformance, and specialized suite without
silently skipping unavailable evidence.

**Why this priority**: Strict gates are sustainable only when ordinary changes
receive quick local feedback and slower boundary proofs remain explicit rather
than being bypassed.

**Independent Test**: On a clean supported environment, run both documented
paths, compare the executed proof inventory with the declared portfolio, and
verify that unavailable mandatory evidence is reported as not evaluated and
blocks completion.

**Acceptance Scenarios**:

1. **Given** a clean checkout with prerequisites available, **When** the fast
   path runs, **Then** it builds every required target, runs all paired unit
   projects and structural gates, and does not rely on stale binaries.
2. **Given** a clean checkout, **When** the complete path runs, **Then** every
   declared automated proof layer is executed or is reported explicitly as a
   blocking missing prerequisite rather than silently skipped.
3. **Given** an acceptance test that invokes the Program Kit CLI, **When** tests
   run without a prior manual build, **Then** the exact CLI under test is built
   as a declared dependency before execution.
4. **Given** an environment where a specialized proof is intentionally
   observational or human-reviewed, **When** automated verification completes,
   **Then** its state remains distinct from passed and cannot be inferred from
   unit or integration coverage.

### Edge Cases

- A production project contains only a root entry point and no subdirectories.
- A production source file contains multiple executable types or partial types
  spread across directories.
- Compiler-generated branches appear in coverage output even though no
  first-party source line owns them.
- A materialized consumer artifact contains executable code generated by Program
  Kit but is not compiled into a Program Kit production assembly.
- A contract test crosses assemblies, while an integration test also asserts a
  portion of the same public contract.
- One executable test supplies supporting evidence for several claims or proof
  layers.
- A filesystem or process-heavy test is deterministic but cannot honestly be
  isolated as a unit test.
- An analyzer rule defaults to informational severity and is therefore
  unaffected by ordinary warning-as-error configuration.
- A package or restore warning is emitted outside the language compiler.
- A linked or shared test helper has no single mirrored production directory.
- A project or test suite is added by the active features after this preparation
  branch was created from `main`.
- A test passes only because a CLI binary from an earlier build remains on disk.
- A platform-specific branch is executable only on one supported operating
  system.
- A diagnostic is genuinely incorrect or inapplicable for one exact source
  location.

## Requirements *(mandatory)*

### Functional Requirements

#### Scope and Baseline

- **FR-001**: The remediation MUST apply to every first-party production project
  present when implementation begins, including projects introduced by features
  completed after this specification branch was created.
- **FR-002**: Before implementation changes test structure, the feature MUST
  record the production-project inventory, test-project inventory, executable
  proof inventory, current warning and suppression inventory, namespace
  mismatches, and per-project line and branch coverage baseline.
- **FR-003**: The implementation branch MUST be reconciled with the completed
  active feature branches before the baseline is accepted; stale project or
  proof inventories MUST block implementation.
- **FR-004**: This feature MUST change repository engineering evidence and
  enforcement without changing Program Kit's accepted public behavior merely to
  make a gate pass.

#### Paired Unit Projects and Coverage

- **FR-005**: Every first-party production project MUST have exactly one
  corresponding unit-test project with an unambiguous project identity derived
  from the production project it owns.
- **FR-006**: A paired unit-test project MUST own unit proof for only its
  corresponding production project; it MAY use shared test infrastructure and
  the production project's ordinary dependencies but MUST NOT remain an omnibus
  unit-test owner for unrelated production projects.
- **FR-007**: Below each paired unit-test project root, test directories MUST
  mirror the corresponding production directories, while project-root source
  behavior MUST be tested at the test-project root.
- **FR-008**: Test names or an adjacent machine-checkable mapping MUST make every
  production type or behavior under test traceable without requiring a one-test-
  file-per-source-file rule.
- **FR-009**: Unit tests MUST target and report 100 percent of executable
  first-party production lines and 100 percent of executable first-party
  production branches for each production project separately.
- **FR-010**: Coverage contributed by contract, integration, acceptance,
  conformance, or other broader suites MUST NOT count toward the per-project unit
  coverage gate, even when those suites execute the same production path. Every
  boundary-appropriate broader suite MUST be evaluated separately from that
  coverage result.
- **FR-011**: The coverage denominator MUST include executable first-party source
  compiled into Program Kit production assemblies and MUST exclude test code,
  external dependencies, compiler-generated code without a first-party source
  location, and materialized consumer artifacts that are not Program Kit
  production assemblies. Compiler-generated behavior mapped to an executable
  first-party source location remains in scope.
- **FR-012**: Coverage exclusions MUST be derived from the denominator rule and
  reported explicitly; arbitrary file, type, line, or branch exclusions used
  only to reach the threshold MUST fail verification.
- **FR-013**: Adding a first-party production project or executable production
  path MUST automatically place it under the pairing, mirror, and coverage gates
  without requiring a maintainer to remember a second opt-in list.

#### Layered Test Portfolio

- **FR-014**: The repository MUST maintain a requirement-to-proof map that gives
  each governed claim exactly one primary proof layer and identifies any number
  of supporting proofs at other layers. One executable test MAY support several
  claims, but no claim MAY have multiple co-primary layers.
- **FR-015**: Unit proof MUST validate isolated decisions and local failure paths
  owned by one production project.
- **FR-016**: Contract proof MUST validate stable public schemas, APIs,
  serialization, diagnostics, compatibility, and allowed or forbidden
  dependency boundaries.
- **FR-017**: Integration proof MUST validate collaboration across multiple real
  components or filesystem, process, package, or tool boundaries.
- **FR-018**: Acceptance proof MUST invoke a public product entry point and
  validate a complete public workflow or independently observable consumer
  outcome without private implementation coupling.
- **FR-019**: Conformance, repeatability, runtime-isolation, fault-injection,
  security, performance, and human-review evidence MUST remain distinct whenever
  the claim requires its specialized boundary or evidence semantics.
- **FR-020**: Contract, integration, and acceptance tests MUST each have one
  distinct repository-level test project organized by the claim or boundary it
  proves. These projects MUST NOT be paired to or duplicated for each production
  project.
- **FR-021**: The remediation MUST NOT delete, weaken, relabel, or replace a
  broader proof solely because the same production path has unit coverage.
- **FR-022**: A broader test MAY be moved, consolidated, or replaced only when
  the requirement-to-proof map demonstrates equivalent or stronger evidence at
  the same required boundary and all affected negative paths remain explicit.
- **FR-023**: Shared fixtures and test infrastructure MUST have an explicit
  repository-level owner and namespace and MUST NOT obscure which production
  project or proof layer a test serves.

#### Diagnostics, Namespaces, and Suppressions

- **FR-024**: Supported repository build and test commands MUST fail on every
  emitted compiler, analyzer, code-style, test-framework, package, restore, and
  build-system warning.
- **FR-025**: Repository policy MUST explicitly promote required diagnostics that
  default below warning severity so they fail command-line builds; this includes
  namespace-to-folder mismatch and failure to flow the available test
  cancellation token.
- **FR-026**: Every source namespace MUST equal the owning project's exact root
  namespace plus the source file's containing directory path; a project-root
  source file MUST use the exact root namespace.
- **FR-027**: Namespace enforcement MUST run during documented command-line
  verification on every supported contributor and automation platform and MUST
  NOT depend on editor-only context.
- **FR-028**: Blanket, inherited, wildcard, or unexplained diagnostic
  suppressions MUST be removed.
- **FR-029**: An exact local suppression MAY remain only for a demonstrably
  inapplicable or incorrect diagnostic and MUST record its diagnostic identity,
  bounded source scope, and rationale beside the suppression.
- **FR-030**: Suppressions MUST NOT lower the project-pairing, unit-coverage,
  namespace, warning-free, or boundary-proof floors.

#### Verification and Migration Safety

- **FR-031**: The repository MUST expose one documented fast verification path
  for build, paired unit tests, coverage, topology, namespaces, and diagnostics,
  and one documented complete path for all applicable automated proof layers.
- **FR-032**: The fast path MUST build every artifact required by its tests and
  MUST NOT pass because of a stale output from an earlier command.
- **FR-033**: The complete path MUST execute every declared automated proof or
  report a missing mandatory prerequisite as blocking and not evaluated; it MUST
  NOT silently skip proof.
- **FR-034**: Test execution, coverage collection, and gate evaluation MUST
  produce a single unambiguous failing process result when any mandatory project
  or proof layer fails.
- **FR-035**: Each structural gate MUST be tested by seeding a representative
  violation and demonstrating an actionable failure for missing project pairing,
  folder mismatch, uncovered line, uncovered branch, namespace mismatch,
  governed diagnostic, unjustified suppression, and stale test dependency.
- **FR-036**: The remediation MUST preserve ordinary restore, build, test, and
  runtime behavior of generated consumer artifacts and MUST NOT impose Program
  Kit repository analyzer or test topology policy on consumer-owned projects.
- **FR-037**: Existing public contract, integration, and acceptance outcomes
  MUST be compared before and after migration, and any changed result MUST remain
  a blocker until explained by an accepted product change outside this feature.
- **FR-038**: A custom compiler analyzer MUST NOT be introduced unless planning
  demonstrates a repository rule that cannot be enforced reliably through
  existing compiler, analyzer, build, coverage, or repository-validation
  mechanisms.
- **FR-039**: The default per-project unit gate MUST require 100 percent raw line
  and branch coverage; no repository-wide reduction, rounding allowance,
  wildcard, or unreviewed tolerance MAY replace that target.
- **FR-040**: A finite coverage exception MAY allow only exact named source lines
  or branches to remain uncovered after reasonable attempts to exercise them
  through observable behavior, introduce a bounded test seam, refactor without
  changing accepted behavior, and use deterministic test techniques have been
  documented.
- **FR-041**: Private visibility, inconvenience, test duration, or a complex
  arrange phase alone MUST NOT justify a coverage exception. The exception MUST
  show that direct unit exercise would be unsafe, nondeterministic,
  environment-destructive, behavior-changing, or disproportionate after the
  documented alternatives were attempted.
- **FR-042**: Every coverage exception MUST identify the production project,
  exact source location or branch, attempted alternatives, bounded reason,
  residual risk, alternative boundary-appropriate proof, approving owner,
  review date, and finite expiry.
- **FR-043**: Raw coverage and every accepted exception MUST remain visible in
  gate output. An exception MUST NOT remove its location from the denominator,
  label it covered, or contribute covered hits to the reported percentage.
- **FR-044**: An expired exception or a material change to its source location,
  behavior, risk, or alternative proof MUST invalidate the exception and block
  completion until it is removed or reapproved from current evidence.

### Key Entities

- **Production Project**: A first-party project under Program Kit source control
  whose output is shipped or executed as part of Program Kit, excluding tests,
  fixtures, generated consumer workspaces, and repository-only test support.
- **Paired Unit-Test Project**: The single test project that owns isolated unit
  proof and per-project coverage for one production project and mirrors that
  project's source directories.
- **Proof Claim**: A testable statement about local behavior, a public contract,
  component collaboration, a product workflow, a consumer outcome, or a
  specialized evidence obligation.
- **Proof Layer**: The primary boundary at which a proof claim is honestly
  observable: unit, contract, integration, acceptance, conformance, specialized
  automated evidence, or human review.
- **Requirement-to-Proof Map**: The machine-checkable inventory connecting each
  governed claim to its primary proof, supporting evidence, owner, execution
  path, and current status.
- **Coverage Denominator**: The exact set of executable first-party production
  lines and branches against which one production project's unit gate is
  evaluated.
- **Coverage Exception**: A finite human-approved record for exact uncovered
  lines or branches that preserves raw coverage and binds attempted alternatives,
  bounded rationale, residual risk, alternative proof, owner, review, and
  expiry without claiming the location was covered.
- **Quality Gate**: A command-line check whose failure prevents merge and release
  when a required topology, coverage, diagnostic, namespace, dependency, or
  proof condition is unsatisfied.
- **Local Suppression Record**: The exact diagnostic identity, source scope, and
  adjacent rationale proving why one diagnostic is inapplicable or incorrect
  without weakening a governed floor.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 percent of first-party production projects have exactly one
  paired unit-test project and 100 percent of their production directory paths
  are represented in that test project.
- **SC-002**: Every first-party production project reports 100 percent raw unit
  line and branch coverage or identifies every raw deficit through an accepted
  exact finite coverage exception, with zero arbitrary coverage exclusions and
  zero hidden uncovered locations.
- **SC-003**: Supported clean build and test paths complete with zero compiler,
  analyzer, code-style, test-framework, package, restore, or build-system
  warnings.
- **SC-004**: Command-line verification reports zero namespace-to-folder
  mismatches across production and test source.
- **SC-005**: 100 percent of accepted repository proof claims are mapped to
  exactly one primary proof layer with zero co-primary ambiguity, and every pre-
  remediation contract, integration, acceptance, conformance, and specialized
  claim retains equivalent or stronger evidence after migration.
- **SC-006**: A clean checkout with prerequisites available can run the fast and
  complete verification paths without a preparatory manual build or stale
  binary, and every declared mandatory proof is executed or blocks as not
  evaluated.
- **SC-007**: Each of the eight representative gate violations in FR-035 causes
  a deterministic nonzero result that identifies the violated rule and affected
  project, source path, diagnostic, or proof.
- **SC-008**: On the repository's baseline automation environment, the fast
  verification path completes within two minutes while the complete path retains
  all broader suites regardless of their separately recorded duration.
- **SC-009**: Generated consumer applications exhibit zero new Program Kit
  repository analyzer, test-framework, coverage, or runtime dependencies after
  remediation.
- **SC-010**: The repository contains one distinct contract-test project, one
  distinct integration-test project, and one distinct acceptance-test project,
  and each executes independently through the documented complete path.

## Assumptions

- Implementation begins only after the currently active features are complete
  and this branch has been reconciled with their resulting projects, tests, and
  accepted proof obligations.
- The strict unit-coverage gate is supplied only by paired unit-test projects;
  incidental production coverage from higher-level suites is reported
  separately and cannot fill a unit gap. An accepted finite exception can allow
  the gate to proceed but cannot make the raw unit gap appear covered.
- Contract, integration, and acceptance suites are distinct repository-level
  projects organized by proof boundary; they do not require a duplicate project
  for every production project.
- One test or observation may support several claims, but every claim has one
  primary proof layer so execution and failure meaning remain unambiguous.
- Compiler-generated code without a first-party source location, external
  dependencies, test assemblies, and materialized consumer artifacts are not
  part of a Program Kit production project's unit-coverage denominator.
- Exact local suppressions for demonstrably inapplicable or incorrect
  diagnostics are permitted; suppressions for convenience, inherited
  suppressions, and suppressions that lower a governed floor are not.
- Existing platform and local-first constraints remain authoritative; a complex
  integration or acceptance proof may take longer than the fast path and may use
  declared local processes, filesystems, packages, or tools when its claim
  requires them.

## Dependencies

- Program Kit Constitution v1.1.0 with Principle X, Layered Verification and
  Enforced Code Quality.
- Completion and reconciliation of the active feature branches that precede
  implementation of this remediation.
- The existing Program Kit public-contract, integration, acceptance,
  conformance, and specialized evidence obligations established by accepted
  feature artifacts.

## Out of Scope

- Implementing or changing unrelated Program Kit product behavior discovered
  during the quality audit; such work requires its own specification or an
  accepted change to the feature that owns the behavior.
- Removing complex tests merely to reduce duration, dependencies, setup, or
  maintenance cost.
- Requiring generated consumer-owned projects to adopt Program Kit's repository
  test topology, analyzer policy, namespace root, or coverage thresholds.
- Treating live-provider observations or human-review obligations as automated
  passes.
- Creating a distributable general-purpose analyzer when solution-local existing
  mechanisms can enforce the rule.
- Merging, modifying, or implementing the currently active feature branches from
  this preparation branch.
