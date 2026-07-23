namespace Orbyss.ProgramKit.Workbench.Operations.Diagnostics;

/// <summary>Returns either one deterministic value or stable diagnostics.</summary>
/// <typeparam name="T">The operation value type.</typeparam>
/// <param name="Value">The value when validation succeeded.</param>
/// <param name="Validation">Stable operation diagnostics.</param>
public sealed record WorkbenchResult<T>(
    T? Value,
    ProgramKitValidationResult Validation)
{
    /// <summary>Gets whether the operation produced a valid value.</summary>
    public bool IsSuccessful => Value is not null && Validation.IsValid;

}
