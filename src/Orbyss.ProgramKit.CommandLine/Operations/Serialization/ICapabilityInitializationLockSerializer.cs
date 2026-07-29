using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Reads and writes one strict source-generated capability ownership lock.</summary>
public interface ICapabilityInitializationLockSerializer
{
    /// <summary>Reads the required top-level lock-format version.</summary>
    string ReadVersion(ReadOnlySpan<byte> content);

    /// <summary>Reads exact lock bytes.</summary>
    CapabilityInitializationLock Read(ReadOnlySpan<byte> content);

    /// <summary>Reads exact legacy bytes for explicit verified migration only.</summary>
    LegacyCapabilityInitializationLock ReadLegacy(ReadOnlySpan<byte> content);

    /// <summary>Writes deterministic lock bytes.</summary>
    byte[] Write(CapabilityInitializationLock value);
}
