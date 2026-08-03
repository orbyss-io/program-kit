using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Distribution;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Kernel.Workspace;

public sealed class WorkspaceRestoreService
{
    private readonly ProviderRegistry providers;

    public WorkspaceRestoreService(ProviderRegistry providers)
    {
        this.providers = providers;
    }

    public (JsonObject Payload, NamespacedPublicationResult Publication) Restore(string workspaceRoot, JsonObject request)
    {
        Validate(ContractSchemaResources.WorkspaceRestoreRequestId, request);
        JsonObject requestBinding = DistributionDescriptor.ValidateBinding(request["distributionBinding"]!.AsObject());
        string manifestPath = LogicalPaths.ResolveInside(workspaceRoot, request["manifest"]!.GetValue<string>());
        if (!File.Exists(manifestPath) || (File.GetAttributes(manifestPath) & FileAttributes.ReparsePoint) != 0)
            throw new InvalidDataException("The workspace manifest must be a regular file inside the workspace.");
        JsonObject manifest = new RestrictedYamlParser().Parse(File.ReadAllBytes(manifestPath)).AsObject();
        BoundWorkspaceManifest bound = new WorkspaceManifestBinder(providers).Bind(manifest);
        if (!CanonicalJson.Encode(bound.Distribution).SequenceEqual(CanonicalJson.Encode(requestBinding)))
            throw new InvalidDataException("The request and manifest distribution bindings differ.");

        string mode = request["mode"]!.GetValue<string>();
        if (mode == "factory" && bound.Selections.Count == 0)
            throw new KeyNotFoundException("Factory restore requires at least one exact profile selection.");

        TypedContractBinder contractBinder = new();
        GovernedIdentity workspace = contractBinder.BindIdentity(request["workspaceIdentity"]!.AsObject());
        JsonArray resolved = new(ResolveItems(bound).Select(ContractJson.Identity).ToArray());
        JsonObject lockDocument = new()
        {
            ["schema"] = "program-kit.workspace-lock/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["workspaceIdentity"] = ContractJson.Identity(workspace),
            ["distributionBinding"] = requestBinding,
            ["manifestDigest"] = CanonicalJson.Digest(manifest),
            ["mode"] = mode,
            ["resolvedItems"] = resolved,
            ["selections"] = new JsonArray(bound.Selections.Select(static selection => selection.Document.DeepClone()).ToArray()),
            ["unresolvedItems"] = new JsonArray(),
            ["closureDigest"] = Digests.Sha256(System.Text.Encoding.UTF8.GetBytes(string.Join('\n', ResolveItems(bound).Select(static item => $"{item.StableKey}:{item.Digest}")))),
            ["evidence"] = new JsonArray(bound.Selections.SelectMany(static selection => selection.Provider.Manifest.ConformanceEvidence).Select(static evidence => JsonValue.Create(evidence.Artifact.Digest)).ToArray()),
        };
        if (bound.DefaultSelection is not null) lockDocument["defaultSelection"] = bound.DefaultSelection;
        lockDocument["digest"] = CanonicalJson.Digest(lockDocument);
        Validate(ContractSchemaResources.WorkspaceLockId, lockDocument);

        string lockLogicalPath = request["lockPath"]!.GetValue<string>();
        string lockPath = LogicalPaths.ResolveInside(workspaceRoot, lockLogicalPath);
        string? expected = null;
        if (File.Exists(lockPath))
        {
            JsonObject previous = CanonicalJson.Parse(File.ReadAllBytes(lockPath)).AsObject();
            Validate(ContractSchemaResources.WorkspaceLockId, previous);
            expected = Digests.Sha256(File.ReadAllBytes(lockPath));
        }

        NamespacedPublicationResult publication = new NamespacedArtifactSetPublisher().Publish(
            workspaceRoot,
            "workspace",
            CanonicalJson.Digest(request),
            new[] { new NamespacedArtifact(lockLogicalPath, CanonicalJson.Encode(lockDocument), expected) });
        JsonObject payload = new()
        {
            ["lock"] = lockDocument,
            ["states"] = new JsonObject
            {
                ["installed"] = true,
                ["available"] = true,
                ["selected"] = bound.Selections.Count > 0,
                ["activated"] = false,
                ["authorized"] = false,
            },
        };
        return (payload, publication);
    }

    private static IReadOnlyList<GovernedIdentity> ResolveItems(BoundWorkspaceManifest manifest)
    {
        List<GovernedIdentity> values = new();
        TypedContractBinder binder = new();
        values.Add(binder.BindIdentity(manifest.Distribution["distribution"]!.AsObject()));
        foreach (BoundWorkspaceSelection selection in manifest.Selections)
        {
            values.Add(selection.Provider.Manifest.Identity);
            values.Add(selection.Profile);
        }

        return values.GroupBy(static item => item.StableKey, StringComparer.Ordinal).Select(static group => group.First()).OrderBy(static item => item.StableKey, StringComparer.Ordinal).ToArray();
    }

    private static void Validate(string schema, JsonObject document)
    {
        var failures = new StructuralSchemaValidator(new SchemaRegistry()).Validate(schema, document);
        if (failures.Count > 0) throw new InvalidDataException(string.Join(" | ", failures));
    }
}
