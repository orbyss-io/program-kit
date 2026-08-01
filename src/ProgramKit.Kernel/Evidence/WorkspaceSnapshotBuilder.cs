using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Authority;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Evaluation;
using Orbyss.ProgramKit.Kernel.Publication;
using Orbyss.ProgramKit.Kernel.Resolution;

namespace Orbyss.ProgramKit.Kernel.Evidence;

public static class WorkspaceSnapshotBuilder
{
    public static JsonObject Build(
        string workspaceRoot,
        ResolvedFactoryInput resolved,
        CandidateArtifactSet candidate,
        CandidateEvaluation evaluation,
        AuthorityDecision authority,
        PreparedAdmission admission,
        string diagnosticCollectionDigest)
    {
        ExactSelection profileSelection = resolved.Input.Request.Selections.Single(static selection => selection.Role == "target-profile");
        GovernedIdentity candidateIdentity = new(
            "orbyss.program-kit",
            "candidate-artifact-set",
            candidate.ConstructionIdentity["sha256:".Length..20],
            "1",
            candidate.SetDigest);
        EvidenceReference evidenceReference = new(
            ContractJson.StableIdentity("orbyss.program-kit", "candidate-evaluation", candidate.ConstructionIdentity["sha256:".Length..20], "1", evaluation.EvidenceDigest),
            candidateIdentity,
            profileSelection.Selected,
            evaluation.EvidenceArtifact,
            "current");
        JsonObject explanation = resolved.Explanation.CanonicalDocument;
        JsonArray semanticCoverage = CloneArray(explanation, "semanticCoverage");
        JsonArray relationships = SnapshotRelationships(resolved.Lock.Relationships);
        JsonArray seams = SnapshotSeams(CloneArray(explanation, "seams"));
        JsonArray trace = CloneArray(explanation, "trace");
        GovernedIdentity contract = relationships.OfType<JsonObject>().FirstOrDefault()?["contract"] is JsonObject contractDocument
            ? BindIdentity(contractDocument)
            : resolved.Input.Request.RootBundle.Identity;

        JsonArray identities = new(
            resolved.Lock.ResolvedItems.Select(static item => ContractJson.Identity(item.Identity))
                .Append(ContractJson.Identity(resolved.Input.Request.RootBundle.Identity))
                .Append(ContractJson.Identity(resolved.ConstructionProvider.Manifest.Identity))
                .Append(ContractJson.Identity(resolved.EvaluationProvider.Manifest.Identity))
                .Append(ContractJson.Identity(profileSelection.Selected))
                .OrderBy(static item => item["authority"]!.GetValue<string>(), StringComparer.Ordinal)
                .ThenBy(static item => item["kind"]!.GetValue<string>(), StringComparer.Ordinal)
                .ThenBy(static item => item["name"]!.GetValue<string>(), StringComparer.Ordinal)
                .ToArray());

        JsonArray artifacts = new(candidate.Artifacts.OrderBy(static artifact => artifact.LogicalPath, StringComparer.Ordinal).Select(artifact =>
        {
            GovernedIdentity identity = new(
                "orbyss.program-kit",
                "generated-artifact",
                artifact.LogicalPath,
                candidate.ConstructionIdentity["sha256:".Length..20],
                artifact.Digest);
            GovernedIdentity producer = ContractJson.StableIdentity("orbyss.program-kit", "producer", SafeName(artifact.ProducerIdentity), "1", artifact.ProducerIdentity);
            return new JsonObject
            {
                ["artifact"] = ContractJson.Artifact(new ArtifactReference(identity, artifact.MediaType, artifact.LogicalPath, artifact.Digest, artifact.Ownership)),
                ["producer"] = ContractJson.Identity(producer),
                ["claimClass"] = ContractJson.Kebab(artifact.ClaimClass),
                ["state"] = "exact",
                ["trace"] = FirstTrace(resolved.Input.Request),
            };
        }).ToArray());
        GovernedIdentity retentionPolicy = ContractJson.StableIdentity("orbyss.program-kit", "retention-policy", "local-workspace", "1.0.0", "local-workspace");
        JsonObject review = new()
        {
            ["identity"] = ContractJson.Identity(authority.Grant.Provenance.Identity),
            ["scope"] = new JsonArray(
                ContractJson.Subject("workspace", resolved.Input.Request.WorkspaceIdentity),
                ContractJson.Subject("root-bundle", resolved.Input.Request.RootBundle.Identity)),
            ["decision"] = "accepted",
            ["authority"] = ContractJson.Identity(authority.Grant.Provider),
            ["evidence"] = new JsonArray(ContractJson.Evidence(evidenceReference)),
        };
        JsonObject diagnosticState = new()
        {
            ["outcome"] = "succeeded",
            ["effect"] = "committed",
            ["disposition"] = "complete",
            ["collectionDigest"] = diagnosticCollectionDigest,
            ["unresolvedCount"] = 0,
            ["redactedCount"] = 0,
        };
        return new JsonObject
        {
            ["schema"] = "program-kit.workspace-snapshot/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["rootBundle"] = ContractJson.Artifact(resolved.Input.Request.RootBundle),
            ["closureDigest"] = resolved.Lock.ClosureDigest,
            ["evidenceDigest"] = evaluation.EvidenceDigest,
            ["constructionIdentity"] = candidate.ConstructionIdentity,
            ["freshness"] = "current",
            ["identities"] = identities,
            ["semanticCoverage"] = semanticCoverage,
            ["bindings"] = new JsonArray(new JsonObject
            {
                ["role"] = "construction-provider",
                ["subject"] = ContractJson.Identity(resolved.Input.Request.RootBundle.Identity),
                ["contract"] = ContractJson.Identity(contract),
                ["implementation"] = ContractJson.Identity(resolved.ConstructionProvider.Manifest.Identity),
                ["profile"] = ContractJson.Identity(profileSelection.Selected),
            }),
            ["selections"] = new JsonArray(resolved.Input.Request.Selections.OrderBy(static item => item.Role, StringComparer.Ordinal).Select(ContractJson.Selection).ToArray()),
            ["relationships"] = relationships,
            ["seams"] = seams,
            ["artifacts"] = artifacts,
            ["provenance"] = new JsonArray(resolved.Input.Inputs.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).Select(ContractJson.Artifact).Prepend(ContractJson.Artifact(resolved.Input.Request.RootBundle)).ToArray()),
            ["gates"] = new JsonArray(evaluation.GateResults.Select(static gate => gate.DeepClone()).ToArray()),
            ["reviews"] = new JsonArray(review),
            ["waivers"] = new JsonArray(),
            ["evidence"] = new JsonArray(ContractJson.Evidence(evidenceReference)),
            ["receipts"] = new JsonArray(ContractJson.Artifact(admission.ReceiptReference)),
            ["support"] = new JsonArray(new JsonObject
            {
                ["subject"] = ContractJson.Identity(resolved.ConstructionProvider.Manifest.Identity),
                ["profile"] = ContractJson.Identity(profileSelection.Selected),
                ["state"] = "supported",
            }),
            ["retention"] = new JsonArray(new JsonObject
            {
                ["subject"] = ContractJson.Identity(admission.ReceiptReference.Identity),
                ["policy"] = ContractJson.Identity(retentionPolicy),
                ["availability"] = "available",
            }),
            ["diagnosticState"] = diagnosticState,
            ["trace"] = trace,
        };
    }

    public static string RecomputeFreshness(
        JsonObject snapshot,
        string closureDigest,
        string evidenceDigest,
        System.Collections.Generic.IReadOnlyList<ArtifactObservation> observations,
        bool supportAvailable,
        bool receiptAvailable,
        bool interrupted)
    {
        if (interrupted)
        {
            return "incomplete";
        }

        if (!receiptAvailable)
        {
            return "unavailable";
        }

        if (!supportAvailable)
        {
            return "unsupported";
        }

        if (observations.Any(static item => item.State is "missing" or "modified" or "colliding"))
        {
            return "drifted";
        }

        return string.Equals(snapshot["closureDigest"]?.GetValue<string>(), closureDigest, StringComparison.Ordinal)
            && string.Equals(snapshot["evidenceDigest"]?.GetValue<string>(), evidenceDigest, StringComparison.Ordinal)
            ? "current"
            : "stale";
    }

    private static JsonArray CloneArray(JsonObject parent, string name) => parent[name] is JsonArray array
        ? new JsonArray(array.Select(static item => item?.DeepClone()).ToArray())
        : throw new InvalidDataException($"The authoritative explanation is missing {name}.");

    private static JsonArray SnapshotRelationships(System.Collections.Generic.IReadOnlyList<Contracts.Resolution.ResolvedRelationship> source) => new(source.Select(item => new JsonObject
    {
        ["assertion"] = ContractJson.Identity(item.Assertion),
        ["from"] = ContractJson.Identity(item.From),
        ["to"] = ContractJson.Identity(item.To),
        ["contract"] = ContractJson.Identity(item.Contract),
        ["status"] = item.Status,
        ["trace"] = new JsonArray(item.Trace.Select(ContractJson.Trace).ToArray()),
    }).ToArray());

    private static JsonArray SnapshotSeams(JsonArray source) => new(source.OfType<JsonObject>().Select(item => new JsonObject
    {
        ["seam"] = item["seam"]?.DeepClone(),
        ["owner"] = item["owner"]?.DeepClone(),
        ["contributions"] = item["contributions"]?.DeepClone(),
        ["status"] = item["status"]?.DeepClone(),
    }).ToArray());

    private static JsonObject FirstTrace(FactoryRequest request) => request.Selections.Select(static item => item.Trace).FirstOrDefault(static item => item is not null) is { } trace
        ? ContractJson.Trace(trace)
        : throw new InvalidOperationException("The exact factory request has no traceable selection.");

    private static GovernedIdentity BindIdentity(JsonObject document) => new(
        document["authority"]!.GetValue<string>(),
        document["kind"]!.GetValue<string>(),
        document["name"]!.GetValue<string>(),
        document["revision"]!.GetValue<string>(),
        document["digest"]!.GetValue<string>());

    private static string SafeName(string value)
    {
        string safe = new(value.Select(static character => char.IsLetterOrDigit(character) || character is '.' or '-' ? character : '-').ToArray());
        return safe.Length <= 200 ? safe : safe[..200];
    }
}
