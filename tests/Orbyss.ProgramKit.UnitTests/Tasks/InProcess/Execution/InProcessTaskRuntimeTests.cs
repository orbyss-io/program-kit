using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Tasks.Coordination;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Core.Cancellation;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Instances;
using Orbyss.ProgramKit.Tasks.Core.Results;
using Orbyss.ProgramKit.UnitTests.Tasks.Composition.TestSupport;
using Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution;

[TestClass]
public sealed class InProcessTaskRuntimeTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task ImmediateExecutionUsesAFreshActivationScope()
    {
        await using var provider = InProcessRuntimeTestServices.Build();
        var control = provider.GetRequiredService<ITaskRuntimeControl>();
        await control.StartAsync(CancellationToken.None);
        var runner = provider.GetRequiredService<ITaskRunner>();

        var outcome = await runner.RunAsync<
            TestTaskRequestModel,
            TestTaskResponseModel>(
            TasksCoreTestValues.Request(),
            CancellationToken.None);

        Assert.AreEqual(TaskExecutionOutcomeKind.Succeeded, outcome.Kind);
        Assert.IsNotNull(outcome.Response);
        Assert.AreEqual("test", outcome.Response.Payload.Subject);
        Assert.AreEqual(
            1,
            provider.GetRequiredService<
                TestTaskActivationScopeResolver>().CreatedScopes);
        await control.StopAsync(true, CancellationToken.None);
    }

    [TestMethod]
    public async Task DispatchUsesOnlyMiddlewareSelectedByTheBinding()
    {
        await using var provider =
            InProcessRuntimeTestServices.BuildWithDispatchMiddleware();
        var control = provider.GetRequiredService<ITaskRuntimeControl>();
        await control.StartAsync(CancellationToken.None);
        var dispatcher = provider.GetRequiredService<ITaskDispatcher>();

        var dispatch = await dispatcher.DispatchAsync(
            TasksCoreTestValues.Request(),
            CancellationToken.None);

        var tracker =
            provider.GetRequiredService<TestTaskMiddlewareTracker>();
        Assert.AreEqual(TaskDispatchDisposition.Accepted, dispatch.Disposition);
        Assert.AreEqual(1, tracker.SelectedInvocations);
        Assert.AreEqual(0, tracker.UnselectedInvocations);
        await control.StopAsync(true, CancellationToken.None);
    }

    [TestMethod]
    public async Task RuntimeRevisionMismatchFailsBeforeAcceptingWork()
    {
        await using var provider = InProcessRuntimeTestServices.Build(
            runtimeRevision: TestContractValues.Reference(
                "pkid:runtime:program-kit:other-runtime"));
        var control = provider.GetRequiredService<ITaskRuntimeControl>();

        var exception = await Assert.ThrowsExactlyAsync<
            InvalidOperationException>(
            () => control.StartAsync(CancellationToken.None).AsTask());

        Assert.Contains(
            "exact in-process runtime revision",
            exception.Message);
        Assert.IsFalse(control.IsStarted);
        Assert.IsFalse(control.IsAccepting);
    }

    [TestMethod]
    public async Task RepeatedIdempotencyKeyIsRejectedInsideTheRetentionWindow()
    {
        await using var provider = InProcessRuntimeTestServices.Build();
        var control = provider.GetRequiredService<ITaskRuntimeControl>();
        await control.StartAsync(CancellationToken.None);
        var runner = provider.GetRequiredService<ITaskRunner>();
        var request = TasksCoreTestValues.Request();

        var first = await runner.RunAsync<
            TestTaskRequestModel,
            TestTaskResponseModel>(
            request,
            CancellationToken.None);
        var second = await runner.RunAsync<
            TestTaskRequestModel,
            TestTaskResponseModel>(
            request,
            CancellationToken.None);

        Assert.AreEqual(TaskExecutionOutcomeKind.Succeeded, first.Kind);
        Assert.AreEqual(TaskExecutionOutcomeKind.Rejected, second.Kind);
        Assert.ContainsSingle(second.Diagnostics);
        await control.StopAsync(true, CancellationToken.None);
    }

    [TestMethod]
    public async Task BackgroundDispatchReturnsAfterAcceptanceAndBecomesTerminal()
    {
        await using var provider = InProcessRuntimeTestServices.Build();
        var control = provider.GetRequiredService<ITaskRuntimeControl>();
        await control.StartAsync(CancellationToken.None);
        var dispatcher = provider.GetRequiredService<ITaskDispatcher>();
        var statusReader = provider.GetRequiredService<ITaskStatusReader>();

        var dispatch = await dispatcher.DispatchAsync(
            TasksCoreTestValues.Request(),
            CancellationToken.None);

        Assert.AreEqual(TaskDispatchDisposition.Accepted, dispatch.Disposition);
        Assert.IsNotNull(dispatch.InstanceRevision);
        TaskInstanceStatus? status = null;
        for (var index = 0; index < 100; index++)
        {
            status = await statusReader.ReadAsync(
                dispatch.InstanceRevision,
                CancellationToken.None);
            if (status?.IsTerminal == true)
            {
                break;
            }

            await Task.Delay(5, TestContext.CancellationToken);
        }

        Assert.IsNotNull(status);
        Assert.AreEqual(TaskInstanceState.Succeeded, status.State);
        await control.StopAsync(true, CancellationToken.None);
    }

    [TestMethod]
    public async Task OverflowCancellationAndCancelShutdownRemainExplicit()
    {
        await using var provider = InProcessRuntimeTestServices.BuildBlocking(1);
        var control = provider.GetRequiredService<ITaskRuntimeControl>();
        await control.StartAsync(CancellationToken.None);
        var dispatcher = provider.GetRequiredService<ITaskDispatcher>();
        var cancellationRequester =
            provider.GetRequiredService<ITaskCancellationRequester>();
        var statusReader = provider.GetRequiredService<ITaskStatusReader>();
        var latch = provider.GetRequiredService<TestTaskExecutionLatch>();
        var first = await dispatcher.DispatchAsync(
            Request("first"),
            CancellationToken.None);
        await latch.Entered.WaitAsync(TestContext.CancellationToken);
        var second = await dispatcher.DispatchAsync(
            Request("second"),
            CancellationToken.None);
        var overflow = await dispatcher.DispatchAsync(
            Request("overflow"),
            CancellationToken.None);

        Assert.AreEqual(TaskDispatchDisposition.Accepted, first.Disposition);
        Assert.AreEqual(TaskDispatchDisposition.Accepted, second.Disposition);
        Assert.AreEqual(TaskDispatchDisposition.Rejected, overflow.Disposition);
        Assert.AreEqual("PKTIP001", overflow.Diagnostics[0].Id);
        var cancellation = await cancellationRequester.RequestAsync(
            new TaskCancellationRequest(
                TestContractValues.Reference(
                    "pkid:task-cancellation-request:program-kit:first"),
                first.InstanceRevision!,
                TasksCoreTestValues.Request().RequestedBy,
                TasksCoreTestValues.Instant,
                "test-cancellation",
                []),
            CancellationToken.None);
        Assert.AreEqual(
            TaskCancellationDisposition.Requested,
            cancellation.Disposition);

        await control.StopAsync(false, TestContext.CancellationToken);
        var firstStatus = await statusReader.ReadAsync(
            first.InstanceRevision!,
            CancellationToken.None);
        var secondStatus = await statusReader.ReadAsync(
            second.InstanceRevision!,
            CancellationToken.None);

        Assert.AreEqual(TaskInstanceState.Cancelled, firstStatus!.State);
        Assert.AreEqual(TaskInstanceState.Cancelled, secondStatus!.State);
    }

    private static Orbyss.ProgramKit.Tasks.Core.Requests.TaskRequest<
        TestTaskRequestModel> Request(string suffix) =>
        TasksCoreTestValues.Request() with
        {
            Revision = TestContractValues.Reference(
                string.Concat(
                    "pkid:task-request:program-kit:",
                    suffix)),
            IdempotencyKey = suffix,
            Payload = new TestTaskRequestModel(suffix),
        };
}
