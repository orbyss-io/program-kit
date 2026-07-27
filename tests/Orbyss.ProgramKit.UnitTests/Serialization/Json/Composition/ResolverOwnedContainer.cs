using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed record ResolverOwnedContainer(
    [property: JsonPropertyName("shared")] ResolverOwnedShared Shared);
