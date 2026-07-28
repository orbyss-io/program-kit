namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class MetadataFixtureHandler : IMetadataFixtureHandler
{
    public ValueTask<int> HandleAsync(
        MetadataFixtureRequest request,
        CancellationToken cancellationToken)
    {
        MetadataFixtureInvocationRecorder.RecordHandler(
            cancellationToken);
        return ValueTask.FromResult(request.Count);
    }
}
