namespace Orbyss.ProgramKit.UnitTests.Tasks.Results;

[TestClass]
public sealed class TaskExecutionOutcomeTests
{
    [TestMethod]
    public void RejectedOutcomeCannotCarryAcceptedInstanceOrTerminalPayload()
    {
        ITaskContractValidator sut = TasksCoreTestValues.Validator();
        var contradictory = new TaskExecutionOutcome<string>(
            TasksCoreTestValues.Request().Revision,
            TaskExecutionOutcomeKind.Rejected,
            TasksCoreTestValues.Instance().Revision,
            null,
            null,
            []);

        var result = sut.Validate(contradictory);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == TasksCoreDiagnosticIds.InvalidTaskLifecycleView &&
            diagnostic.Path == "/kind"));
    }

    [TestMethod]
    public void SuccessfulOutcomeRequiresTypedResponseForTheAcceptedInstance()
    {
        ITaskContractValidator sut = TasksCoreTestValues.Validator();
        var response = new TaskResponse<string>(
            TestContractValues.Reference(
                "pkid:task-response:program-kit:test-response"),
            TasksCoreTestValues.Instance().Revision,
            TasksCoreTestValues.Definition().ResponseContract,
            TasksCoreTestValues.Instant,
            "complete");
        var outcome = new TaskExecutionOutcome<string>(
            TasksCoreTestValues.Request().Revision,
            TaskExecutionOutcomeKind.Succeeded,
            TasksCoreTestValues.Instance().Revision,
            response,
            null,
            []);

        var result = sut.Validate(outcome);

        Assert.IsTrue(result.IsValid);
    }
}
