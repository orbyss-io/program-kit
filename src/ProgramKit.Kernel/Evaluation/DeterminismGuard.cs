using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;

namespace Orbyss.ProgramKit.Kernel.Evaluation;

public static class DeterminismGuard
{
    public static void EnsureCompatibleWithAdmittedCanonicalBytes(string workspaceRoot, CandidateArtifactSet candidate)
    {
        string receiptPath = Path.Combine(workspaceRoot, ".program-kit", "construction-receipt.json");
        string manifestPath = Path.Combine(workspaceRoot, ".program-kit", "artifact-manifest.json");
        if (!File.Exists(receiptPath) || !File.Exists(manifestPath))
        {
            return;
        }

        JsonObject receipt = CanonicalJson.Parse(File.ReadAllBytes(receiptPath)) as JsonObject
            ?? throw new InvalidDataException("The admitted receipt must be an object.");
        if (!string.Equals(receipt["constructionIdentity"]?.GetValue<string>(), candidate.ConstructionIdentity, StringComparison.Ordinal))
        {
            return;
        }

        JsonObject manifest = CanonicalJson.Parse(File.ReadAllBytes(manifestPath)) as JsonObject
            ?? throw new InvalidDataException("The admitted artifact manifest must be an object.");
        string[] admitted = (manifest["artifacts"] as JsonArray ?? new JsonArray())
            .OfType<JsonObject>()
            .Where(static artifact => string.Equals(artifact["claimClass"]?.GetValue<string>(), "canonical-byte", StringComparison.Ordinal))
            .Select(static artifact => $"{artifact["logicalPath"]!.GetValue<string>()}:{artifact["digest"]!.GetValue<string>()}")
            .OrderBy(static value => value, StringComparer.Ordinal)
            .ToArray();
        string[] proposed = candidate.Artifacts
            .Where(static artifact => artifact.ClaimClass == ClaimClass.CanonicalByte)
            .Select(static artifact => $"{artifact.LogicalPath}:{artifact.Digest}")
            .OrderBy(static value => value, StringComparer.Ordinal)
            .ToArray();
        if (!admitted.SequenceEqual(proposed, StringComparer.Ordinal))
        {
            throw new ProgramKitDiagnosticException(
                DiagnosticIds.DeterminismMismatch,
                OperationPhase.Evaluation,
                PrimaryDisposition.Stop,
                "Equal construction identities produced different Program Kit-owned canonical bytes.");
        }
    }
}
