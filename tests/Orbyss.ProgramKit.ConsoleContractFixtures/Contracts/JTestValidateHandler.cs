namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class JTestValidateHandler : IJTestValidateHandler
{
    public ValueTask<int> HandleAsync(
        JTestValidateRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        Console.WriteLine("validate handler invoked");
        return ValueTask.FromResult(23);
    }
}
