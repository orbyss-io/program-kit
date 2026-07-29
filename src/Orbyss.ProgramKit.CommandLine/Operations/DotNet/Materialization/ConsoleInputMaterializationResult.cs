namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Finite successful Console input materialization outcome.</summary>
public sealed record ConsoleInputMaterializationResult(
    ConsoleInputMaterializationStatus Status,
    string OutputRoot,
    string ShellPath,
    string ArtifactManifestPath,
    string HostIdentity);
