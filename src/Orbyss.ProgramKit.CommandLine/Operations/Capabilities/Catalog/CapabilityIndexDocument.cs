using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Catalog;

/// <summary>Strict parsed projection of the canonical capability index table.</summary>
public sealed record CapabilityIndexDocument(
    ImmutableArray<CapabilityIndexEntry> Entries);
