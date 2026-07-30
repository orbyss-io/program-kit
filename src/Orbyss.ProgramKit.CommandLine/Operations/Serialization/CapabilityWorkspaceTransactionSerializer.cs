using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Strict source-generated transaction-journal serialization.</summary>
internal static class CapabilityWorkspaceTransactionSerializer
{
    internal static byte[] Write(
        CapabilityWorkspaceTransactionJournal value) =>
        JsonSerializer.SerializeToUtf8Bytes(
            value,
            CapabilityWorkspaceTransactionJsonContext.Default
                .CapabilityWorkspaceTransactionJournal);

    internal static CapabilityWorkspaceTransactionJournal Read(
        ReadOnlySpan<byte> content) =>
        JsonSerializer.Deserialize(
            content,
            CapabilityWorkspaceTransactionJsonContext.Default
                .CapabilityWorkspaceTransactionJournal)
        ?? throw new JsonException(
            "The capability transaction journal cannot be JSON null.");
}
