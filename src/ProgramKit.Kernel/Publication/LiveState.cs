using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Publication;

public static class LiveState
{
    public static string Compute(string workspaceRoot, IEnumerable<ArtifactManifestEntry> artifacts)
    {
        List<string> observations = new();
        foreach (ArtifactManifestEntry artifact in artifacts.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal))
        {
            string path = LogicalPaths.ResolveInside(workspaceRoot, artifact.LogicalPath);
            if (File.Exists(path))
            {
                observations.Add($"{artifact.LogicalPath}:{Digests.Sha256(File.ReadAllBytes(path))}");
            }
        }

        return Digests.Sha256(System.Text.Encoding.UTF8.GetBytes(string.Join('\n', observations)));
    }

    public static string ComputeObserved(IEnumerable<(string LogicalPath, string? Digest)> observations) =>
        Digests.Sha256(System.Text.Encoding.UTF8.GetBytes(string.Join('\n', observations
            .Where(static item => item.Digest is not null)
            .OrderBy(static item => item.LogicalPath, StringComparer.Ordinal)
            .Select(static item => $"{item.LogicalPath}:{item.Digest}"))));
}
