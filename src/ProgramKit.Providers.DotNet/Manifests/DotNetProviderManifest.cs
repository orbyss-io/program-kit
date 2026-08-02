using System;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;

namespace Orbyss.ProgramKit.Providers.DotNet.Manifests;

public static class DotNetProviderManifest
{
    public const string StableKey = "orbyss.program-kit.dotnet:factory-provider:dotnet-cshells@1.0.0";
    public const string Profile = "dotnet10-cshells-0.0.28";
    public const string SupportDigest = "sha256:5106ae49249752d98185e2ab0ff116cebe7e3467be0740656c1c01d2f03e7d16";

    public static ProviderManifest Create()
    {
        string digest = Digest("dotnet10-cshells-0.0.28@29fe542835696131278fcacc6cdb9a6186fc0447");
        GovernedIdentity provider = new("orbyss.program-kit.dotnet", "factory-provider", "dotnet-cshells", "1.0.0", digest);
        GovernedIdentity distribution = new("orbyss.program-kit.dotnet", "distribution", "dotnet10-cshells", "1.0.0", digest);
        GovernedIdentity profile = Exact("target-profile", Profile, Profile);
        ArtifactReference support = new(
            new GovernedIdentity("orbyss.program-kit.dotnet", "provider-conformance", "dotnet-cshells-support", "1.0.0", SupportDigest),
            "application/json",
            "artifacts/evidence/provider-support.json",
            SupportDigest,
            ArtifactOwnership.GeneratedOwned);
        EvidenceReference conformance = new(
            Exact("provider-conformance-evidence", "dotnet-cshells", $"{provider.Digest}\n{support.Digest}"),
            provider,
            profile,
            support,
            "current");
        return new ProviderManifest(
            provider,
            distribution,
            new[] { ProviderRole.IntakeMapping, ProviderRole.Construction, ProviderRole.Evaluation },
            new[] { Profile },
            new[] { "program-kit.software-definition-bundle/v1", "program-kit.provider.dotnet.component-api-definition/v1" },
            new[] { "dotnet-component-package", "aspnetcore-application" },
            new[] { "dotnet restore", "dotnet build", "dotnet pack" },
            new[] { "read-workspace", "write-candidate", "write-local-package-source" },
            DiagnosticCatalogArtifacts.DotNetArtifact,
            new[] { conformance });
    }

    private static GovernedIdentity Exact(string kind, string name, string material) =>
        new("orbyss.program-kit.dotnet", kind, name, "1.0.0", Digest(material));

    private static string Digest(string material) =>
        $"sha256:{Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(material))).ToLowerInvariant()}";
}
