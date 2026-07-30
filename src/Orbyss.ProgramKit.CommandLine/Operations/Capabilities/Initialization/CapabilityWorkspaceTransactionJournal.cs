namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>One prepared capability workspace transaction.</summary>
internal sealed record CapabilityWorkspaceTransactionJournal(
    string TransactionVersion,
    CapabilityWorkspaceTransactionEntry[] Entries);
