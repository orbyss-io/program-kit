using System.Collections.Immutable;
using System.Text.Json.Serialization.Metadata;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class StubProgramKitJsonRegistry : IProgramKitJsonRegistry
{
    public ImmutableArray<JsonSerializationProfile> Profiles => [];

    public ImmutableArray<JsonSerializationProfileSelection> Selections => [];

    public JsonSerializationProfile GetProfile(
        JsonSerializationProfileRef profileReference) =>
        throw new NotSupportedException();

    public JsonTypeInfo<T> GetTypeInfo<T>(
        JsonSerializationProfileRef profileReference) =>
        throw new NotSupportedException();
}
