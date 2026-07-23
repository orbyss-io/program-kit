using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>An owned boundary, its guarantees, and its explicit exclusions.</summary>
public sealed record BoundaryDefinition(
    ProgramKitIdentifier OwnerId,
    string Policy,
    ImmutableArray<string> Guarantees,
    ImmutableArray<string> Exclusions);
