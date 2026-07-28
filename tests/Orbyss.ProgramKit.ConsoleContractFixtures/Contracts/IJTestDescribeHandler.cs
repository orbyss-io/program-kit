namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public interface IJTestDescribeHandler
{
    ValueTask<int> HandleAsync(
        JTestDescribeRequest request,
        CancellationToken cancellationToken);
}
