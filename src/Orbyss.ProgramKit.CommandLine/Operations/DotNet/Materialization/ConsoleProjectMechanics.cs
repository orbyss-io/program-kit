namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Exact mechanics derived from one explicitly selected project.</summary>
internal sealed record ConsoleProjectMechanics(
    string AssemblyName,
    string TargetFramework);
