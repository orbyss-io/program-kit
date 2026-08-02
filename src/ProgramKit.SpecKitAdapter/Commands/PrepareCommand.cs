using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
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
        string reviewDigest = context.Review!["digest"]!.GetValue<string>();
        JsonObject manifest = AdapterGeneratedManifestBuilder.Build(context.Handoff!, reviewDigest, translation, context.Trace!);
        if (!FilesAreExact(workspaceRoot, translation.Bytes)) new AdapterArtifactPublisher().Publish(workspaceRoot, translation, manifest);

        string preparePath = $"{translation.FeatureRoot}/requests/prepare.json";
        string explainPath = $"{translation.FeatureRoot}/requests/explain.json";
        JsonObject prepareResult = invoker.Invoke(workspaceRoot, "prepare", preparePath);
        JsonObject explainResult = invoker.Invoke(workspaceRoot, "explain", explainPath);
        Dictionary<string, JsonObject> finalDocuments = new(translation.Documents, StringComparer.Ordinal)
        {
            [$"{translation.FeatureRoot}/results/prepare.json"] = prepareResult,
            [$"{translation.FeatureRoot}/results/explain.json"] = explainResult,
        };
        TranslationResult finalTranslation = new(translation.FeatureRoot, finalDocuments, CanonicalArtifactWriter.Materialize(finalDocuments));
        JsonObject finalManifest = AdapterGeneratedManifestBuilder.Build(context.Handoff!, reviewDigest, finalTranslation, context.Trace!);
        PublicationResult publication = new AdapterArtifactPublisher().Publish(workspaceRoot, finalTranslation, finalManifest);
        return AdapterResultWriter.Success(AdapterOperation.Prepare, new JsonObject
        {
            ["handoffDigest"] = context.Handoff!.Digest,
            ["proposalDigest"] = prepareResult["payload"]?["proposal"]?["digest"]?.DeepClone(),
            ["explanationRequest"] = explainPath,
            ["generatedManifestDigest"] = finalManifest["digest"]!.DeepClone(),
            ["changed"] = publication.Changed,
        }, "adapter-files-only", prepareResult);
    }

    private static bool FilesAreExact(string workspaceRoot, IReadOnlyDictionary<string, byte[]> expected) =>
        expected.All(item =>
        {
            string path = LogicalPathPolicy.Resolve(workspaceRoot, item.Key);
            return File.Exists(path) && File.ReadAllBytes(path).SequenceEqual(item.Value);
        });
}
