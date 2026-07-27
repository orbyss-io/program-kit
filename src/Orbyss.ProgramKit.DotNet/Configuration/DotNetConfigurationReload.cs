namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Declared reload mechanics and provider capability.</summary>
public sealed record DotNetConfigurationReload(
    [property: JsonPropertyName("enabled")] bool Enabled,
    [property: JsonPropertyName("capability")] DotNetConfigurationReloadCapability Capability,
    [property: JsonPropertyName("pollIntervalSeconds")] int? PollIntervalSeconds,
    [property: JsonPropertyName("refreshRevision")] ArtifactReference? RefreshRevision);
