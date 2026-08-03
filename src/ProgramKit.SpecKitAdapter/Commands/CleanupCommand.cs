using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public static class CleanupCommand
{
    public static JsonObject Execute(string workspaceRoot, JsonObject request)
    {
        string featureKey = request["feature"]?["key"]?.GetValue<string>() ?? throw new InvalidDataException("A feature key is required.");
        string outputRoot = request["outputRoot"]?.GetValue<string>() ?? throw new InvalidDataException("An outputRoot is required.");
        AdapterCleanupResult cleanup = new AdapterCleanupService().Cleanup(workspaceRoot, featureKey, outputRoot);
        return AdapterResultWriter.Success(AdapterOperation.Cleanup, new JsonObject
        {
            ["changed"] = cleanup.Changed,
            ["removed"] = new JsonArray(cleanup.Removed.Select(static path => JsonValue.Create(path)).ToArray()),
            ["preserved"] = new JsonArray(cleanup.Preserved.Select(static path => JsonValue.Create(path)).ToArray()),
        }, cleanup.Changed ? "adapter-files-only" : "none");
    }
}
