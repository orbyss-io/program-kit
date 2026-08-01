using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Evaluation;

public sealed record ArtifactObservation(string LogicalPath, string ExpectedDigest, string? ObservedDigest, string State, string Ownership);

public sealed class WorkspaceEvaluator
{
    public IReadOnlyList<ArtifactObservation> Evaluate(string workspaceRoot, JsonObject receipt)
    {
        if (receipt["artifacts"] is not JsonArray artifacts)
        {
            throw new InvalidDataException("The admission receipt contains no artifact manifest.");
        }

        List<ArtifactObservation> observations = new();
        foreach (JsonNode? node in artifacts)
        {
            JsonObject artifact = node as JsonObject ?? throw new InvalidDataException("Invalid receipt artifact entry.");
            string logicalPath = artifact["logicalPath"]?.GetValue<string>() ?? throw new InvalidDataException("Receipt artifact path is missing.");
            string expected = artifact["digest"]?.GetValue<string>() ?? throw new InvalidDataException("Receipt artifact digest is missing.");
            string ownership = artifact["ownership"]?.GetValue<string>() ?? "Unknown";
            string path = Path.GetFullPath(Path.Combine(workspaceRoot, logicalPath.Replace('/', Path.DirectorySeparatorChar)));
            if (!File.Exists(path))
            {
                observations.Add(new ArtifactObservation(logicalPath, expected, null, "missing", ownership));
                continue;
            }

            string observed = Digests.Sha256(File.ReadAllBytes(path));
            observations.Add(new ArtifactObservation(logicalPath, expected, observed, string.Equals(expected, observed, StringComparison.Ordinal) ? "exact" : "modified", ownership));
        }

        return observations;
    }
}
