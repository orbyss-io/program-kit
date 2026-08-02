using System;
using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public static class DoctorCommand
{
    public static JsonObject Execute(string workspaceRoot, JsonObject request)
    {
        JsonObject configReference = request["config"]?.AsObject() ?? throw new InvalidDataException("Doctor requires an exact config artifact reference.");
        string configPath = configReference["logicalPath"]?.GetValue<string>() ?? throw new InvalidDataException("Doctor config logicalPath is required.");
        ResolvedAdapterConfig config = new AdapterConfigResolver().Resolve(workspaceRoot, configPath);
        string extensionManifestPath = LogicalPathPolicy.Resolve(workspaceRoot, ".specify/extensions/orbyss-program-kit-adapter/extension.yml");
        string toolManifestPath = LogicalPathPolicy.Resolve(workspaceRoot, ".config/dotnet-tools.json");
        string workspaceManifestPath = LogicalPathPolicy.Resolve(workspaceRoot, config.Document["programKit"]!["manifest"]!.GetValue<string>());
        string lockPath = LogicalPathPolicy.Resolve(workspaceRoot, config.Document["programKit"]!["lock"]!.GetValue<string>());
        RequireText(extensionManifestPath, "version: 0.1.0", "Spec Kit extension 0.1.0 is unavailable.");
        RequireText(extensionManifestPath, "speckit_version: \"==0.15.1\"", "Spec Kit compatibility is not exact.");
        RequireText(toolManifestPath, "Orbyss.ProgramKit.Cli", "The local Program Kit tool manifest is unavailable.");
        RequireText(toolManifestPath, "1.0.0-alpha.2", "The local Program Kit version is incompatible.");
        JsonObject workspaceManifest = RestrictedYaml.Parse(File.ReadAllText(workspaceManifestPath));
        if (workspaceManifest["schema"]?.GetValue<string>() != "program-kit.workspace/v1")
            throw new InvalidDataException("The Program Kit workspace manifest is incompatible.");
        JsonObject lockDocument = CanonicalDocument.Parse(File.ReadAllBytes(lockPath)).AsObject();
        if (lockDocument["schema"]?.GetValue<string>() != "program-kit.workspace-lock/v1"
            || lockDocument["mode"]?.GetValue<string>() != "base")
            throw new InvalidDataException("Base doctor requires a current base workspace lock.");
        int selections = lockDocument["selections"]?.AsArray().Count ?? throw new InvalidDataException("The workspace lock has no selection collection.");
        return AdapterResultWriter.Success(AdapterOperation.Doctor, new JsonObject
        {
            ["scope"] = "base",
            ["states"] = new JsonObject
            {
                ["installed"] = true,
                ["available"] = true,
                ["selected"] = selections > 0,
                ["activated"] = false,
                ["authorized"] = false,
            },
            ["selectionCount"] = selections,
            ["ambientOverridesIgnored"] = config.AmbientLayerPresent,
        });
    }

    private static void RequireText(string path, string expected, string message)
    {
        if (!File.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0 || !File.ReadAllText(path).Contains(expected, StringComparison.Ordinal))
            throw new InvalidDataException(message);
    }
}
