namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class ForbiddenMetadataFixtureHandler :
    IForbiddenMetadataFixtureHandler
{
    public ForbiddenMetadataFixtureHandler(IServiceProvider services)
    {
        ArgumentNullException.ThrowIfNull(services);
    }

    public ValueTask<int> HandleAsync(
        MetadataFixtureRequest request,
        CancellationToken cancellationToken) =>
        ValueTask.FromResult(request.Count);
}
