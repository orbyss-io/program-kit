using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>The exact output contract and production boundary of an operation.</summary>
public sealed record OperationOutputDefinition(
    ImmutableArray<ArtifactReference> Contracts,
    bool AllowsNoOutput,
    bool IsStreaming,
    string CompletionSemantics);
