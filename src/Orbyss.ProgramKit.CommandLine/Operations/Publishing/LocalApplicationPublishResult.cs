namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Completed canonical local publish manifest and its exact path.</summary>
public sealed record LocalApplicationPublishResult(
    LocalPublishManifest Manifest,
    string ManifestPath);
