using System;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Contracts.Diagnostics;

public static class DiagnosticCatalogArtifacts
{
    public const string KernelDigest = "sha256:113c041abed194a27c9b7768c28ce45f1ca4ee2f00fc03c08f1f48d5a3955aa7";
    public const string DotNetDigest = "sha256:221d2ad99101f09a44178364d0638d6b1d9890d8a475980b803da6fa0cb51376";

    public static GovernedIdentity KernelIdentity { get; } = new(
        "orbyss.program-kit", "diagnostic-catalog", "kernel", "1.0.0", KernelDigest);

    public static GovernedIdentity DotNetIdentity { get; } = new(
        "orbyss.program-kit.dotnet", "diagnostic-catalog", "provider", "1.0.0", DotNetDigest);

    public static ArtifactReference KernelArtifact { get; } = Artifact(
        KernelIdentity, "artifacts/evidence/kernel-diagnostic-catalog.json");

    public static ArtifactReference DotNetArtifact { get; } = Artifact(
        DotNetIdentity, "artifacts/evidence/dotnet-diagnostic-catalog.json");

    public static GovernedIdentity IdentityFor(string diagnosticId) =>
        IsDotNet(diagnosticId) ? DotNetIdentity : KernelIdentity;

    public static ArtifactReference ArtifactFor(string diagnosticId) =>
        IsDotNet(diagnosticId) ? DotNetArtifact : KernelArtifact;

    public static EvidenceReference EvidenceFor(string diagnosticId)
    {
        GovernedIdentity catalog = IdentityFor(diagnosticId);
        ArtifactReference artifact = ArtifactFor(diagnosticId);
        return new EvidenceReference(
            Exact(catalog.Authority, "diagnostic-definition-evidence", diagnosticId.Replace('/', '-'), "1.0.0", $"{diagnosticId}\n{catalog.Digest}"),
            catalog,
            ProtocolIdentities.Rule("diagnostic-contract"),
            artifact,
            "current");
    }

    private static bool IsDotNet(string diagnosticId) =>
        diagnosticId.StartsWith("program-kit.provider.dotnet/", StringComparison.Ordinal);

    private static ArtifactReference Artifact(GovernedIdentity identity, string logicalPath) =>
        new(identity, "application/json", logicalPath, identity.Digest, ArtifactOwnership.GeneratedOwned);

    private static GovernedIdentity Exact(string authority, string kind, string name, string revision, string material)
    {
        string digest = $"sha256:{Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(material))).ToLowerInvariant()}";
        return new GovernedIdentity(authority, kind, name, revision, digest);
    }
}
