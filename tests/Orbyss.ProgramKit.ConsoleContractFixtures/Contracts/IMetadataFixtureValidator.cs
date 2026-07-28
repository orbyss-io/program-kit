namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public interface IMetadataFixtureValidator
{
    ValueTask<MetadataFixtureValidationResult> ValidateAsync(
        MetadataFixtureRequest request,
        CancellationToken cancellationToken);
}
