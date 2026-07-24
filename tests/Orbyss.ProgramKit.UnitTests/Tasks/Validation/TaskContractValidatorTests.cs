namespace Orbyss.ProgramKit.UnitTests.Tasks.Validation;

[TestClass]
public sealed class TaskContractValidatorTests
{
    [TestMethod]
    public void SevenOwnedSemanticIdentitiesValidateAsOneExactContractFamily()
    {
        ITaskContractValidator sut = TasksCoreTestValues.Validator();
        var attempt = new TaskAttempt(
            TestContractValues.Reference(
                "pkid:task-attempt:program-kit:test-attempt"),
            TasksCoreTestValues.Instance().Revision,
            TasksCoreTestValues.Binding().Revision,
            1,
            TaskAttemptState.Running,
            TasksCoreTestValues.Instant,
            null,
            null);

        ProgramKitValidationResult[] results =
        [
            sut.Validate(TasksCoreTestValues.Definition()),
            sut.Validate(TasksCoreTestValues.Request()),
            sut.Validate(TasksCoreTestValues.Instance()),
            sut.Validate(attempt),
            sut.Validate(TasksCoreTestValues.Binding(scheduled: true)),
            sut.Validate(TasksCoreTestValues.Schedule()),
            sut.Validate(TasksCoreTestValues.Occurrence()),
        ];

        Assert.IsTrue(results.All(static result => result.IsValid));
    }

    [TestMethod]
    public void ScheduledBindingRequiresScheduleMisfireAndOverlapSelectionsTogether()
    {
        ITaskContractValidator sut = TasksCoreTestValues.Validator();
        var incomplete = TasksCoreTestValues.Binding() with
        {
            ScheduleRevision = TasksCoreTestValues.Schedule().Revision,
        };

        var result = sut.Validate(incomplete);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
                TasksCoreDiagnosticIds.InvalidTaskActivationBinding &&
            diagnostic.Path == "/scheduleRevision"));
    }

    [TestMethod]
    public void RetryIsASeparatePositiveNumberedAttemptForTheSameInstance()
    {
        ITaskContractValidator sut = TasksCoreTestValues.Validator();
        var first = new TaskAttempt(
            TestContractValues.Reference(
                "pkid:task-attempt:program-kit:test-attempt-one"),
            TasksCoreTestValues.Instance().Revision,
            TasksCoreTestValues.Binding().Revision,
            1,
            TaskAttemptState.Failed,
            TasksCoreTestValues.Instant,
            TasksCoreTestValues.Instant.AddMinutes(1),
            TestContractValues.Reference(
                "pkid:task-failure:program-kit:test-failure"));
        var retry = first with
        {
            Revision = TestContractValues.Reference(
                "pkid:task-attempt:program-kit:test-attempt-two"),
            Number = 2,
            State = TaskAttemptState.Running,
            CompletedAt = null,
            FailureRevision = null,
        };

        Assert.IsTrue(sut.Validate(first).IsValid);
        Assert.IsTrue(sut.Validate(retry).IsValid);
        Assert.AreEqual(first.InstanceRevision, retry.InstanceRevision);
        Assert.AreNotEqual(first.Revision, retry.Revision);
    }
}
