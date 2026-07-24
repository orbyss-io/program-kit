namespace Orbyss.ProgramKit.UnitTests.TestSupport.Fixtures;

internal static class TasksCoreTestValues
{
    internal static DateTimeOffset Instant { get; } =
        DateTimeOffset.Parse(
            "2026-07-23T12:00:00+00:00",
            System.Globalization.CultureInfo.InvariantCulture);

    internal static TaskDefinition Definition() =>
        new(
            TestContractValues.Reference(
                "pkid:task-definition:program-kit:test-task"),
            ProgramKitIdentifier.Parse("pkid:domain:program-kit:tests"),
            TestContractValues.Reference(
                "pkid:contract:program-kit:test-task-request"),
            TestContractValues.Reference(
                "pkid:contract:program-kit:test-task-response"),
            TestContractValues.Reference(
                "pkid:contract:program-kit:test-task-failure"),
            TestContractValues.Reference(
                "pkid:policy:program-kit:test-task-authority"),
            TestContractValues.Reference(
                "pkid:policy:program-kit:test-task-cancellation"),
            TestContractValues.Reference(
                "pkid:policy:program-kit:test-task-idempotency"),
            TestContractValues.Reference(
                "pkid:policy:program-kit:test-task-retry"),
            TestContractValues.Reference(
                "pkid:policy:program-kit:test-task-observability"),
            TestContractValues.Reference(
                "pkid:policy:program-kit:test-task-resource"));

    internal static TaskRequest<TestTaskRequestModel> Request() =>
        new(
            TestContractValues.Reference(
                "pkid:task-request:program-kit:test-task-request"),
            Definition().Revision,
            Definition().RequestContract,
            Definition().ResponseContract,
            Definition().FailureContract,
            ProgramKitIdentifier.Parse("pkid:actor:program-kit:test-operator"),
            Instant,
            new TestTaskRequestModel("test"),
            "test-key",
            [],
            null);

    internal static TaskInstance Instance() =>
        new(
            TestContractValues.Reference(
                "pkid:task-instance:program-kit:test-task-instance"),
            Request().Revision,
            Definition().Revision,
            Definition().RequestContract,
            Definition().ResponseContract,
            Definition().FailureContract,
            Instant,
            "test-key",
            null);

    internal static TaskActivationBinding Binding(bool scheduled = false) =>
        new(
            TestContractValues.Reference(
                "pkid:task-activation-binding:program-kit:test-binding"),
            Definition().Revision,
            TestContractValues.Reference(
                "pkid:handler:program-kit:test-handler"),
            TestContractValues.Reference(
                "pkid:feature:program-kit:test-feature"),
            ProgramKitIdentifier.Parse(
                "pkid:activation:program-kit:test-feature"),
            TestContractValues.Reference(
                "pkid:runtime:program-kit:test-runtime"),
            [],
            Definition().RetryPolicy,
            Definition().IdempotencyPolicy,
            scheduled
                ? TestContractValues.Reference(
                    "pkid:task-schedule-definition:program-kit:test-schedule")
                : null,
            scheduled
                ? TestContractValues.Reference(
                    "pkid:policy:program-kit:test-misfire")
                : null,
            scheduled
                ? TestContractValues.Reference(
                    "pkid:policy:program-kit:test-overlap")
                : null);

    internal static TaskScheduleDefinition Schedule() =>
        new(
            TestContractValues.Reference(
                "pkid:task-schedule-definition:program-kit:test-schedule"),
            Definition().Revision,
            Binding(scheduled: true).Revision,
            TestContractValues.Reference(
                "pkid:schedule-descriptor:program-kit:test-interval"),
            TestContractValues.Reference(
                "pkid:schema:program-kit:test-interval"),
            TestContractValues.Reference(
                "pkid:profile:program-kit:test-occurrence-calculator"));

    internal static TaskOccurrence Occurrence() =>
        new(
            TestContractValues.Reference(
                "pkid:task-occurrence:program-kit:test-occurrence"),
            Schedule().Revision,
            Definition().Revision,
            Schedule().DescriptorRevision,
            Schedule().OccurrenceCalculatorProfile,
            0,
            Instant,
            Instant);

    internal static ITaskContractValidator Validator() =>
        new TaskContractValidator(new ArtifactReferenceValidator());
}
