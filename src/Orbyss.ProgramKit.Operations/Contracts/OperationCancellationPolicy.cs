namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>Mechanical cancellation support exposed by an operation.</summary>
public enum OperationCancellationPolicy
{
    /// <summary>The operation exposes no cancellation signal.</summary>
    Unsupported,

    /// <summary>The operation accepts a bounded cooperative cancellation signal.</summary>
    Cooperative,
}
