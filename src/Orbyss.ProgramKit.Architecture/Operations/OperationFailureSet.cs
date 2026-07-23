using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>The complete stable failure surface of an operation.</summary>
public sealed record OperationFailureSet(
    ImmutableArray<OperationFailureDefinition> DeclaredFailures,
    string UndeclaredFailurePolicy);
