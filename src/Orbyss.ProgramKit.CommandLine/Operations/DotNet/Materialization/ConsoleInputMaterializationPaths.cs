namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

internal sealed record ConsoleInputMaterializationPaths(
    string RequestPath,
    string WorkspaceRoot,
    string OutputRoot,
    string TransactionRoot,
    string BackupRoot);
