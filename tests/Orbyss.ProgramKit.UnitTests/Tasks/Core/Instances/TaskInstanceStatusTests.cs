namespace Orbyss.ProgramKit.UnitTests.Tasks.Core.Instances;

[TestClass]
public sealed class TaskInstanceStatusTests
{
    [TestMethod]
    public void CancellationRequestedRemainsSeparateFromTerminalCancellation()
    {
        ITaskContractValidator sut = TasksCoreTestValues.Validator();
        var status = new TaskInstanceStatus(
            TasksCoreTestValues.Instance().Revision,
            TaskInstanceState.Running,
            1,
            true,
            TasksCoreTestValues.Instant,
            TestContractValues.Reference(
                "pkid:task-attempt:program-kit:test-attempt"),
            null,
            null);

        var result = sut.Validate(status);

        Assert.IsTrue(result.IsValid);
        Assert.IsTrue(status.CancellationRequested);
        Assert.IsFalse(status.IsTerminal);
    }

    [TestMethod]
    public void ExactlySucceededFailedAndCancelledAreTerminal()
    {
        TaskInstanceState[] states = Enum.GetValues<TaskInstanceState>();
        var terminal = states.Where(state =>
            new TaskInstanceStatus(
                TasksCoreTestValues.Instance().Revision,
                state,
                0,
                false,
                TasksCoreTestValues.Instant,
                null,
                state is TaskInstanceState.Succeeded or
                    TaskInstanceState.Failed or
                    TaskInstanceState.Cancelled
                    ? TestContractValues.Reference(
                        "pkid:task-outcome:program-kit:test-outcome")
                    : null,
                state is TaskInstanceState.Succeeded or
                    TaskInstanceState.Failed or
                    TaskInstanceState.Cancelled
                    ? TasksCoreTestValues.Instant
                    : null).IsTerminal);

        Assert.AreSequenceEqual(
            [
                TaskInstanceState.Succeeded,
                TaskInstanceState.Failed,
                TaskInstanceState.Cancelled,
            ],
            terminal);
    }
}
