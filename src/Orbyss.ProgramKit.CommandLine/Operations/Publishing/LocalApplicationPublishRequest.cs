namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Exact selected inputs for one local application publish.</summary>
public sealed record LocalApplicationPublishRequest(
    string ShellPath,
    string HostIdentity,
    string ArtifactManifestPath,
    string PackageManifestPath,
    string OutputRoot);
