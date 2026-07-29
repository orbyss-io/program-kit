using Orbyss.ProgramKit.DotNet.Shells;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>
/// Complete consumer-owned semantic input for deterministic Console generation
/// input materialization.
/// </summary>
public sealed record DotNetConsoleInputMaterializationRequest(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("identity")] ProgramKitIdentifier Identity,
    [property: JsonPropertyName("ownerIdentity")] ProgramKitIdentifier OwnerIdentity,
    [property: JsonPropertyName("outputSetIdentity")]
    ProgramKitIdentifier OutputSetIdentity,
    [property: JsonPropertyName("hostIdentity")]
    ProgramKitIdentifier HostIdentity,
    [property: JsonPropertyName("consumerProjectPath")]
    string ConsumerProjectPath,
    [property: JsonPropertyName("consumerProjectIdentity")]
    ProgramKitIdentifier ConsumerProjectIdentity,
    [property: JsonPropertyName("consumerProjectName")]
    string ConsumerProjectName,
    [property: JsonPropertyName("targetFramework")] string TargetFramework,
    [property: JsonPropertyName("configuration")] string Configuration,
    [property: JsonPropertyName("platform")] string Platform,
    [property: JsonPropertyName("shell")] DotNetShellDocument Shell,
    [property: JsonPropertyName("openConsole")]
    DotNetConsoleOpenConsoleIntent OpenConsole,
    [property: JsonPropertyName("binding")] DotNetConsoleBindingIntent Binding,
    [property: JsonPropertyName("suppliedArtifacts")]
    ImmutableArray<DotNetConsoleSuppliedArtifact> SuppliedArtifacts);
