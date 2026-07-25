namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Typed Options binding and lifetime intent required by one generated host.</summary>
public sealed record DotNetConfigurationBinding(
    [property: JsonPropertyName("definition")] DotNetConfigurationDefinition Definition,
    [property: JsonPropertyName("optionsName")] string OptionsName,
    [property: JsonPropertyName("sourceIdentities")] ImmutableArray<ProgramKitIdentifier> SourceIdentities,
    [property: JsonPropertyName("consumption")] DotNetOptionsConsumption Consumption,
    [property: JsonPropertyName("consumerLifetime")] DotNetServiceLifetime ConsumerLifetime,
    [property: JsonPropertyName("validateOnStart")] bool ValidateOnStart,
    [property: JsonPropertyName("securityCritical")] bool SecurityCritical,
    [property: JsonPropertyName("changeReaction")] DotNetConfigurationChangeReaction ChangeReaction,
    [property: JsonPropertyName("restartRequired")] bool RestartRequired);
