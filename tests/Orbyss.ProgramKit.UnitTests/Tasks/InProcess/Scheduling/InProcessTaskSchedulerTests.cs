using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Tasks.Coordination;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Instances;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Scheduling;

[TestClass]
public sealed class InProcessTaskSchedulerTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task FixedDelayUsesThePreviousTerminalCompletionBeforeDispatch()
    {
        await using var provider =
            InProcessRuntimeTestServices.BuildScheduled(
                TimeSpan.FromSeconds(5));
        var control = provider.GetRequiredService<ITaskRuntimeControl>();
        await control.StartAsync(CancellationToken.None);
        var scheduler = provider.GetRequiredService<ITaskScheduler>();
        var statusReader = provider.GetRequiredService<ITaskStatusReader>();
        var reference = TasksCoreTestValues.Instant;

        var first = await scheduler.EvaluateAsync(
            new TaskScheduleEvaluationRequest(
                TasksCoreTestValues.Schedule().Revision,
                reference,
                reference.AddSeconds(5),
                1),
            CancellationToken.None);

        Assert.ContainsSingle(first.AcceptedInstanceRevisions);
        var status = await AwaitTerminalAsync(
            statusReader,
            first.AcceptedInstanceRevisions[0]);
        Assert.IsNotNull(status.TerminalCompletionInstant);

        var second = await scheduler.EvaluateAsync(
            new TaskScheduleEvaluationRequest(
                TasksCoreTestValues.Schedule().Revision,
                first.EvaluatedThrough,
                status.TerminalCompletionInstant.Value.AddSeconds(5),
                1),
            CancellationToken.None);

        Assert.ContainsSingle(second.AcceptedInstanceRevisions);
        Assert.AreEqual(
            status.TerminalCompletionInstant.Value.AddSeconds(5),
            second.Occurrences[0].ScheduledFor);
        await control.StopAsync(true, CancellationToken.None);
    }

    [TestMethod]
    public async Task InvalidDescriptorFailsStartupAndRollsRuntimeBack()
    {
        await using var provider =
            InProcessRuntimeTestServices.BuildScheduled(TimeSpan.Zero);
        var control = provider.GetRequiredService<ITaskRuntimeControl>();

        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(
            async () =>
                await control.StartAsync(CancellationToken.None));

        Assert.IsFalse(control.IsStarted);
        Assert.IsFalse(control.IsAccepting);
    }

    private async ValueTask<TaskInstanceStatus> AwaitTerminalAsync(
        ITaskStatusReader reader,
        Orbyss.ProgramKit.Artifacts.References.ArtifactReference revision)
    {
        for (var index = 0; index < 100; index++)
        {
            var status = await reader.ReadAsync(
                revision,
                TestContext.CancellationToken);
            if (status?.IsTerminal == true)
            {
                return status;
            }

            await Task.Delay(5, TestContext.CancellationToken);
        }

        Assert.Fail("The accepted scheduled instance did not terminate.");
        throw new InvalidOperationException();
    }
}
