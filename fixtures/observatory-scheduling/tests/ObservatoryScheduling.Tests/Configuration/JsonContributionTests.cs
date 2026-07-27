using System.Text.Json;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using ObservatoryScheduling.Core.Configuration;
using ObservatoryScheduling.Core.Contracts.Time;

namespace ObservatoryScheduling.Tests.Configuration;

public sealed class JsonContributionTests
{
    private static readonly JsonSerializerOptions WindowOptions =
        CreateWindowOptions();

    [Test]
    public void TypedConverterAndSourceGeneratedMetadataAreExplicitContributions()
    {
        var converterContribution =
            ObservatoryJsonContributionCatalog.CreateWindowConverter();
        var contextContribution =
            ObservatoryJsonContributionCatalog.CreateModelContext();

        FixtureAssert.IsNotNull(converterContribution.Converter);
        FixtureAssert.IsNull(converterContribution.TypeInfoResolver);
        FixtureAssert.HasCount(1, converterContribution.RuntimeTargetTypes);
        FixtureAssert.IsNull(contextContribution.Converter);
        FixtureAssert.IsNotNull(contextContribution.TypeInfoResolver);
        FixtureAssert.HasCount(4, contextContribution.RuntimeTargetTypes);
    }

    [Test]
    public void WindowConverterRoundTripsWithoutADomAndCanonicalizesPredictably()
    {
        var value = new ObservatoryWindow(
            new DateTimeOffset(2026, 1, 1, 20, 0, 0, TimeSpan.Zero),
            new DateTimeOffset(2026, 1, 1, 21, 0, 0, TimeSpan.Zero));
        var bytes = JsonSerializer.SerializeToUtf8Bytes(value, WindowOptions);
        var canonicalizer = new ProgramKitJsonCanonicalizer();

        var first = canonicalizer.Canonicalize(
            bytes,
            JsonSerializationLimits.Default);
        var second = canonicalizer.Canonicalize(
            first.ToArray(),
            JsonSerializationLimits.Default);
        var roundTrip = JsonSerializer.Deserialize<ObservatoryWindow>(
            first.ToArray(),
            WindowOptions);

        FixtureAssert.SequenceEqual(first.ToArray(), second.ToArray());
        FixtureAssert.AreEqual(value, roundTrip);
    }

    private static JsonSerializerOptions CreateWindowOptions()
    {
        var contribution =
            ObservatoryJsonContributionCatalog.CreateWindowConverter();
        var options = new JsonSerializerOptions();
        options.Converters.Add(contribution.Converter!);
        return options;
    }
}
