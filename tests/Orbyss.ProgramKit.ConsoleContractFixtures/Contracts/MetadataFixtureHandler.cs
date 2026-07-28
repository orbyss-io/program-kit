namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class MetadataFixtureHandler : IMetadataFixtureHandler
{
    public ValueTask<int> HandleAsync(
        MetadataFixtureRequest request,
        CancellationToken cancellationToken)
    {
        MetadataFixtureInvocationRecorder.RecordHandler(
            cancellationToken);
        if (request.Target == "native-types" &&
            request.Total == 9223372036854775000L &&
            request.Ratio == 1234.50M &&
            request.Correlation == Guid.ParseExact(
                "67ed4ad8-cc28-4f98-aecb-852a50d7b04f",
                "D") &&
            request.At == DateTimeOffset.ParseExact(
                "2026-07-28T08:15:30.0000000+02:00",
                "O",
                System.Globalization.CultureInfo.InvariantCulture) &&
            request.Tags.SequenceEqual(["alpha", "beta"]))
        {
            return ValueTask.FromResult(37);
        }

        return ValueTask.FromResult(request.Count);
    }
}
