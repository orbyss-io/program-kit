using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Publication;

namespace Orbyss.ProgramKit.Kernel.Operations;

internal static class PublicationRepairGuidance
{
    public static Remediation RecoveryRemediation(JsonObject repairRequest) => new(
        "repair",
        new[] { ".program-kit/publication.journal.json" },
        new[] { "exact-incomplete-journal", "fresh-evaluation", "exact-authority-required" },
        RequestedEffect.Committed,
        new[] { "human-approved-repository-record" },
        repairRequest,
        null,
        new[] { "publication-recovered-before-reconstruction", "no-state-trusted-without-final-receipt" },
        OperationPhase.Publication);

    public static string ObservedPublicationLiveState(string workspaceRoot)
    {
        string journalPath = Path.Combine(workspaceRoot, ".program-kit", "publication.journal.json");
        JsonObject journal = CanonicalJson.Parse(File.ReadAllBytes(journalPath)) as JsonObject
            ?? throw new InvalidDataException("The publication journal is invalid.");
        JsonArray operations = journal["operations"] as JsonArray
            ?? throw new InvalidDataException("The publication journal operations are unavailable.");
        var observations = operations.OfType<JsonObject>()
            .Select(operation =>
            {
                string logicalPath = operation["logicalPath"]?.GetValue<string>()
                    ?? throw new InvalidDataException("A publication operation has no logical path.");
                string path = LogicalPaths.ResolveInside(workspaceRoot, logicalPath);
                string? digest = File.Exists(path) && (File.GetAttributes(path) & FileAttributes.ReparsePoint) == 0
                    ? Digests.Sha256(File.ReadAllBytes(path))
                    : null;
                return (LogicalPath: logicalPath, Digest: digest);
            })
            .OrderBy(static item => item.LogicalPath, StringComparer.Ordinal)
            .ToArray();
        return LiveState.ComputeObserved(observations);
    }
}
