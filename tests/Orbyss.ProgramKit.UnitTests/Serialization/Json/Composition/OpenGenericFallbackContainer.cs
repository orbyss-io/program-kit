using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed record OpenGenericFallbackContainer<TValue>(
    [property: JsonPropertyName("items")] List<TValue> Items);
