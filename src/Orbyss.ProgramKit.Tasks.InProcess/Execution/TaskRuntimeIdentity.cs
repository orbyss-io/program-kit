using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.InProcess.Execution;

internal static class TaskRuntimeIdentity
{
    internal static ArtifactReference Create(
        string kind,
        ArtifactReference parent,
        string discriminator)
    {
        var bytes = Encoding.UTF8.GetBytes(
            string.Join(
                "\n",
                kind,
                parent.Identity.Value,
                parent.Version.Value,
                parent.Digest.Value,
                discriminator));
        var digestHex = Convert.ToHexStringLower(SHA256.HashData(bytes));
        return new ArtifactReference(
            ProgramKitIdentifier.Parse(
                $"pkid:{kind}:program-kit:{digestHex}"),
            parent.Version,
            Sha256Digest.Parse($"sha256:{digestHex}"));
    }
}
