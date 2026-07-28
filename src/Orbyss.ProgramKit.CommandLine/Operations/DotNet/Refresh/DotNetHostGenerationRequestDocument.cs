namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Refresh;

/// <summary>Committed exact inputs for repeatable generated-host refresh.</summary>
public sealed record DotNetHostGenerationRequestDocument(
    string SchemaVersion,
    string ProgramKitVersion,
    string Kind,
    string ShellPath,
    string HostIdentity,
    string ArtifactManifestPath,
    string OutputRoot,
    DotNetHostConsumerBuildRequest? ConsumerBuild);
