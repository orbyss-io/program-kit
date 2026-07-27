using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>One explicitly owned side effect.</summary>
public sealed record OperationSideEffect(
    ProgramKitIdentifier OwnerId,
    string Effect,
    string CommitBoundary,
    string CompensationPolicy);
