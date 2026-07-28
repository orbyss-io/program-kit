namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class ThrowingMetadataFixtureHandler : IMetadataFixtureHandler
{
    public ValueTask<int> HandleAsync(
        MetadataFixtureRequest request,
        CancellationToken cancellationToken)
    {
        _ = request;
        _ = cancellationToken;
        throw new InvalidOperationException(
            "Consumer exception detail must not cross the host boundary.");
    }
}
