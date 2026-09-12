# Program Kit architecture backlog

This backlog also holds future functionality proposals as input to an official intake. Deferred
entries are unscheduled and do not authorize intake or implementation. When a proposal is selected
for intake, read its linked material, revisit it against the current product, and confirm scope and
decisions through that intake before treating recommendations as approved design.

## PK-ARCH-001: Durable Integration Events and transactional outbox

- Status: Required before first durable event consumer
- Decision: ADR-0007
- Trigger: any reliable post-commit, background, broker, cross-process, or independently deployed
  event consumer

Design and implement separately versioned `ProgramKit.IntegrationEvents.Abstractions`, the default
runtime integration, and provider-specific outbox packages only after resolving:

- atomic state/outbox persistence without introducing generic repository or unit-of-work contracts;
- at-least-once delivery, publisher confirmation, idempotent consumers, and duplicate detection;
- retry schedules, poison/dead-letter ownership, operational recovery, and compensation;
- ordering/partition keys and explicit non-ordering guarantees;
- event identity, correlation, causation, actor, tenant, time, and trace metadata;
- schema/version compatibility, upcasting or translation, deprecation, and consumer contracts;
- retention, cleanup, replay authorization, privacy classification, and secret/PII handling;
- metrics, tracing, lag, failure alerts, replay evidence, and deterministic tests; and
- mapping from internal domain events to stable integration contracts.

Architecture and implementation checks must reject use of `Orbyss.Foundation.DomainEvents` as durable
delivery. This item becomes blocking as soon as a trigger is present; it is not a license to defer a
required reliability decision during feature implementation.

## PK-ARCH-002: Adopt Program Kit in an existing repository

- Status: Deferred — awaiting official intake; unscheduled
- Trigger: the user explicitly chooses to begin the official intake for existing-repository adoption
- Input: [Existing-repository adoption proposal](existing-repository-adoption-proposal.md)
- Decision: No implementation design accepted; retain the proposal as initial intake material

Explore a workflow for introducing Program Kit into an existing codebase with implemented
specifications, architecture history, tests, and scattered AI instructions. The initial proposal
recommends a dedicated adoption entry point that reconciles inherited evidence and joins the shared
governed delivery lifecycle while retaining established technology choices where appropriate.

Carry this explicit requirement into the official intake: adoption must produce a coherent
repository without unexplained, orphaned legacy artifacts in the adopted scope. It should move,
merge, remove, update, or reconcile files as needed, repair their references, and connect retained
active artifacts to the skills, workflows, or other consumers that actually use them. Merely adding
new Program Kit files alongside unused legacy material is not sufficient. Historical and out-of-scope
files may remain when their purpose and disposition are explicit.

When this item is selected, use the proposal's analysis, alternatives, implementation seams, and
acceptance scenarios as discussion inputs. Revalidate its source/version assumptions, resolve the
actual scope and tradeoffs, and produce the official intake artifacts. The suggested implementation
increments are provisional; no work on them is scheduled or started by this backlog entry.

## PK-ARCH-003: Cumulative release migration guidance for agents

- Status: Deferred — awaiting official intake; unscheduled
- Trigger: the user explicitly chooses to begin the official intake for release migration guidance
- Input: [Release migration guidance proposal](release-migration-guidance-proposal.md)
- Decision: No implementation design accepted; retain the proposal as initial intake material

Provide migration guidance with every release so an agent upgrading an older installation can
understand all relevant changes across its version gap and determine the work needed to complete
the upgrade. The initial proposal recommends cumulative, shipped migration guidance, an applicable
upgrade plan, and evidence that distinguishes component installation from consumer readiness.

Account for every intervening release, but require intermediate installations only when a supported
migration needs them. Revisit historical compatibility claims against actual release artifacts,
consumer states, and test evidence before promising an upgrade from any previous version.

When selected for intake, revalidate the proposal's 0.10.1 findings, resolve its open questions, and
agree scope and acceptance criteria through the official intake. The proposed increments and
release-note corrections are deferred discussion inputs, not authorization to implement or publish.
