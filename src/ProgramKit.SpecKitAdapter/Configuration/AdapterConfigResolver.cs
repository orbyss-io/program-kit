using System;
using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Configuration;

public sealed record ResolvedAdapterConfig(JsonObject Document, string LogicalPath, bool AmbientLayerPresent);

public sealed class AdapterConfigResolver
{
    public const string ProjectConfigPath = ".specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml";
    public const string LocalConfigPath = ".specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.local.yml";

    public ResolvedAdapterConfig Resolve(string workspaceRoot, string requestedLogicalPath)
    {
        if (!string.Equals(requestedLogicalPath, ProjectConfigPath, StringComparison.Ordinal))
            throw new InvalidDataException("Only the exact consumer-owned adapter project config is semantic.");
        string path = LogicalPathPolicy.Resolve(workspaceRoot, requestedLogicalPath);
        if (!File.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            throw new InvalidDataException("The exact adapter project config is missing or unsafe.");
        JsonObject config = RestrictedYaml.Parse(File.ReadAllText(path));
        AdapterSchemaValidator.Validate("adapter-config.schema.json", config);
        return new ResolvedAdapterConfig(config, requestedLogicalPath, File.Exists(LogicalPathPolicy.Resolve(workspaceRoot, LocalConfigPath)));
    }
}
