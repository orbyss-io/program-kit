namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class JTestRunHandler : IJTestRunHandler
{
    public ValueTask<int> HandleAsync(
        JTestRunRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        Console.WriteLine("run handler invoked");
        return ValueTask.FromResult(request.MaximumParallelism + 10);
    }
}
