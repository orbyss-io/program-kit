# Program Kit architecture backlog

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

Architecture and implementation checks must reject use of `ProgramKit.DomainEvents` as durable
delivery. This item becomes blocking as soon as a trigger is present; it is not a license to defer a
required reliability decision during feature implementation.
