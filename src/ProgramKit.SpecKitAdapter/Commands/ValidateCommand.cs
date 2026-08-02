using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Translation;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public static class ValidateCommand
{
    public static JsonObject Execute(string workspaceRoot, JsonObject request)
    {
        AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspaceRoot, request, requireReviewedHandoff: true);
        if (!context.Applicability.Active)
            return AdapterResultWriter.Inactive(Contracts.AdapterOperation.Validate, context.Applicability);
        TranslationResult translation = new DotNetHandoffTranslator().Translate(context.Handoff!, context.WorkspaceLock);
        return AdapterResultWriter.Success(Contracts.AdapterOperation.Validate, new JsonObject
        {
            ["handoffDigest"] = context.Handoff!.Digest,
            ["reviewDigest"] = context.Review!["digest"]!.DeepClone(),
            ["traceDependencyCount"] = context.Trace!.DependencyDigests.Count,
            ["selectionAlias"] = context.Handoff.Document["effectiveSelection"]!["alias"]!.DeepClone(),
            ["selectionDiverged"] = context.Selection!.Diverged,
            ["currentSelectionAlias"] = context.Selection.CurrentAlias,
            ["requiresRehandoff"] = context.Selection.Diverged,
            ["translatedArtifactCount"] = translation.Documents.Count,
        });
    }
}
