using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Payload;

/// <summary>Complete declared Program Kit-owned knowledge closure for one capability.</summary>
public sealed record CapabilityKnowledgeClosure(
    string CapabilityId,
    string Role,
    string Availability,
    string Reason,
    ImmutableArray<string> Commands,
    ImmutableArray<string> Resources,
    ImmutableArray<string> Schemas,
    ImmutableArray<string> HumanInputs,
    ImmutableArray<string> ExternalInputs);
