using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Development.Capabilities;

/// <summary>
/// Carries the human-session supplied capability-index snapshot used by routing.
/// Program Kit does not read the index implicitly.
/// </summary>
public sealed record CapabilityAvailabilitySnapshot(
    string SourcePath,
    Sha256Digest SourceDigest,
    ImmutableArray<CapabilityAvailability> Capabilities,
    ProgramKitIdentifier SupplierId,
    DateTimeOffset SuppliedAt);
