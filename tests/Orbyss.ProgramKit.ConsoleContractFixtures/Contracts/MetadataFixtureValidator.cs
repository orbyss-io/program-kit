namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class MetadataFixtureValidator : IMetadataFixtureValidator
{
    public ValueTask<MetadataFixtureValidationResult> ValidateAsync(
        MetadataFixtureRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        MetadataFixtureInvocationRecorder.RecordValidator();
        return ValueTask.FromResult(
            new MetadataFixtureValidationResult(
                MetadataFixtureInvocationRecorder.ValidatorIsValid,
                MetadataFixtureInvocationRecorder.ValidatorMessages));
    }
}
