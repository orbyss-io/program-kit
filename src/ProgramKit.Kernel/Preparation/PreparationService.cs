using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Publication;
using Orbyss.ProgramKit.Kernel.Resolution;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Kernel.Preparation;

public sealed class PreparationService
{
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";
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
                ["closureDigest"] = EmptyDigest,
                ["liveStateDigest"] = EmptyDigest,
            },
        };
        ResolvedFactoryInput preview = ResolveProspective(workspaceRoot, ungranted);
        string previewLiveState = ProspectiveLiveState(workspaceRoot, preview.Explanation.CanonicalDocument);
        ungranted["expectedState"] = new JsonObject
        {
            ["closureDigest"] = preview.Lock.ClosureDigest,
            ["liveStateDigest"] = previewLiveState,
        };
        ResolvedFactoryInput resolved = ResolveProspective(workspaceRoot, ungranted);
        string liveState = ProspectiveLiveState(workspaceRoot, resolved.Explanation.CanonicalDocument);
        if (!string.Equals(resolved.Lock.ClosureDigest, preview.Lock.ClosureDigest, StringComparison.Ordinal)
            || !string.Equals(liveState, previewLiveState, StringComparison.Ordinal))
            throw new InvalidDataException("Prospective construction resolution did not converge to one exact closure.");
        JsonObject proposal = new()
        {
            ["schema"] = "program-kit.preparation-proposal/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["requestBinding"] = CanonicalJson.Digest(request),
            ["closureDigest"] = resolved.Lock.ClosureDigest,
            ["liveStateDigest"] = liveState,
            ["subjects"] = new JsonArray(request["workspaceIdentity"]!.DeepClone(), request["rootBundle"]!["identity"]!.DeepClone()),
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

    public static JsonObject ProspectiveConstructRequest(JsonObject ungrantedProjection)
    {
        JsonObject request = (JsonObject)ungrantedProjection.DeepClone();
        request["authorityGrant"] = new JsonObject
        {
            ["identity"] = new JsonObject
            {
                ["authority"] = "orbyss.program-kit",
                ["kind"] = "authority-placeholder",
                ["name"] = "ungranted-proposal",
                ["revision"] = "1.0.0",
                ["digest"] = EmptyDigest,
            },
            ["mediaType"] = "application/vnd.program-kit.ungranted-placeholder+json",
            ["logicalPath"] = ".program-kit/authority/ungranted-proposal.placeholder.json",
            ["digest"] = EmptyDigest,
            ["ownership"] = "generated-owned",
        };
        return request;
    }

    private ResolvedFactoryInput ResolveProspective(string workspaceRoot, JsonObject ungrantedProjection)
    {
        FactoryInput admitted = intake.AdmitAndMap(workspaceRoot, ProspectiveConstructRequest(ungrantedProjection));
        return resolution.Resolve(admitted);
    }

    private static void ValidateExpectedLock(string workspaceRoot, JsonObject artifact)
    {
        string logicalPath = artifact["logicalPath"]?.GetValue<string>() ?? throw new InvalidDataException("Expected lock logicalPath is required.");
        string expected = artifact["digest"]?.GetValue<string>() ?? throw new InvalidDataException("Expected lock digest is required.");
        string path = LogicalPaths.ResolveInside(workspaceRoot, logicalPath);
        if (!File.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0 || !string.Equals(Digests.Sha256(File.ReadAllBytes(path)), expected, StringComparison.Ordinal))
            throw new InvalidDataException("The expected workspace lock is missing or stale.");
    }

    public static string ProspectiveLiveState(string workspaceRoot, JsonObject explanation)
    {
        SortedSet<string> paths = new(StringComparer.Ordinal);
        CollectLogicalPaths(explanation["artifactPlan"], paths);
        return LiveState.ComputeObserved(paths.Select(path =>
        {
            string resolved = LogicalPaths.ResolveInside(workspaceRoot, path);
            return (path, File.Exists(resolved) ? Digests.Sha256(File.ReadAllBytes(resolved)) : null);
        }));
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
