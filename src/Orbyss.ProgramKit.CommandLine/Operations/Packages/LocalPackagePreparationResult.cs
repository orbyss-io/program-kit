namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>Completed package-root manifest and its exact output path.</summary>
public sealed record LocalPackagePreparationResult(
    LocalPackageRootManifest Manifest,
    string ManifestPath);
