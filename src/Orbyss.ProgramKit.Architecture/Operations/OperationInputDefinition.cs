using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>The exact input contract and validation boundary of an operation.</summary>
public sealed record OperationInputDefinition(
    ImmutableArray<ArtifactReference> Contracts,
    bool AllowsNoInput,
    string ValidationSemantics);
