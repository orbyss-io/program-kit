using System;
using System.IO;

namespace Orbyss.ProgramKit.SessionIntegration.Policy;

public sealed class SourceAuthoringGuard
{
    public const string MarkerFileName = ".program-kit-source.json";

    public void DemandConsumerWorkspace(string workspaceRoot)
    {
        string workspace = Path.GetFullPath(workspaceRoot);
        string marker = Path.Combine(workspace, MarkerFileName);
        if (File.Exists(marker))
            throw new InvalidOperationException("PKSES0008: Program Kit source-authoring workspaces cannot initialize, inspect, catalog, preflight, read, or remove consumer session integrations.");
    }
}
