namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>One explicit secret-free value for an in-memory provider boundary.</summary>
public sealed record DotNetConfigurationInitialValue(
    [property: JsonPropertyName("key")] string Key,
    [property: JsonPropertyName("value")] string Value,
    [property: JsonPropertyName("classification")] DotNetConfigurationValueClassification Classification);
