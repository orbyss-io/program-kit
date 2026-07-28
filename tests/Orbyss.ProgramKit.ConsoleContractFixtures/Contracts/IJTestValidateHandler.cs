namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public interface IJTestValidateHandler
{
    ValueTask<int> HandleAsync(
        JTestValidateRequest request,
        CancellationToken cancellationToken);
}
