using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>The strength of an operation's idempotency contract.</summary>
public enum OperationIdempotencyKind
{
    /// <summary>Repeated execution is not guaranteed to be equivalent.</summary>
    NonIdempotent,

    /// <summary>The same semantic request can safely be repeated.</summary>
    NaturallyIdempotent,

    /// <summary>An explicit key controls deduplication.</summary>
    IdempotencyKey,

    /// <summary>The caller must supply an optimistic concurrency condition.</summary>
    Conditional
}
