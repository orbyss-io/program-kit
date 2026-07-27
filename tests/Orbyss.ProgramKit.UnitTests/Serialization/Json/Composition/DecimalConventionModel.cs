using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed record DecimalConventionModel(
    [property: JsonPropertyName("amount")] decimal Amount);
