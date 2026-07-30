namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>Durable recovery evidence for one workspace file mutation.</summary>
internal sealed record CapabilityWorkspaceTransactionEntry(
    string RelativePath,
    bool HadOriginal,
    string? OriginalSha256,
    string? DesiredSha256,
    string? StagePath,
    string? BackupPath);
