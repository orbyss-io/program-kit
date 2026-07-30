using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.OpenConsole.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>
/// Consumer-owned semantic selections from which Program Kit may derive only
/// project mechanics and exact operation schema-set mirrors.
/// </summary>
public sealed record DotNetConsoleCommandSketch(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("contractStyle")] string ContractStyle,
    [property: JsonPropertyName("identity")] ProgramKitIdentifier Identity,
    [property: JsonPropertyName("ownerIdentity")] ProgramKitIdentifier OwnerIdentity,
    [property: JsonPropertyName("outputSetIdentity")]
    ProgramKitIdentifier OutputSetIdentity,
    [property: JsonPropertyName("hostIdentity")]
    ProgramKitIdentifier HostIdentity,
    [property: JsonPropertyName("consumerProjectIdentity")]
    ProgramKitIdentifier ConsumerProjectIdentity,
    [property: JsonPropertyName("configuration")] string Configuration,
    [property: JsonPropertyName("platform")] string Platform,
    [property: JsonPropertyName("shell")] DotNetShellDocument Shell,
    [property: JsonPropertyName("openConsole")]
    DotNetConsoleOpenConsoleSketch OpenConsole,
    [property: JsonPropertyName("binding")] DotNetConsoleBindingIntent Binding,
    [property: JsonPropertyName("suppliedArtifacts")]
    ImmutableArray<DotNetConsoleSuppliedArtifact> SuppliedArtifacts);
