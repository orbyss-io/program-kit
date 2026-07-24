namespace Orbyss.ProgramKit.DotNet.Targeting;

/// <summary>Exact .NET 10 target profile materialized into a host lock.</summary>
public sealed record DotNetTargetLock(
    [property: JsonPropertyName("profileRevision")] ArtifactReference ProfileRevision,
    [property: JsonPropertyName("sdkVersion")] string SdkVersion,
    [property: JsonPropertyName("targetFramework")] string TargetFramework,
    [property: JsonPropertyName("languageVersion")] string LanguageVersion,
    [property: JsonPropertyName("rollForward")] string RollForward,
    [property: JsonPropertyName("allowPrerelease")] bool AllowPrerelease);
