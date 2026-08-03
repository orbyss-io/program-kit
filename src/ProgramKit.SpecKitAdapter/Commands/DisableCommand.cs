using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public static class DisableCommand
{
    public static JsonObject Execute(string workspaceRoot, JsonObject request)
    {
        string featureKey = request["feature"]?["key"]?.GetValue<string>() ?? throw new InvalidDataException("A feature key is required.");
        string configPath = request["config"]?["logicalPath"]?.GetValue<string>() ?? throw new InvalidDataException("A config logicalPath is required.");
        ResolvedAdapterConfig config = new AdapterConfigResolver().Resolve(workspaceRoot, configPath);
        JsonObject? currentFeature = config.Document["activation"]!["features"]?[featureKey] as JsonObject;
        JsonObject proposedFeature = currentFeature is null ? new JsonObject() : (JsonObject)currentFeature.DeepClone();
        proposedFeature["applicability"] = "disabled";

        return AdapterResultWriter.Success(AdapterOperation.Disable, new JsonObject
        {
            ["applied"] = false,
            ["configLogicalPath"] = config.LogicalPath,
            ["featureKey"] = featureKey,
            ["proposedFeature"] = proposedFeature,
            ["preservesHistoricalArtifacts"] = true,
            ["cleanupPerformed"] = false,
            ["requiresRevalidationBeforeReenable"] = true,
        });
    }
}
