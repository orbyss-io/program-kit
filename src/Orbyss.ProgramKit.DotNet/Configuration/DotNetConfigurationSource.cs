using Orbyss.ProgramKit.DotNet.Packages;

namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>One explicitly ordered configuration-provider binding.</summary>
public sealed record DotNetConfigurationSource(
    [property: JsonPropertyName("identity")] ProgramKitIdentifier Identity,
    [property: JsonPropertyName("order")] int Order,
    [property: JsonPropertyName("providerKind")] DotNetConfigurationProviderKind ProviderKind,
    [property: JsonPropertyName("providerRevision")] ArtifactReference ProviderRevision,
    [property: JsonPropertyName("package")] DotNetPackageReference Package,
    [property: JsonPropertyName("path")] string? Path,
    [property: JsonPropertyName("prefix")] string? Prefix,
    [property: JsonPropertyName("optional")] bool Optional,
    [property: JsonPropertyName("startupDisposition")] DotNetConfigurationStartupDisposition StartupDisposition,
    [property: JsonPropertyName("reload")] DotNetConfigurationReload Reload,
    [property: JsonPropertyName("secretClassification")] DotNetConfigurationSecretClassification SecretClassification,
    [property: JsonPropertyName("failureDisposition")] DotNetConfigurationFailureDisposition FailureDisposition);
