namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>One owner-defined typed configuration property.</summary>
public sealed record DotNetConfigurationProperty(
    [property: JsonPropertyName("propertyName")] string PropertyName,
    [property: JsonPropertyName("key")] string Key,
    [property: JsonPropertyName("valueKind")] DotNetConfigurationValueKind ValueKind,
    [property: JsonPropertyName("required")] bool Required,
    [property: JsonPropertyName("defaultValue")] string? DefaultValue,
    [property: JsonPropertyName("exampleValue")] string? ExampleValue,
    [property: JsonPropertyName("classification")] DotNetConfigurationValueClassification Classification,
    [property: JsonPropertyName("validation")] DotNetConfigurationPropertyValidation Validation);
