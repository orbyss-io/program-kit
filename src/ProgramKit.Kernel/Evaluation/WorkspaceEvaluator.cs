using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Evaluation;

public sealed record ArtifactObservation(string LogicalPath, string ExpectedDigest, string? ObservedDigest, string State, string Ownership);

public sealed record WorkspaceEvaluation(
    IReadOnlyList<ArtifactObservation> Artifacts,
    string LiveStateDigest,
    string EvidenceDigest,
    bool SupportAvailable,
    bool ReceiptAvailable,
    bool Interrupted);

public sealed class WorkspaceEvaluator
{
    public IReadOnlyList<ArtifactObservation> Evaluate(string workspaceRoot, JsonObject receipt) =>
        EvaluateDetailed(workspaceRoot, receipt).Artifacts;

    public WorkspaceEvaluation EvaluateDetailed(string workspaceRoot, JsonObject receipt)
    {
        if (receipt["artifacts"] is not JsonArray artifacts)
        {
            throw new InvalidDataException("The admission receipt contains no artifact manifest.");
        }

        string freshness = receipt["support"]?["evidenceFreshness"]?.GetValue<string>() ?? "unavailable";
        bool supportAvailable = freshness == "current";
        List<ArtifactObservation> observations = new();
        foreach (JsonNode? node in artifacts)
        {
            JsonObject entry = node as JsonObject ?? throw new InvalidDataException("Invalid receipt artifact entry.");
            JsonObject artifact = entry["artifact"] as JsonObject ?? throw new InvalidDataException("Receipt artifact reference is missing.");
            string logicalPath = Required(artifact, "logicalPath");
            string expected = Required(artifact, "digest");
            string ownership = Required(artifact, "ownership");
            string path;
            try
            {
                path = LogicalPaths.ResolveInside(workspaceRoot, logicalPath);
            }
            catch (Exception exception) when (exception is ArgumentException or InvalidOperationException)
            {
                observations.Add(new ArtifactObservation(logicalPath, expected, null, "unavailable", ownership));
                continue;
            }

            if (!File.Exists(path))
            {
                observations.Add(new ArtifactObservation(logicalPath, expected, null, "missing", ownership));
                continue;
            }

            if ((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            {
                observations.Add(new ArtifactObservation(logicalPath, expected, null, "unavailable", ownership));
                continue;
            }

            string observed = Digests.Sha256(File.ReadAllBytes(path));
            string state = !string.Equals(freshness, "current", StringComparison.Ordinal)
                ? freshness is "stale" or "expired" ? "stale" : "unsupported"
                : string.Equals(expected, observed, StringComparison.Ordinal)
                    ? "exact"
                    : ownership == "generated-owned" ? "modified" : "colliding";
            observations.Add(new ArtifactObservation(logicalPath, expected, observed, state, ownership));
        }

        string journalPath = Path.Combine(workspaceRoot, ".program-kit", "publication.journal.json");
        bool interrupted = false;
        if (File.Exists(journalPath))
        {
            JsonObject journal = CanonicalJson.Parse(File.ReadAllBytes(journalPath)) as JsonObject
                ?? throw new InvalidDataException("The publication journal is invalid.");
            interrupted = new Publication.PublicationRecovery().Inspect(workspaceRoot)?.State is "prepared" or "publishing" or "incomplete" or "published-unadmitted";
        }

        string liveState = Publication.LiveState.ComputeObserved(observations.Select(static item => (item.LogicalPath, item.ObservedDigest)));
        string evidence = RecomputeEvidenceDigest(workspaceRoot, receipt);
        return new WorkspaceEvaluation(observations, liveState, evidence, supportAvailable, true, interrupted);
    }

    private static string RecomputeEvidenceDigest(string workspaceRoot, JsonObject receipt)
    {
        List<string> digests = new();
        if (receipt["gateResults"] is JsonArray gates)
        {
            digests.AddRange(gates.OfType<JsonObject>().Select(CanonicalJson.Digest));
        }

        JsonObject? verificationArtifact = (receipt["artifacts"] as JsonArray)?.OfType<JsonObject>()
            .Select(static entry => entry["verification"]?["artifact"] as JsonObject)
            .FirstOrDefault(static artifact => artifact is not null);
        if (verificationArtifact is not null)
        {
            string logicalPath = Required(verificationArtifact, "logicalPath");
            string path = LogicalPaths.ResolveInside(workspaceRoot, logicalPath);
            string expected = Required(verificationArtifact, "digest");
            if (!File.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            {
                digests.Add($"unavailable:{logicalPath}:{expected}");
            }
            else
            {
                byte[] evidenceBytes = File.ReadAllBytes(path);
                string observed = Digests.Sha256(evidenceBytes);
                if (!string.Equals(observed, expected, StringComparison.Ordinal))
                {
                    digests.Add($"changed:{logicalPath}:{observed}");
                }
                else
                {
                    JsonObject evidence = CanonicalJson.Parse(evidenceBytes) as JsonObject
                        ?? throw new InvalidDataException("Candidate evaluation evidence is invalid.");
                    foreach (string section in new[] { "construction", "evaluation" })
                    {
                        if (evidence[section] is JsonArray records)
                        {
                            digests.AddRange(records.OfType<JsonObject>().Select(CanonicalJson.Digest));
                        }
                    }
                }
            }
        }

        return Digests.Sha256(System.Text.Encoding.UTF8.GetBytes(string.Join('\n', digests.OrderBy(static value => value, StringComparer.Ordinal))));
    }

    private static string Required(JsonObject parent, string name) =>
        parent[name]?.GetValue<string>() is { Length: > 0 } value
            ? value
            : throw new InvalidDataException($"Receipt artifact {name} is missing.");
}
