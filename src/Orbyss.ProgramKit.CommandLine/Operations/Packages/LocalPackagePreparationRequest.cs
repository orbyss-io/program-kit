namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>Explicit local package-preparation parameters.</summary>
public sealed record LocalPackagePreparationRequest(
    string WorkspaceManifestPath,
    string OutputRoot);
