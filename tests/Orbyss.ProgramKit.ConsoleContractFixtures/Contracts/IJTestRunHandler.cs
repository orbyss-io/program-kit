namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public interface IJTestRunHandler
{
    ValueTask<int> HandleAsync(
        JTestRunRequest request,
        CancellationToken cancellationToken);
}
