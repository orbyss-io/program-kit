using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Resolution;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Kernel.Preparation;

public sealed class PreparationService
{
    private readonly IntakePipeline intake;
    private readonly ResolutionEngine resolution;

    public PreparationService(ProviderRegistry providers)
    {
        intake = new IntakePipeline(providers);
        resolution = new ResolutionEngine(providers);
    }

    public JsonObject Prepare(string workspaceRoot, JsonObject request)
    {
        Validate(ContractSchemaResources.PreparationRequestId, request);
        ValidateExpectedLock(workspaceRoot, request["expectedLock"]!.AsObject());
        JsonObject explainRequest = new()
        {
            ["schema"] = "program-kit.factory-request/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["operation"] = "explain",
            ["rootBundle"] = request["rootBundle"]!.DeepClone(),
            ["workspaceIdentity"] = request["workspaceIdentity"]!.DeepClone(),
            ["evaluationContext"] = request["evaluationContext"]!.DeepClone(),
            ["requestedEffect"] = "none",
            ["selections"] = request["selections"]!.DeepClone(),
        };
        FactoryInput admitted = intake.AdmitAndMap(workspaceRoot, explainRequest);
        ResolvedFactoryInput resolved = resolution.Resolve(admitted);
        string liveState = ProspectiveLiveState(workspaceRoot, resolved.Explanation.CanonicalDocument);
        JsonObject ungranted = new()
        {
            ["schema"] = "program-kit.factory-request/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["operation"] = "construct",
            ["constructionMode"] = request["constructionMode"]!.DeepClone(),
            ["rootBundle"] = request["rootBundle"]!.DeepClone(),
            ["workspaceIdentity"] = request["workspaceIdentity"]!.DeepClone(),
            ["evaluationContext"] = request["evaluationContext"]!.DeepClone(),
            ["requestedEffect"] = request["desiredEffect"]!.DeepClone(),
            ["selections"] = request["selections"]!.DeepClone(),
            ["expectedState"] = new JsonObject
            {
                ["closureDigest"] = resolved.Lock.ClosureDigest,
                ["liveStateDigest"] = liveState,
            },
        };
        JsonObject proposal = new()
        {
            ["schema"] = "program-kit.preparation-proposal/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["requestBinding"] = CanonicalJson.Digest(request),
            ["closureDigest"] = resolved.Lock.ClosureDigest,
            ["liveStateDigest"] = liveState,
            ["subjects"] = new JsonArray(request["rootBundle"]!["identity"]!.DeepClone()),
            ["operation"] = "construct",
            ["constructionMode"] = request["constructionMode"]!.DeepClone(),
            ["maximumEffect"] = request["desiredEffect"]!.DeepClone(),
            ["explanation"] = resolved.Explanation.CanonicalDocument.DeepClone(),
            ["authorityRequirements"] = new JsonArray("exact-current-proposal", "exact-subjects", "exact-operation", "bounded-effect", "finite-validity", "revocation-record"),
            ["ungrantedProjection"] = ungranted,
            ["evidence"] = new JsonArray(),
        };
        proposal["digest"] = CanonicalJson.Digest(proposal);
        Validate(ContractSchemaResources.PreparationProposalId, proposal);
        return proposal;
    }

    private static void ValidateExpectedLock(string workspaceRoot, JsonObject artifact)
    {
        string logicalPath = artifact["logicalPath"]?.GetValue<string>() ?? throw new InvalidDataException("Expected lock logicalPath is required.");
        string expected = artifact["digest"]?.GetValue<string>() ?? throw new InvalidDataException("Expected lock digest is required.");
        string path = LogicalPaths.ResolveInside(workspaceRoot, logicalPath);
        if (!File.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0 || !string.Equals(Digests.Sha256(File.ReadAllBytes(path)), expected, StringComparison.Ordinal))
            throw new InvalidDataException("The expected workspace lock is missing or stale.");
    }

    private static string ProspectiveLiveState(string workspaceRoot, JsonObject explanation)
    {
        SortedSet<string> paths = new(StringComparer.Ordinal);
        CollectLogicalPaths(explanation["artifactPlan"], paths);
        string material = string.Join('\n', paths.Select(path =>
        {
            string resolved = LogicalPaths.ResolveInside(workspaceRoot, path);
            string digest = File.Exists(resolved) ? Digests.Sha256(File.ReadAllBytes(resolved)) : "missing";
            return $"{path}:{digest}";
        }));
        return Digests.Sha256(Encoding.UTF8.GetBytes(material));
    }

    private static void CollectLogicalPaths(JsonNode? node, ISet<string> paths)
    {
        if (node is JsonObject obj)
        {
            if (obj["logicalPath"]?.GetValue<string>() is { Length: > 0 } path) paths.Add(path);
            foreach ((string _, JsonNode? child) in obj) CollectLogicalPaths(child, paths);
        }
        else if (node is JsonArray array)
        {
            foreach (JsonNode? child in array) CollectLogicalPaths(child, paths);
        }
    }

    private static void Validate(string schemaId, JsonObject document)
    {
        var failures = new StructuralSchemaValidator(new SchemaRegistry()).Validate(schemaId, document);
        if (failures.Count > 0) throw new InvalidDataException(string.Join(" | ", failures));
    }
}
