using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Invocation;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;
using Orbyss.ProgramKit.SpecKitAdapter.Translation;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public sealed class PrepareCommand
{
    private readonly IPublicProgramKitInvoker invoker;

    public PrepareCommand(IPublicProgramKitInvoker? invoker = null)
    {
        this.invoker = invoker ?? new PublicProgramKitInvoker();
    }

    public JsonObject Execute(string workspaceRoot, JsonObject request)
    {
        AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspaceRoot, request, requireReviewedHandoff: true);
        if (!context.Applicability.Active)
            return AdapterResultWriter.NotApplicable(AdapterOperation.Prepare, new JsonObject { ["blocking"] = context.Applicability.BlocksWorkflow });
        TranslationResult translation = new DotNetHandoffTranslator().Translate(context.Handoff!, context.WorkspaceLock);
        string manifestPath = LogicalPathPolicy.Resolve(workspaceRoot, $"{translation.FeatureRoot}/adapter-manifest.json");
        Dictionary<string, JsonObject> documents = File.Exists(manifestPath)
            ? new Dictionary<string, JsonObject>(AdapterFeatureClosure.Load(workspaceRoot, translation.FeatureRoot), StringComparer.Ordinal)
            : new Dictionary<string, JsonObject>(StringComparer.Ordinal);
        foreach ((string logicalPath, JsonObject document) in translation.Documents) documents[logicalPath] = (JsonObject)document.DeepClone();
        PublicationResult initialPublication = AdapterFeatureClosure.Publish(workspaceRoot, context, documents);

        string preparePath = $"{translation.FeatureRoot}/requests/prepare.json";
        string explainPath = $"{translation.FeatureRoot}/requests/explain.json";
        JsonObject prepareResult = invoker.Invoke(workspaceRoot, "prepare", preparePath);
        JsonObject explainResult = invoker.Invoke(workspaceRoot, "explain", explainPath);
        documents[$"{translation.FeatureRoot}/results/prepare.json"] = prepareResult;
        documents[$"{translation.FeatureRoot}/results/explain.json"] = explainResult;
        PublicationResult publication = AdapterFeatureClosure.Publish(workspaceRoot, context, documents);
        JsonObject finalManifest = CanonicalDocument.Parse(File.ReadAllBytes(manifestPath)).AsObject();
        return AdapterResultWriter.Success(AdapterOperation.Prepare, new JsonObject
        {
            ["handoffDigest"] = context.Handoff!.Digest,
            ["proposalDigest"] = prepareResult["payload"]?["proposal"]?["digest"]?.DeepClone(),
            ["explanationRequest"] = explainPath,
            ["generatedManifestDigest"] = finalManifest["digest"]!.DeepClone(),
            ["changed"] = initialPublication.Changed || publication.Changed,
        }, "adapter-files-only", prepareResult);
    }
}
