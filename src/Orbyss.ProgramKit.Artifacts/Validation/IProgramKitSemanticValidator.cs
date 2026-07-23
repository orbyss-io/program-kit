using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Validation;

/// <summary>Validates cross-field semantics for an immutable Program Kit contract.</summary>
/// <typeparam name="T">The contract type.</typeparam>
public interface IProgramKitSemanticValidator<in T>
{
    /// <summary>Validates <paramref name="value"/> without consulting ambient state.</summary>
    ProgramKitValidationResult Validate(T value);
}
