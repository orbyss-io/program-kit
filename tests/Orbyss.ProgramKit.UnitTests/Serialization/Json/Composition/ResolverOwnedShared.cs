using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed record ResolverOwnedShared(
    [property: JsonPropertyName("value")] string Value);
