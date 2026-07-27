using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Reads and writes one strict source-generated capability ownership lock.</summary>
public interface ICapabilityInitializationLockSerializer
{
    /// <summary>Reads exact lock bytes.</summary>
    CapabilityInitializationLock Read(ReadOnlySpan<byte> content);

    /// <summary>Writes deterministic lock bytes.</summary>
    byte[] Write(CapabilityInitializationLock value);
}
