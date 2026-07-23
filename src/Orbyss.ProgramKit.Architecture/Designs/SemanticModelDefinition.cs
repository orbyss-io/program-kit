using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>A named semantic model that is not itself a public exchange contract.</summary>
public sealed record SemanticModelDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerDomainId,
    string Meaning,
    ImmutableArray<ProgramKitIdentifier> TermContractIds,
    string Invariants);
