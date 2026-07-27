namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>
/// The only reusable result classifications; all result meaning remains in the
/// consumer-owned typed payload.
/// </summary>
public enum OperationResultDisposition
{
    /// <summary>The exact invocation attempt has reached a final domain-owned outcome.</summary>
    Terminal,

    /// <summary>A typed payload identifies an exact related operation for new input.</summary>
    AdditionalInputRequired,
}
