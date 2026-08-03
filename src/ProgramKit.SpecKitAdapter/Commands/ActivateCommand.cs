using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public static class ActivateCommand
{
    public static JsonObject Execute(string workspaceRoot, JsonObject request)
    {
        string featureKey = request["feature"]?["key"]?.GetValue<string>() ?? throw new InvalidDataException("A feature key is required.");
        string configPath = request["config"]?["logicalPath"]?.GetValue<string>() ?? throw new InvalidDataException("A config logicalPath is required.");
        ResolvedAdapterConfig config = new AdapterConfigResolver().Resolve(workspaceRoot, configPath);
        string lockLogical = config.Document["programKit"]!["lock"]!.GetValue<string>();
        string lockPath = LogicalPathPolicy.Resolve(workspaceRoot, lockLogical);
        if (!File.Exists(lockPath)) throw new InvalidDataException("Activation requires the current Program Kit workspace lock.");
        JsonObject workspaceLock = CanonicalDocument.Parse(File.ReadAllBytes(lockPath)).AsObject();
        EffectiveSelection selection = SelectionResolver.Resolve(config.Document, featureKey, workspaceLock);
        JsonObject? currentFeature = config.Document["activation"]!["features"]?[featureKey] as JsonObject;
        string currentMode = currentFeature?["mode"]?.GetValue<string>()
            ?? config.Document["activation"]!["defaultMode"]!.GetValue<string>();
        string proposedMode = currentMode == "off" ? "assist" : currentMode;
        JsonObject proposedFeature = new()
        {
            ["mode"] = proposedMode,
            ["applicability"] = "applicable",
        };
        if (selection.Source == "feature-override") proposedFeature["selection"] = selection.Alias;
        if (currentFeature?["decisionSource"] is JsonObject decisionSource)
            proposedFeature["decisionSource"] = decisionSource.DeepClone();

        return AdapterResultWriter.Success(AdapterOperation.Activate, new JsonObject
        {
            ["applied"] = false,
            ["configLogicalPath"] = config.LogicalPath,
            ["featureKey"] = featureKey,
            ["proposedFeature"] = proposedFeature,
            ["effectiveSelection"] = new JsonObject
            {
                ["alias"] = selection.Alias,
                ["source"] = selection.Source,
                ["selection"] = selection.Selection.DeepClone(),
            },
            ["requiresConsumerDecisionSource"] = proposedFeature["decisionSource"] is null,
            ["requiresHandoffReview"] = true,
        });
    }
}
