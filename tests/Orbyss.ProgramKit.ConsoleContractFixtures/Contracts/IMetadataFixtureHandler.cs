namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public interface IMetadataFixtureHandler
{
    ValueTask<int> HandleAsync(
        MetadataFixtureRequest request,
        CancellationToken cancellationToken);
}
