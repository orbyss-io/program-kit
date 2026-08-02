using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Translation;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public static class ValidateCommand
{
    public static JsonObject Execute(string workspaceRoot, JsonObject request)
    {
        AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspaceRoot, request, requireReviewedHandoff: true);
        if (!context.Applicability.Active)
            return AdapterResultWriter.NotApplicable(Contracts.AdapterOperation.Validate, new JsonObject { ["blocking"] = context.Applicability.BlocksWorkflow });
        TranslationResult translation = new DotNetHandoffTranslator().Translate(context.Handoff!, context.WorkspaceLock);
        return AdapterResultWriter.Success(Contracts.AdapterOperation.Validate, new JsonObject
        {
            ["handoffDigest"] = context.Handoff!.Digest,
            ["reviewDigest"] = context.Review!["digest"]!.DeepClone(),
            ["traceDependencyCount"] = context.Trace!.DependencyDigests.Count,
            ["selectionAlias"] = context.Handoff.Document["effectiveSelection"]!["alias"]!.DeepClone(),
            ["translatedArtifactCount"] = translation.Documents.Count,
        });
    }
}
