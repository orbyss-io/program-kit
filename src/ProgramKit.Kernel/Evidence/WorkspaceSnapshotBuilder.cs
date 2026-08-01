using System;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Resolution;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Evidence;

public static class WorkspaceSnapshotBuilder
{
    public static JsonObject Build(ResolutionLock resolution, CandidateArtifactSet candidate, string evidenceDigest) => new()
    {
        ["schema"] = "program-kit.workspace-snapshot/v1",
        ["canonicalProfile"] = CanonicalJson.Profile,
        ["rootBundle"] = new JsonObject
        {
            ["identity"] = new JsonObject
            {
                ["authority"] = resolution.RootBundle.Identity.Authority,
                ["kind"] = resolution.RootBundle.Identity.Kind,
                ["name"] = resolution.RootBundle.Identity.Name,
                ["revision"] = resolution.RootBundle.Identity.Revision,
                ["digest"] = resolution.RootBundle.Identity.Digest,
            },
            ["mediaType"] = resolution.RootBundle.MediaType,
            ["logicalPath"] = resolution.RootBundle.LogicalPath,
            ["digest"] = resolution.RootBundle.Digest,
            ["ownership"] = "consumer-owned",
        },
        ["closureDigest"] = resolution.ClosureDigest,
        ["evidenceDigest"] = evidenceDigest,
        ["constructionIdentity"] = candidate.ConstructionIdentity,
        ["freshness"] = "current",
        ["identities"] = new JsonArray(),
        ["semanticCoverage"] = new JsonArray(),
        ["bindings"] = new JsonArray(),
        ["selections"] = new JsonArray(),
        ["relationships"] = new JsonArray(),
        ["seams"] = new JsonArray(),
        ["artifacts"] = new JsonArray(candidate.Artifacts.Select(static artifact => new JsonObject
        {
            ["logicalPath"] = artifact.LogicalPath,
            ["ownership"] = Kebab(artifact.Ownership),
            ["producer"] = artifact.ProducerIdentity,
            ["digest"] = artifact.Digest,
            ["claimClass"] = Kebab(artifact.ClaimClass),
            ["state"] = "exact",
        }).ToArray()),
        ["provenance"] = new JsonArray(),
        ["gates"] = new JsonArray("exact-resolution:passed", "ownership:passed", "publication:passed"),
        ["reviews"] = new JsonArray(),
        ["waivers"] = new JsonArray(),
        ["evidence"] = new JsonArray(evidenceDigest),
        ["receipts"] = new JsonArray(),
        ["support"] = new JsonArray("dotnet10-cshells-0.0.28:supported"),
        ["retention"] = new JsonArray("local-workspace"),
        ["diagnosticState"] = new JsonObject
        {
            ["outcome"] = "succeeded",
            ["effect"] = "committed",
            ["disposition"] = "complete",
            ["collectionDigest"] = Digests.Sha256(Array.Empty<byte>()),
            ["unresolvedCount"] = 0,
            ["redactedCount"] = 0,
        },
        ["trace"] = new JsonArray(".program-kit/resolution.lock.json", ".program-kit/artifact-manifest.json"),
        ["limitations"] = new JsonArray("Custom behavior requires source inspection for debugging", "No runtime-state inference"),
    };

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
