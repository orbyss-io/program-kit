namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class JTestRunValidator : IJTestRunValidator
{
    public ValueTask<MetadataFixtureValidationResult> ValidateAsync(
        JTestRunRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        var valid = request.Suite != "missing";
        return ValueTask.FromResult(
            new MetadataFixtureValidationResult(
                valid,
                valid
                    ? []
                    : ["suite 'missing' is unavailable"]));
    }
}
