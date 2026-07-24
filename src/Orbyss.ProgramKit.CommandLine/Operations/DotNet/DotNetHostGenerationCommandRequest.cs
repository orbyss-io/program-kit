using Orbyss.ProgramKit.DotNet.Shells;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet;

/// <summary>Explicit manifest-bound host generation parameters shared by CLI adapters.</summary>
public sealed record DotNetHostGenerationCommandRequest(
    string ShellPath,
    string HostIdentity,
    string ArtifactManifestPath,
    string OutputRoot,
    DotNetHostKind? ExpectedKind);
