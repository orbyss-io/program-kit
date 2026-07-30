using Orbyss.ProgramKit.DotNet.Shells;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>
/// Current alpha Console input request with explicit operation schema sets.
/// </summary>
public sealed record DotNetConsoleInputMaterializationRequestAlpha2(
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
    DotNetConsoleOpenConsoleIntentAlpha2 OpenConsole,
    [property: JsonPropertyName("binding")] DotNetConsoleBindingIntent Binding,
    [property: JsonPropertyName("suppliedArtifacts")]
    ImmutableArray<DotNetConsoleSuppliedArtifact> SuppliedArtifacts)
{
    /// <summary>
    /// Projects a validated alpha.2 request into the immutable alpha.1 reader
    /// shape used internally by the materialization implementation.
    /// </summary>
    public DotNetConsoleInputMaterializationRequest ToAlpha1Reader() =>
        new(
            "pkid:schema:program-kit:dotnet-console-input-materialization-request@0.1.0-alpha.1",
            new SemanticVersion("0.1.0-alpha.1"),
            Identity,
            OwnerIdentity,
            OutputSetIdentity,
            HostIdentity,
            ConsumerProjectPath,
            ConsumerProjectIdentity,
            ConsumerProjectName,
            TargetFramework,
            Configuration,
            Platform,
            Shell,
            OpenConsole.ToVersion1(),
            Binding,
            SuppliedArtifacts);
}
