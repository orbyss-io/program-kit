namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Creates one complete Console materialization request.</summary>
public interface IConsoleRequestScaffolder
{
    /// <summary>
    /// Creates one new request from exact consumer-owned semantic selections
    /// and one exact project boundary.
    /// </summary>
    ValueTask<string> ScaffoldAsync(
        string sketchPath,
        string workspaceRoot,
        string consumerProjectPath,
        string outputPath,
        CancellationToken cancellationToken);
}
