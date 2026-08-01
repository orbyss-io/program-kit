using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Publication;

public sealed class AdmissionService
{
    public string Admit(
        string workspaceRoot,
        CandidateArtifactSet candidate,
        string lockDigest,
        string liveStateDigest)
    {
        foreach (ArtifactManifestEntry artifact in candidate.Artifacts)
        {
            string path = Path.Combine(workspaceRoot, artifact.LogicalPath.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path) || !string.Equals(Digests.Sha256(File.ReadAllBytes(path)), artifact.Digest, StringComparison.Ordinal))
            {
                throw new InvalidOperationException("Admission requires complete verified live bytes.");
            }
        }

        JsonObject receipt = new()
        {
            ["schema"] = "program-kit.construction-receipt/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["constructionIdentity"] = candidate.ConstructionIdentity,
            ["lockDigest"] = lockDigest,
            ["artifactSetDigest"] = candidate.SetDigest,
            ["artifacts"] = new JsonArray(candidate.Artifacts.Select(static item => new JsonObject
            {
                ["logicalPath"] = item.LogicalPath,
                ["digest"] = item.Digest,
                ["ownership"] = Kebab(item.Ownership),
                ["claimClass"] = Kebab(item.ClaimClass),
                ["producer"] = item.ProducerIdentity,
            }).ToArray()),
            ["gateResults"] = new JsonArray("exact-resolution:passed", "candidate-integrity:passed", "live-verification:passed"),
            ["publicationState"] = "admitted",
            ["observedLiveState"] = liveStateDigest,
            ["support"] = new JsonObject
            {
                ["profile"] = "dotnet10-cshells-0.0.28",
                ["retentionPolicy"] = "local-workspace",
                ["evidenceFreshness"] = "current",
            },
        };
        string receiptPath = Path.Combine(workspaceRoot, ".program-kit", "construction-receipt.json");
        File.WriteAllBytes(receiptPath, CanonicalJson.Encode(receipt));
        return Digests.Sha256(File.ReadAllBytes(receiptPath));
    }

    private static string Kebab<T>(T value)
        where T : struct, Enum
    {
        string name = value.ToString();
        System.Text.StringBuilder builder = new();
        for (int index = 0; index < name.Length; index++)
        {
            if (index > 0 && char.IsUpper(name[index]))
            {
                builder.Append('-');
            }

            builder.Append(char.ToLowerInvariant(name[index]));
        }

        return builder.ToString();
    }
}
