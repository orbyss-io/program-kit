using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>The side effects an operation may perform.</summary>
public sealed record OperationSideEffectDefinition(
    bool IsSideEffectFree,
    ImmutableArray<OperationSideEffect> Effects);
