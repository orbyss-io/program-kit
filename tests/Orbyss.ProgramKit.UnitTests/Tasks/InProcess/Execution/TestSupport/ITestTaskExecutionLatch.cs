namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution.TestSupport;

internal interface ITestTaskExecutionLatch
{
    Task Entered { get; }

    ValueTask WaitAsync(CancellationToken cancellationToken);
}
