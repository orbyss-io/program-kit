using Orbyss.ProgramKit.Artifacts.Validation;

namespace Orbyss.ProgramKit.Modularity.Diagnostics;

/// <summary>
/// Reports deterministic registry or policy validation failure without
/// inventing a domain-specific outcome.
/// </summary>
public sealed class ModularityValidationException : InvalidOperationException
{
    /// <summary>Initializes the exception from a failed validation result.</summary>
    /// <param name="message">The culture-invariant exception message.</param>
    /// <param name="validation">The failed validation result.</param>
    public ModularityValidationException(
        string message,
        ProgramKitValidationResult validation)
        : base(message)
    {
        ArgumentNullException.ThrowIfNull(validation);
        Validation = validation;
    }

    /// <summary>Gets the complete deterministic validation result.</summary>
    public ProgramKitValidationResult Validation { get; }
}
