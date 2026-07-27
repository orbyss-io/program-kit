namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>Mechanical progress support exposed by an operation.</summary>
public enum OperationProgressPolicy
{
    /// <summary>The operation exposes no progress documents.</summary>
    Unsupported,

    /// <summary>Progress is bounded, redacted, droppable, and non-authoritative.</summary>
    BoundedNonAuthoritative,
}
