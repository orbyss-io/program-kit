using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Providers.DotNet.Diagnostics;

namespace Orbyss.ProgramKit.Providers.DotNet.Evaluation;

public static class ProviderArtifactValidator
{
    public static IReadOnlyList<string> ReadRuntimeLibraries(string depsPath)
    {
        if (!File.Exists(depsPath))
        {
            throw new ProviderDiagnosticException(
                DiagnosticIds.CShellsConformance,
                PrimaryDisposition.Stop,
                "The generated application dependency graph is unavailable.");
        }

        using JsonDocument parsed = JsonDocument.Parse(File.ReadAllBytes(depsPath));
        JsonObject document = JsonNode.Parse(parsed.RootElement.GetRawText()) as JsonObject
            ?? throw new ProviderDiagnosticException(DiagnosticIds.CShellsConformance, PrimaryDisposition.Stop, "The dependency graph is invalid.");
        return (document["libraries"] as JsonObject ?? throw new ProviderDiagnosticException(
                DiagnosticIds.CShellsConformance,
                PrimaryDisposition.Stop,
                "The dependency graph has no library closure."))
            .Select(static item => item.Key).ToArray();
    }

    public static void RequirePackage(string packagePath)
    {
        if (!File.Exists(packagePath))
        {
            throw new ProviderDiagnosticException(
                DiagnosticIds.PackageMismatch,
                PrimaryDisposition.Stop,
                "The exact component package expected from the admitted build is unavailable.");
        }
    }
}
