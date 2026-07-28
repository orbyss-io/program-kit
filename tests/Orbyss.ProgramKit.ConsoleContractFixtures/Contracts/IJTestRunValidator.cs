namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public interface IJTestRunValidator
{
    ValueTask<MetadataFixtureValidationResult> ValidateAsync(
        JTestRunRequest request,
        CancellationToken cancellationToken);
}
