namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Preflighted contained paths for one scaffold transaction.</summary>
internal sealed record ConsoleRequestScaffoldPaths(
    string WorkspaceRoot,
    string SketchPath,
    string ProjectPath,
    string ProjectRelativePath,
    string OutputPath,
    string StagePath);
