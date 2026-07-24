using Orbyss.ProgramKit.DotNet.Packages;

namespace Orbyss.ProgramKit.DotNet.Shells;

/// <summary>Exact concrete feature package and activation selected by a shell.</summary>
public sealed record DotNetFeatureSelection(
    [property: JsonPropertyName("featureIdentity")] ProgramKitIdentifier FeatureIdentity,
    [property: JsonPropertyName("activationIdentity")] ProgramKitIdentifier ActivationIdentity,
    [property: JsonPropertyName("shellIdentity")] ProgramKitIdentifier ShellIdentity,
    [property: JsonPropertyName("featureTypeName")] string FeatureTypeName,
    [property: JsonPropertyName("package")] DotNetPackageReference Package);
