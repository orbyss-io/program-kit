namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>Whether invocation mechanics carry an idempotency key.</summary>
public enum OperationIdempotencyPolicy
{
    /// <summary>No idempotency key is carried.</summary>
    Unsupported,

    /// <summary>An idempotency key may be carried.</summary>
    Optional,

    /// <summary>An idempotency key must be carried.</summary>
    Required,
}
