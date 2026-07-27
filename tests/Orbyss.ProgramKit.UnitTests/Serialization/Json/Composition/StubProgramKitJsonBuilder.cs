namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class StubProgramKitJsonBuilder : IProgramKitJsonBuilder
{
    public IProgramKitJsonBuilder AddProfile(
        JsonSerializationProfile profile) =>
        this;

    public IProgramKitJsonBuilder AddOwnedProfile(
        JsonSerializationProfile profile,
        JsonProfileOwnedMechanics mechanics) =>
        this;

    public IProgramKitJsonBuilder AddJsonSerializationContribution(
        JsonSerializationProfileRef profileReference,
        JsonSerializationContribution contribution) =>
        this;

    public IProgramKitJsonRegistry Freeze() =>
        throw new NotSupportedException();
}
