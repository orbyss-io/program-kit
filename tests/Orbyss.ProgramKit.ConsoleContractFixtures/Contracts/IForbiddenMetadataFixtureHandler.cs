namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public interface IForbiddenMetadataFixtureHandler
{
    ValueTask<int> HandleAsync(
        MetadataFixtureRequest request,
        CancellationToken cancellationToken);
}
