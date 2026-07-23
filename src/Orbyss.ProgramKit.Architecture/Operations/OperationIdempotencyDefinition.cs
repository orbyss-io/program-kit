using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>The idempotency guarantee of an operation.</summary>
public sealed record OperationIdempotencyDefinition(
    OperationIdempotencyKind Kind,
    string KeySemantics,
    string DuplicateSemantics);
