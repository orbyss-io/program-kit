namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class MetadataFixtureHandler : IMetadataFixtureHandler
{
    public ValueTask<int> HandleAsync(
        MetadataFixtureRequest request,
        CancellationToken cancellationToken) =>
        ValueTask.FromResult(request.Count);
}
