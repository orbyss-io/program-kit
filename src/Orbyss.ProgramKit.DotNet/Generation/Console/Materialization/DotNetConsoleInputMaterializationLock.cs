namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>
/// Exact ownership and freshness evidence for one materialized Console input
/// directory.
/// </summary>
public sealed record DotNetConsoleInputMaterializationLock(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("programKitVersion")]
    SemanticVersion ProgramKitVersion,
    [property: JsonPropertyName("requestDigest")] Sha256Digest RequestDigest,
    [property: JsonPropertyName("workspaceRootRelativePath")]
    string WorkspaceRootRelativePath,
    [property: JsonPropertyName("consumerProjectPath")]
    string ConsumerProjectPath,
    [property: JsonPropertyName("targetFramework")] string TargetFramework,
    [property: JsonPropertyName("configuration")] string Configuration,
    [property: JsonPropertyName("platform")] string Platform,
    [property: JsonPropertyName("buildArguments")]
    ImmutableArray<string> BuildArguments,
    [property: JsonPropertyName("consumerReference")]
    DotNetConsoleMaterializedReference ConsumerReference,
    [property: JsonPropertyName("compilationReferences")]
    ImmutableArray<DotNetConsoleMaterializedReference> CompilationReferences,
    [property: JsonPropertyName("manifestDigest")]
    Sha256Digest ManifestDigest,
    [property: JsonPropertyName("outputs")]
    ImmutableArray<DotNetConsoleMaterializedOutput> Outputs);
