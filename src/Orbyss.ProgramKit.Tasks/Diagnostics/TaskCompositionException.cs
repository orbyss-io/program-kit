using Orbyss.ProgramKit.Artifacts.Validation;

namespace Orbyss.ProgramKit.Tasks.Diagnostics;

/// <summary>Reports fail-closed task composition diagnostics.</summary>
public sealed class TaskCompositionException : Exception
{
    /// <summary>Initializes the exception with its complete validation result.</summary>
    public TaskCompositionException(
        string message,
        ProgramKitValidationResult validation)
        : base(message)
    {
        Validation = validation ??
            throw new ArgumentNullException(nameof(validation));
    }

    /// <summary>Gets the complete stable composition diagnostics.</summary>
    public ProgramKitValidationResult Validation { get; }
}
