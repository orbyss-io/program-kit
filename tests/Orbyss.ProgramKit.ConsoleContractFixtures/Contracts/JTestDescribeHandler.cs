namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class JTestDescribeHandler : IJTestDescribeHandler
{
    public ValueTask<int> HandleAsync(
        JTestDescribeRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        Console.WriteLine("describe handler invoked");
        return ValueTask.FromResult(29);
    }
}
