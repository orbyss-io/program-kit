using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Strict source-generated capability ownership lock serializer.</summary>
public sealed class CapabilityInitializationLockSerializer :
    ICapabilityInitializationLockSerializer
{
    /// <inheritdoc />
    public CapabilityInitializationLock Read(ReadOnlySpan<byte> content) =>
        JsonSerializer.Deserialize(
            content,
            CapabilityInitializationJsonContext.Default
                .CapabilityInitializationLock)
        ?? throw new JsonException(
            "The capability ownership lock cannot be JSON null.");

    /// <inheritdoc />
    public byte[] Write(CapabilityInitializationLock value) =>
        JsonSerializer.SerializeToUtf8Bytes(
            value,
            CapabilityInitializationJsonContext.Default
                .CapabilityInitializationLock);
}
