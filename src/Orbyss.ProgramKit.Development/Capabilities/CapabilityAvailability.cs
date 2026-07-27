using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Development.Capabilities;

/// <summary>Records the availability of one capability without interpreting implementation state.</summary>
public sealed record CapabilityAvailability(
    ProgramKitIdentifier CapabilityId,
    CapabilityAvailabilityStatus Status);
