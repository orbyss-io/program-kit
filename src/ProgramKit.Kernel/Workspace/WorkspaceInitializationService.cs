using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Distribution;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Kernel.Workspace;

public sealed class WorkspaceInitializationService
{
    public (JsonObject Payload, NamespacedPublicationResult Publication) Initialize(string workspaceRoot, JsonObject request)
    {
        Validate(ContractSchemaResources.WorkspaceInitializationRequestId, request);
        JsonObject binding = DistributionDescriptor.ValidateBinding(request["distributionBinding"]!.AsObject());
        JsonObject manifest = new()
        {
            ["schema"] = "program-kit.workspace/v1",
            ["distribution"] = binding.DeepClone(),
            ["factory"] = new JsonObject { ["selections"] = new JsonArray() },
        };
        Validate(ContractSchemaResources.WorkspaceManifestId, manifest);
        JsonObject bootstrapEvidence = new()
        {
            ["schema"] = "program-kit.workspace-bootstrap-evidence/v1",
            ["requestDigest"] = CanonicalJson.Digest(request),
            ["requestedBy"] = request["requestedBy"]!.DeepClone(),
            ["effect"] = "bootstrap-absent-files",
            ["profileSelections"] = 0,
            ["authorityRecords"] = 0,
        };
        NamespacedArtifact[] artifacts =
        {
            new("program-kit.yaml", CanonicalJson.Encode(manifest)),
            new(".program-kit/bootstrap-evidence.json", CanonicalJson.Encode(bootstrapEvidence)),
        };
        NamespacedPublicationResult publication = new NamespacedArtifactSetPublisher().Publish(
            workspaceRoot,
            "bootstrap",
            CanonicalJson.Digest(request),
            artifacts);
        JsonObject payload = new()
        {
            ["manifest"] = manifest,
            ["states"] = new JsonObject
            {
                ["installed"] = true,
                ["available"] = true,
                ["selected"] = false,
                ["activated"] = false,
                ["authorized"] = false,
            },
            ["unchanged"] = publication.Changes.All(static change => change.Kind == "unchanged"),
        };
        return (payload, publication);
    }

    private static void Validate(string schema, JsonObject document)
    {
        var failures = new StructuralSchemaValidator(new SchemaRegistry()).Validate(schema, document);
        if (failures.Count > 0) throw new InvalidDataException(string.Join(" | ", failures));
    }
}
