using Orbyss.ProgramKit.DotNet.Packages;

namespace Orbyss.ProgramKit.DotNet.Configuration.Azure;

/// <summary>Exact reviewed Azure configuration provider descriptors.</summary>
public static class DotNetAzureConfigurationProviderCatalog
{
    private const string GeneratorDigest =
        "sha256:a405b64ffe3704b4233ab03d87551bc9bda960eaa21d297b8350d6233e6e8b43";

    /// <summary>Azure Key Vault configuration provider 1.5.1.</summary>
    public static DotNetConfigurationProviderDescriptor KeyVault { get; } =
        Descriptor(
            "azure-key-vault",
            "1.5.1",
            "Azure.Extensions.AspNetCore.Configuration.Secrets",
            "49d51e8fb944bb9614ef180d685a1d4e41d81691ae1290bc981aeeccb684a7f8",
            "8141fd68f373066014025ebc149658cf088f30747c523f2871d96235256396a9",
            [DotNetConfigurationReloadCapability.None, DotNetConfigurationReloadCapability.ProviderPolling],
            DotNetConfigurationReloadMechanism.ProviderPollingChangeToken,
            [
                "ReloadInterval polls Key Vault; null disables automatic reload.",
                "startup and provider polling require the externally supplied TokenCredential to remain usable",
                "disabled secrets are not loaded; generated active-secret filtering excludes expired and not-yet-valid secrets",
            ]);

    /// <summary>All Azure adapter descriptors in deterministic order.</summary>
    public static ImmutableArray<DotNetConfigurationProviderDescriptor> Descriptors { get; } =
        [KeyVault];

    private static DotNetConfigurationProviderDescriptor Descriptor(
        string name,
        string version,
        string packageId,
        string packageDigest,
        string assemblyDigest,
        ImmutableArray<DotNetConfigurationReloadCapability> reload,
        DotNetConfigurationReloadMechanism mechanism,
        ImmutableArray<string> limitations) =>
        new(
            new ArtifactReference(
                new ProgramKitIdentifier(
                    string.Concat("pkid:provider:program-kit:", name)),
                new SemanticVersion(version),
                new Sha256Digest(string.Concat("sha256:", assemblyDigest))),
            DotNetConfigurationProviderKind.RegisteredAdapter,
            new DotNetPackageReference(
                packageId,
                new SemanticVersion(version),
                new Sha256Digest(string.Concat("sha256:", packageDigest))),
            new ArtifactReference(
                new ProgramKitIdentifier(
                    "pkid:generator:program-kit:dotnet-azure-configuration"),
                new SemanticVersion("1.0.0"),
                new Sha256Digest(GeneratorDigest)),
            reload,
            mechanism,
            false,
            [
                DotNetConfigurationSecretClassification.ReferencesOnly,
                DotNetConfigurationSecretClassification.ProviderOwned,
            ],
            limitations);
}
