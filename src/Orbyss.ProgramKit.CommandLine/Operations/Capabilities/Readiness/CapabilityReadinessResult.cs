using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Readiness;

/// <summary>Separated release availability, registration, and freshness state.</summary>
public sealed record CapabilityReadinessResult(
    string CapabilityId,
    string Role,
    string Availability,
    bool Registered,
    bool Fresh,
    string State,
    string Reason,
    ImmutableArray<string> Providers);
