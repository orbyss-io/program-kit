namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Closed structural validation rules whose meaning remains definition-owner supplied.</summary>
public sealed record DotNetConfigurationPropertyValidation(
    [property: JsonPropertyName("minimumLength")] int? MinimumLength,
    [property: JsonPropertyName("maximumLength")] int? MaximumLength,
    [property: JsonPropertyName("minimumValue")] string? MinimumValue,
    [property: JsonPropertyName("maximumValue")] string? MaximumValue,
    [property: JsonPropertyName("regularExpression")] string? RegularExpression);
