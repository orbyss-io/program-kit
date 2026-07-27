using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>The resources acquired, released, or transferred by an operation.</summary>
public sealed record OperationResourceOwnershipDefinition(
    ImmutableArray<OperationResourceDefinition> Resources,
    string DisposalSemantics);
