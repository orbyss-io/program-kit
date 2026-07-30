namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>One exact desired workspace file state.</summary>
public sealed record CapabilityWorkspaceMutation(
    string RelativePath,
    ReadOnlyMemory<byte>? DesiredContent);
